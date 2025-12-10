"""
Health check API routes for CrowdStrike AI Pipeline Health Monitor.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db import get_db, HealthCheck, CheckRun, CheckStatus, CheckType, seed_demo_data
from app.services.checker import run_check, HealthCheckResult
from app.services.model_client import inject_failure, clear_failures, model_client
from app.metrics import (
    get_metrics, get_metrics_content_type, record_health_check_run
)

router = APIRouter()


# Pydantic models for request/response
class HealthCheckResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    check_type: str
    enabled: bool
    interval_seconds: int
    threshold_value: Optional[float]
    remediation_strategy: Optional[str]
    last_run: Optional[dict] = None
    
    class Config:
        from_attributes = True


class RunCheckRequest(BaseModel):
    check_id: Optional[int] = None
    check_type: Optional[str] = None
    threshold: Optional[float] = None


class RunCheckResponse(BaseModel):
    check_name: str
    check_type: str
    passed: bool
    result_value: Optional[float]
    details: Optional[dict]
    error: Optional[str]
    latency_ms: Optional[float]
    timestamp: str


class InjectFailureRequest(BaseModel):
    failure_type: str  # latency, error, drift, correctness
    severity: str = "medium"  # low, medium, high


class ModelHealthResponse(BaseModel):
    status: str
    endpoint: str
    model_version: str
    cache_size: int
    failure_mode: dict


@router.get("/healthchecks", response_model=List[HealthCheckResponse])
async def list_health_checks(db: Session = Depends(get_db)):
    """
    List all configured health checks with their latest run results.
    """
    # Ensure demo data exists
    seed_demo_data(db)
    
    checks = db.query(HealthCheck).filter(HealthCheck.enabled == True).all()
    results = []
    
    for check in checks:
        check_dict = check.to_dict()
        
        # Get latest run
        latest_run = (
            db.query(CheckRun)
            .filter(CheckRun.health_check_id == check.id)
            .order_by(CheckRun.started_at.desc())
            .first()
        )
        
        if latest_run:
            check_dict["last_run"] = latest_run.to_dict()
        
        results.append(HealthCheckResponse(**check_dict))
    
    return results


@router.get("/healthchecks/{check_id}", response_model=HealthCheckResponse)
async def get_health_check(check_id: int, db: Session = Depends(get_db)):
    """
    Get details for a specific health check.
    """
    check = db.query(HealthCheck).filter(HealthCheck.id == check_id).first()
    
    if not check:
        raise HTTPException(status_code=404, detail="Health check not found")
    
    check_dict = check.to_dict()
    
    # Get latest run
    latest_run = (
        db.query(CheckRun)
        .filter(CheckRun.health_check_id == check.id)
        .order_by(CheckRun.started_at.desc())
        .first()
    )
    
    if latest_run:
        check_dict["last_run"] = latest_run.to_dict()
    
    return HealthCheckResponse(**check_dict)


@router.post("/healthchecks/run", response_model=RunCheckResponse)
async def run_health_check(request: RunCheckRequest, db: Session = Depends(get_db)):
    """
    Trigger a health check run.
    Can specify either check_id (to run a configured check) or check_type (for ad-hoc).
    """
    import json
    
    if request.check_id:
        # Run configured check
        check = db.query(HealthCheck).filter(HealthCheck.id == request.check_id).first()
        if not check:
            raise HTTPException(status_code=404, detail="Health check not found")
        
        check_type = check.check_type.value
        threshold = request.threshold or check.threshold_value
        check_name = check.name
    elif request.check_type:
        # Ad-hoc check
        check_type = request.check_type
        threshold = request.threshold
        check_name = f"Ad-hoc {check_type} check"
        check = None
    else:
        raise HTTPException(status_code=400, detail="Must specify check_id or check_type")
    
    
    # Run the check via helper to ensure persistence and incident creation
    result_data = await _execute_and_record_check(db, check)
    
    # Record metrics (redundant but keeping for consistency if needed, or _execute handles it)
    # The helper handles DB, let's let it handle everything.
    
    return RunCheckResponse(
        check_name=result_data["check_name"],
        check_type=result_data["check_type"],
        passed=result_data["passed"],
        result_value=result_data["result_value"],
        details=result_data["details"],
        error=result_data["error"],
        latency_ms=result_data["latency_ms"],
        timestamp=result_data["timestamp"]
    )


@router.post("/healthchecks/run-all")
async def run_all_health_checks(db: Session = Depends(get_db)):
    """
    Run all enabled health checks.
    """
    seed_demo_data(db)
    checks = db.query(HealthCheck).filter(HealthCheck.enabled == True).all()
    
    results = []
    for check in checks:
        # Use helper to persist run and create incident
        res = await _execute_and_record_check(db, check)
        results.append({
            "check_id": check.id,
            "check_name": check.name,
            "passed": res["passed"],
            "result_value": res["result_value"],
            "error": res["error"]
        })
    
    return {
        "total": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "results": results
    }


async def _execute_and_record_check(db: Session, check: HealthCheck) -> dict:
    """
    Helper to run a check, record history, and create incident on failure.
    """
    import json
    
    # Run service
    result = await run_check(check.check_type.value, check.threshold_value)
    
    # Record Run
    check_run = CheckRun(
        health_check_id=check.id,
        status=CheckStatus.PASSED if result.passed else CheckStatus.FAILED,
        result_value=result.result_value,
        result_details=json.dumps(result.details) if result.details else None,
        error_message=result.error,
        started_at=result.timestamp,
        completed_at=datetime.utcnow()
    )
    db.add(check_run)
    db.commit()
    db.refresh(check_run)
    
    # Create Incident if failed
    if not result.passed:
        # Check for existing open incident for this check?
        # For demo simplicity, always create new or update unique one. 
        # Let's create new for now to ensure visibility.
        
        from app.db import Incident, IncidentSeverity, IncidentStatus
        
        severity = IncidentSeverity.MEDIUM
        if "latency" in check.check_type.value:
            severity = IncidentSeverity.HIGH
        elif "correctness" in check.check_type.value:
            severity = IncidentSeverity.CRITICAL
            
        incident = Incident(
            title=f"Health Check Failed: {check.name}",
            description=f"Check failed with value {result.result_value} (threshold: {check.threshold_value}). {result.error or ''}",
            severity=severity,
            status=IncidentStatus.OPEN,
            check_run_id=check_run.id,
            triggered_at=datetime.utcnow()
        )
        db.add(incident)
        db.commit()
        
        # Record incident metric
        from app.metrics import record_incident
        record_incident(severity.value)

    # Record run metric
    record_health_check_run(
        check_name=check.name,
        check_type=check.check_type.value,
        status="passed" if result.passed else "failed",
        latency_ms=result.latency_ms,
        result_value=result.result_value
    )
    
    return {
        "check_name": check.name,
        "check_type": check.check_type.value,
        "passed": result.passed,
        "result_value": result.result_value,
        "details": result.details,
        "error": result.error,
        "latency_ms": result.latency_ms,
        "timestamp": result.timestamp.isoformat()
    }


@router.get("/healthchecks/{check_id}/history")
async def get_check_history(
    check_id: int, 
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """
    Get run history for a health check.
    """
    runs = (
        db.query(CheckRun)
        .filter(CheckRun.health_check_id == check_id)
        .order_by(CheckRun.started_at.desc())
        .limit(limit)
        .all()
    )
    
    return [run.to_dict() for run in runs]


@router.get("/metrics")
async def get_prometheus_metrics():
    """
    Prometheus metrics endpoint.
    """
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )


@router.post("/inject-failure")
async def inject_demo_failure(request: InjectFailureRequest):
    """
    Inject a failure for demo purposes.
    """
    result = inject_failure(request.failure_type, request.severity)
    return result


@router.post("/clear-failures")
async def clear_demo_failures():
    """
    Clear all injected failures.
    """
    result = clear_failures()
    return result


@router.get("/model-health", response_model=ModelHealthResponse)
async def get_model_health():
    """
    Get current model client health status.
    """
    health = model_client.get_health()
    return ModelHealthResponse(**health)
