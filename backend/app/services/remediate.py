"""
Auto-remediation service for CrowdStrike AI Pipeline Health Monitor.
Implements remediation strategies with dry-run support and audit logging.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from app.services.model_client import model_client, clear_failures


class RemediationResult:
    """Result of a remediation attempt."""
    
    def __init__(self, strategy: str, success: bool, 
                 dry_run: bool = False, details: Dict[str, Any] = None,
                 error: str = None, duration_seconds: float = None):
        self.strategy = strategy
        self.success = success
        self.dry_run = dry_run
        self.details = details or {}
        self.error = error
        self.duration_seconds = duration_seconds
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "success": self.success,
            "dry_run": self.dry_run,
            "details": self.details,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp.isoformat()
        }


class Remediator:
    """
    Handles automatic and manual remediation of failing health checks.
    Supports multiple remediation strategies with configurable dry-run mode.
    """
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay_seconds = 5
        self.audit_log: List[Dict[str, Any]] = []
    
    async def remediate(self, strategy: str, incident_id: int = None,
                        dry_run: bool = False, **kwargs) -> RemediationResult:
        """
        Execute a remediation strategy.
        
        Args:
            strategy: Remediation strategy to execute
            incident_id: Associated incident ID
            dry_run: If True, simulate without actual changes
            **kwargs: Strategy-specific parameters
            
        Returns:
            RemediationResult with outcome details
        """
        start_time = datetime.utcnow()
        
        try:
            if strategy == "restart_service":
                result = await self._restart_service(dry_run, **kwargs)
            elif strategy == "clear_cache":
                result = await self._clear_cache(dry_run, **kwargs)
            elif strategy == "scale_hint":
                result = await self._scale_hint(dry_run, **kwargs)
            elif strategy == "rollback_model":
                result = await self._rollback_model(dry_run, **kwargs)
            else:
                result = RemediationResult(
                    strategy=strategy,
                    success=False,
                    dry_run=dry_run,
                    error=f"Unknown remediation strategy: {strategy}"
                )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            result.duration_seconds = duration
            
            # Log the attempt
            self._log_attempt(strategy, incident_id, result)
            
            return result
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            result = RemediationResult(
                strategy=strategy,
                success=False,
                dry_run=dry_run,
                error=str(e),
                duration_seconds=duration
            )
            self._log_attempt(strategy, incident_id, result)
            return result
    
    async def _restart_service(self, dry_run: bool, 
                               service_name: str = "inference-service",
                               **kwargs) -> RemediationResult:
        """
        Restart the inference service (simulated for demo).
        
        In production, this would call Docker API or Kubernetes API.
        """
        details = {
            "service": service_name,
            "action": "restart"
        }
        
        if dry_run:
            details["dry_run_message"] = f"Would restart service: {service_name}"
            return RemediationResult(
                strategy="restart_service",
                success=True,
                dry_run=True,
                details=details
            )
        
        # Simulate restart delay
        await asyncio.sleep(2)
        
        # Clear any injected failures (simulating restart fixing issues)
        clear_failures()
        
        details["restart_completed"] = True
        details["simulated"] = True
        details["command"] = f"docker restart {service_name}"
        
        return RemediationResult(
            strategy="restart_service",
            success=True,
            dry_run=False,
            details=details
        )
    
    async def _clear_cache(self, dry_run: bool, **kwargs) -> RemediationResult:
        """
        Clear the model inference cache.
        """
        details = {"action": "clear_cache"}
        
        if dry_run:
            details["dry_run_message"] = "Would clear model cache"
            return RemediationResult(
                strategy="clear_cache",
                success=True,
                dry_run=True,
                details=details
            )
        
        # Actually clear the cache
        cache_result = model_client.clear_cache()
        details.update(cache_result)
        
        return RemediationResult(
            strategy="clear_cache",
            success=True,
            dry_run=False,
            details=details
        )
    
    async def _scale_hint(self, dry_run: bool, 
                          target_replicas: int = 3,
                          **kwargs) -> RemediationResult:
        """
        Generate scaling recommendation (actual scaling requires cloud APIs).
        """
        details = {
            "action": "scale_hint",
            "recommendation": f"Scale inference service to {target_replicas} replicas",
            "target_replicas": target_replicas,
            "current_replicas": 1,
            "reason": "Resource utilization threshold exceeded"
        }
        
        # Generate kubectl command that would be used
        details["kubectl_command"] = f"kubectl scale deployment inference-service --replicas={target_replicas}"
        details["ansible_playbook"] = "scale_inference_service.yml"
        
        if dry_run:
            details["dry_run_message"] = "Would recommend scaling (no actual change)"
        else:
            details["recommendation_logged"] = True
            # In production, this would call cloud provider APIs or Kubernetes
        
        return RemediationResult(
            strategy="scale_hint",
            success=True,
            dry_run=dry_run,
            details=details
        )
    
    async def _rollback_model(self, dry_run: bool,
                              target_version: str = "v1.2.2",
                              **kwargs) -> RemediationResult:
        """
        Rollback to a previous model version (simulated).
        """
        current_version = model_client.model_version
        
        details = {
            "action": "rollback_model",
            "current_version": current_version,
            "target_version": target_version
        }
        
        if dry_run:
            details["dry_run_message"] = f"Would rollback from {current_version} to {target_version}"
            return RemediationResult(
                strategy="rollback_model",
                success=True,
                dry_run=True,
                details=details
            )
        
        # Simulate rollback delay
        await asyncio.sleep(1)
        
        # Update model version (simulated)
        model_client.model_version = target_version
        
        # Clear failures as rollback often fixes issues
        clear_failures()
        
        details["rollback_completed"] = True
        details["new_version"] = target_version
        
        return RemediationResult(
            strategy="rollback_model",
            success=True,
            dry_run=False,
            details=details
        )
    
    async def auto_remediate(self, incident_id: int, check_type: str,
                             strategy: str, max_retries: int = None,
                             dry_run: bool = False) -> List[RemediationResult]:
        """
        Attempt automatic remediation with retries.
        
        Args:
            incident_id: ID of the incident to remediate
            check_type: Type of the failing health check
            strategy: Remediation strategy to use
            max_retries: Maximum remediation attempts
            dry_run: If True, simulate without actual changes
            
        Returns:
            List of RemediationResults for each attempt
        """
        if max_retries is None:
            max_retries = self.max_retries
        
        results = []
        
        for attempt in range(max_retries):
            result = await self.remediate(
                strategy=strategy,
                incident_id=incident_id,
                dry_run=dry_run,
                attempt_number=attempt + 1
            )
            results.append(result)
            
            if result.success:
                break
            
            if attempt < max_retries - 1:
                await asyncio.sleep(self.retry_delay_seconds)
        
        return results
    
    def _log_attempt(self, strategy: str, incident_id: int, 
                     result: RemediationResult):
        """Log remediation attempt to audit log."""
        log_entry = {
            "strategy": strategy,
            "incident_id": incident_id,
            "success": result.success,
            "dry_run": result.dry_run,
            "timestamp": result.timestamp.isoformat(),
            "duration_seconds": result.duration_seconds
        }
        
        if result.error:
            log_entry["error"] = result.error
        
        self.audit_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        return self.audit_log[-limit:]


# Global remediator instance
remediator = Remediator()


async def execute_remediation(strategy: str, incident_id: int = None,
                              dry_run: bool = False, **kwargs) -> RemediationResult:
    """Convenience function to execute remediation."""
    return await remediator.remediate(strategy, incident_id, dry_run, **kwargs)


async def auto_remediate_incident(incident_id: int, check_type: str,
                                  strategy: str, dry_run: bool = False) -> List[RemediationResult]:
    """Convenience function for automatic remediation."""
    return await remediator.auto_remediate(incident_id, check_type, strategy, dry_run=dry_run)
