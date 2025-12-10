"""
Health check implementations for CrowdStrike AI Pipeline Health Monitor.
Supports latency, correctness, drift, and resource checks.
"""

import asyncio
import json
from datetime import datetime
from time import perf_counter
from typing import Dict, Any, Optional
from scipy import stats
import numpy as np

from app.services.model_client import model_client


class HealthCheckResult:
    """Result of a health check execution."""
    
    def __init__(self, name: str, check_type: str, passed: bool, 
                 result_value: float = None, details: Dict[str, Any] = None,
                 error: str = None, latency_ms: float = None):
        self.name = name
        self.check_type = check_type
        self.passed = passed
        self.result_value = result_value
        self.details = details or {}
        self.error = error
        self.latency_ms = latency_ms
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "check_type": self.check_type,
            "passed": self.passed,
            "result_value": self.result_value,
            "details": self.details,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat()
        }


async def latency_check(sample_input: str = "test_sample_1", 
                        threshold_ms: float = 200.0) -> HealthCheckResult:
    """
    Check model inference latency against threshold.
    
    Args:
        sample_input: Input to send to model
        threshold_ms: Maximum acceptable latency in milliseconds
        
    Returns:
        HealthCheckResult with latency measurements
    """
    start = perf_counter()
    
    try:
        result = await model_client.infer(sample_input)
        elapsed_ms = (perf_counter() - start) * 1000
        passed = elapsed_ms <= threshold_ms
        
        return HealthCheckResult(
            name="Latency Check",
            check_type="latency",
            passed=passed,
            result_value=elapsed_ms,
            details={
                "threshold_ms": threshold_ms,
                "measured_ms": elapsed_ms,
                "model_reported_ms": result.get("latency_ms"),
                "model_version": result.get("model_version")
            },
            latency_ms=elapsed_ms
        )
    except Exception as e:
        elapsed_ms = (perf_counter() - start) * 1000
        return HealthCheckResult(
            name="Latency Check",
            check_type="latency",
            passed=False,
            error=str(e),
            latency_ms=elapsed_ms
        )


async def correctness_check(test_samples: list = None,
                           accuracy_threshold: float = 0.95) -> HealthCheckResult:
    """
    Validate model outputs against known expected results.
    
    Args:
        test_samples: List of sample identifiers to test
        accuracy_threshold: Minimum required accuracy (0-1)
        
    Returns:
        HealthCheckResult with accuracy measurements
    """
    if test_samples is None:
        test_samples = ["test_sample_1", "test_sample_2", "test_sample_3"]
    
    expected_outputs = {
        "test_sample_1": "malware",
        "test_sample_2": "benign", 
        "test_sample_3": "suspicious"
    }
    
    start = perf_counter()
    correct = 0
    total = len(test_samples)
    results = []
    
    try:
        for sample_id in test_samples:
            result = await model_client.infer(sample_id)
            actual_label = result["output"]["label"]
            expected_label = expected_outputs.get(sample_id)
            is_correct = actual_label == expected_label
            
            if is_correct:
                correct += 1
            
            results.append({
                "sample": sample_id,
                "expected": expected_label,
                "actual": actual_label,
                "correct": is_correct
            })
        
        elapsed_ms = (perf_counter() - start) * 1000
        accuracy = correct / total if total > 0 else 0
        passed = accuracy >= accuracy_threshold
        
        return HealthCheckResult(
            name="Correctness Check",
            check_type="correctness",
            passed=passed,
            result_value=accuracy,
            details={
                "accuracy": accuracy,
                "accuracy_threshold": accuracy_threshold,
                "correct": correct,
                "total": total,
                "sample_results": results
            },
            latency_ms=elapsed_ms
        )
    except Exception as e:
        elapsed_ms = (perf_counter() - start) * 1000
        return HealthCheckResult(
            name="Correctness Check",
            check_type="correctness",
            passed=False,
            error=str(e),
            latency_ms=elapsed_ms
        )


async def drift_check(n_samples: int = 100,
                      ks_threshold: float = 0.1) -> HealthCheckResult:
    """
    Detect distribution drift using Kolmogorov-Smirnov test.
    
    Args:
        n_samples: Number of samples to compare
        ks_threshold: Maximum acceptable KS statistic
        
    Returns:
        HealthCheckResult with drift analysis
    """
    start = perf_counter()
    
    try:
        # Get current prediction distribution
        current_dist = model_client.get_prediction_distribution(n_samples)
        baseline_dist = model_client.get_baseline_distribution()
        
        # Perform KS test
        ks_statistic, p_value = stats.ks_2samp(current_dist, baseline_dist)
        
        elapsed_ms = (perf_counter() - start) * 1000
        passed = ks_statistic <= ks_threshold
        
        # Calculate additional statistics
        current_mean = float(np.mean(current_dist))
        current_std = float(np.std(current_dist))
        baseline_mean = float(np.mean(baseline_dist))
        baseline_std = float(np.std(baseline_dist))
        
        return HealthCheckResult(
            name="Drift Check",
            check_type="drift",
            passed=passed,
            result_value=ks_statistic,
            details={
                "ks_statistic": ks_statistic,
                "ks_threshold": ks_threshold,
                "p_value": p_value,
                "drift_detected": not passed,
                "current_distribution": {
                    "mean": current_mean,
                    "std": current_std
                },
                "baseline_distribution": {
                    "mean": baseline_mean,
                    "std": baseline_std
                },
                "mean_shift": current_mean - baseline_mean
            },
            latency_ms=elapsed_ms
        )
    except Exception as e:
        elapsed_ms = (perf_counter() - start) * 1000
        return HealthCheckResult(
            name="Drift Check",
            check_type="drift",
            passed=False,
            error=str(e),
            latency_ms=elapsed_ms
        )


async def resource_check(cpu_threshold: float = 80.0,
                         memory_threshold: float = 80.0) -> HealthCheckResult:
    """
    Check simulated resource utilization.
    
    Args:
        cpu_threshold: Maximum acceptable CPU utilization %
        memory_threshold: Maximum acceptable memory utilization %
        
    Returns:
        HealthCheckResult with resource metrics
    """
    start = perf_counter()
    
    try:
        # Simulate resource metrics (in production, would pull from actual metrics)
        import random
        
        # Base utilization with some randomness
        base_cpu = 45 + random.gauss(0, 10)
        base_memory = 55 + random.gauss(0, 8)
        
        # Apply stress if failure mode is active (simulate via model client health)
        health = model_client.get_health()
        if health["failure_mode"]["latency_multiplier"] > 2:
            # High latency often correlates with high resource usage
            base_cpu *= 1.5
            base_memory *= 1.3
        
        cpu_util = min(100, max(0, base_cpu))
        memory_util = min(100, max(0, base_memory))
        
        elapsed_ms = (perf_counter() - start) * 1000
        cpu_ok = cpu_util <= cpu_threshold
        memory_ok = memory_util <= memory_threshold
        passed = cpu_ok and memory_ok
        
        return HealthCheckResult(
            name="Resource Check",
            check_type="resource",
            passed=passed,
            result_value=max(cpu_util, memory_util),  # Report worst metric
            details={
                "cpu_utilization": round(cpu_util, 2),
                "cpu_threshold": cpu_threshold,
                "cpu_ok": cpu_ok,
                "memory_utilization": round(memory_util, 2),
                "memory_threshold": memory_threshold,
                "memory_ok": memory_ok,
                "disk_iops": round(random.uniform(100, 500), 2),
                "network_in_mbps": round(random.uniform(10, 100), 2),
                "network_out_mbps": round(random.uniform(5, 50), 2)
            },
            latency_ms=elapsed_ms
        )
    except Exception as e:
        elapsed_ms = (perf_counter() - start) * 1000
        return HealthCheckResult(
            name="Resource Check",
            check_type="resource",
            passed=False,
            error=str(e),
            latency_ms=elapsed_ms
        )


async def run_check(check_type: str, threshold: float = None, **kwargs) -> HealthCheckResult:
    """
    Run a health check by type.
    
    Args:
        check_type: One of 'latency', 'correctness', 'drift', 'resource'
        threshold: Optional threshold override
        **kwargs: Additional arguments for specific check types
        
    Returns:
        HealthCheckResult
    """
    if check_type == "latency":
        return await latency_check(
            threshold_ms=threshold if threshold else 200.0,
            **kwargs
        )
    elif check_type == "correctness":
        return await correctness_check(
            accuracy_threshold=threshold if threshold else 0.95,
            **kwargs
        )
    elif check_type == "drift":
        return await drift_check(
            ks_threshold=threshold if threshold else 0.1,
            **kwargs
        )
    elif check_type == "resource":
        return await resource_check(
            cpu_threshold=threshold if threshold else 80.0,
            **kwargs
        )
    else:
        return HealthCheckResult(
            name="Unknown Check",
            check_type=check_type,
            passed=False,
            error=f"Unknown check type: {check_type}"
        )
