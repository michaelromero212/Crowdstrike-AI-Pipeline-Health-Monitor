"""
Mock ML/LLM inference client for CrowdStrike AI Pipeline Health Monitor.
Simulates model inference with configurable latency and failure injection.
"""

import random
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import numpy as np


class FailureMode:
    """Configuration for injected failures."""
    def __init__(self):
        self.latency_multiplier: float = 1.0
        self.error_rate: float = 0.0
        self.drift_enabled: bool = False
        self.correctness_flip_rate: float = 0.0
    
    def reset(self):
        """Reset all failure modes to normal."""
        self.latency_multiplier = 1.0
        self.error_rate = 0.0
        self.drift_enabled = False
        self.correctness_flip_rate = 0.0


# Global failure mode instance for demo injection
failure_mode = FailureMode()


class ModelClient:
    """
    Mock ML inference client that simulates model behavior.
    Supports failure injection for demo purposes.
    """
    
    def __init__(self, endpoint: str = "mock://local"):
        self.endpoint = endpoint
        self.base_latency_ms = 50  # Base inference latency
        self.model_version = "v1.2.3"
        self.cache: Dict[str, Any] = {}
        
        # Baseline distribution for drift detection
        self.baseline_distribution = np.random.normal(0.5, 0.1, 1000)
        
        # Known samples for correctness checks
        self.known_samples = {
            "test_sample_1": {"label": "malware", "confidence": 0.95},
            "test_sample_2": {"label": "benign", "confidence": 0.88},
            "test_sample_3": {"label": "suspicious", "confidence": 0.72},
        }
    
    async def infer(self, input_data: str) -> Dict[str, Any]:
        """
        Perform mock inference on input data.
        
        Args:
            input_data: Input string or sample identifier
            
        Returns:
            Dictionary with inference results
        """
        start_time = datetime.utcnow()
        
        # Simulate inference latency with possible injection
        latency_ms = self.base_latency_ms * failure_mode.latency_multiplier
        latency_ms += random.gauss(0, 10)  # Add some noise
        latency_ms = max(10, latency_ms)  # Minimum 10ms
        
        await asyncio.sleep(latency_ms / 1000.0)
        
        # Check for error injection
        if random.random() < failure_mode.error_rate:
            raise RuntimeError("Simulated inference error")
        
        # Generate result
        if input_data in self.known_samples:
            result = self.known_samples[input_data].copy()
            # Apply correctness flip for testing
            if random.random() < failure_mode.correctness_flip_rate:
                result["label"] = "corrupted"
        else:
            result = self._generate_prediction(input_data)
        
        end_time = datetime.utcnow()
        elapsed_ms = (end_time - start_time).total_seconds() * 1000
        
        return {
            "input": input_data,
            "output": result,
            "latency_ms": elapsed_ms,
            "model_version": self.model_version,
            "timestamp": end_time.isoformat()
        }
    
    def _generate_prediction(self, input_data: str) -> Dict[str, Any]:
        """Generate a mock prediction based on input."""
        # Deterministic hash-based prediction for consistency
        hash_val = hash(input_data) % 100
        
        if hash_val < 20:
            label = "malware"
        elif hash_val < 40:
            label = "suspicious"
        else:
            label = "benign"
        
        confidence = 0.7 + (hash_val % 30) / 100.0
        
        return {
            "label": label,
            "confidence": round(confidence, 3)
        }
    
    def get_prediction_distribution(self, n_samples: int = 100) -> np.ndarray:
        """
        Get distribution of prediction confidences for drift detection.
        
        Args:
            n_samples: Number of samples to generate
            
        Returns:
            Array of confidence scores
        """
        if failure_mode.drift_enabled:
            # Return drifted distribution (shifted mean)
            return np.random.normal(0.7, 0.15, n_samples)
        else:
            # Return distribution similar to baseline
            return np.random.normal(0.5, 0.1, n_samples)
    
    def get_baseline_distribution(self) -> np.ndarray:
        """Get the baseline distribution for comparison."""
        return self.baseline_distribution
    
    def clear_cache(self):
        """Clear the inference cache."""
        self.cache.clear()
        return {"status": "cache_cleared", "timestamp": datetime.utcnow().isoformat()}
    
    def get_health(self) -> Dict[str, Any]:
        """Get model client health status."""
        return {
            "status": "healthy" if failure_mode.error_rate < 0.5 else "degraded",
            "endpoint": self.endpoint,
            "model_version": self.model_version,
            "cache_size": len(self.cache),
            "failure_mode": {
                "latency_multiplier": failure_mode.latency_multiplier,
                "error_rate": failure_mode.error_rate,
                "drift_enabled": failure_mode.drift_enabled,
                "correctness_flip_rate": failure_mode.correctness_flip_rate
            }
        }


# Global model client instance
model_client = ModelClient()


def inject_failure(failure_type: str, severity: str = "medium"):
    """
    Inject a failure for demo purposes.
    
    Args:
        failure_type: One of 'latency', 'error', 'drift', 'correctness'
        severity: One of 'low', 'medium', 'high'
    """
    severity_multipliers = {
        "low": 1.5,
        "medium": 3.0,
        "high": 10.0
    }
    multiplier = severity_multipliers.get(severity, 3.0)
    
    if failure_type == "latency":
        failure_mode.latency_multiplier = multiplier
    elif failure_type == "error":
        failure_mode.error_rate = 0.3 * multiplier / 3.0
    elif failure_type == "drift":
        failure_mode.drift_enabled = True
    elif failure_type == "correctness":
        failure_mode.correctness_flip_rate = 0.3 * multiplier / 3.0
    
    return {
        "injected": failure_type,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat()
    }


def clear_failures():
    """Clear all injected failures."""
    failure_mode.reset()
    return {"status": "cleared", "timestamp": datetime.utcnow().isoformat()}
