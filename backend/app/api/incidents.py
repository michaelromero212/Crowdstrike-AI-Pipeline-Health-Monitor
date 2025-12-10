"""
Incidents and remediation API routes for CrowdStrike AI Pipeline Health Monitor.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from app.db import (
    get_db, Incident, IncidentStatus, IncidentSeverity, 
    RemediationAttempt, RemediationStrategy, CheckRun
)
from app.services.remediate import execute_remediation, auto_remediate_incident, remediator
from app.metrics import record_incident, record_remediation

router = APIRouter()


# Pydantic models
class IncidentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    severity: str
    status: str
    check_run_id: Optional[int]
    triggered_at: str
    resolved_at: Optional[str]
    resolution_notes: Optional[str]
    remediation_attempts: List[dict] = []
    
    class Config:
        from_attributes = True


class CreateIncidentRequest(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "medium"
    check_run_id: Optional[int] = None


class RemediateRequest(BaseModel):
    incident_id: int
    strategy: str
    dry_run: bool = False


class RemediationResponse(BaseModel):
    strategy: str
    success: bool
    dry_run: bool
    details: Optional[dict]
    error: Optional[str]
    duration_seconds: Optional[float]
    timestamp: str


class AutoRemediateRequest(BaseModel):
    incident_id: int
    strategy: str
    max_retries: int = 3
    dry_run: bool = False


class ResolveIncidentRequest(BaseModel):
    resolution_notes: Optional[str] = None


@router.get("/incidents", response_model=List[IncidentResponse])
async def list_incidents(
    status: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """
    List incidents with optional filtering.
    """
    query = db.query(Incident)
    
    if status:
        try:
            status_enum = IncidentStatus(status)
            query = query.filter(Incident.status == status_enum)
        except ValueError:
            pass
    
    if severity:
        try:
            severity_enum = IncidentSeverity(severity)
            query = query.filter(Incident.severity == severity_enum)
        except ValueError:
            pass
    
    incidents = query.order_by(desc(Incident.triggered_at)).limit(limit).all()
    
    return [
        IncidentResponse(
            id=inc.id,
            title=inc.title,
            description=inc.description,
            severity=inc.severity.value,
            status=inc.status.value,
            check_run_id=inc.check_run_id,
            triggered_at=inc.triggered_at.isoformat() if inc.triggered_at else None,
            resolved_at=inc.resolved_at.isoformat() if inc.resolved_at else None,
            resolution_notes=inc.resolution_notes,
            remediation_attempts=[r.to_dict() for r in inc.remediation_attempts]
        )
        for inc in incidents
    ]


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """
    Get details for a specific incident.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity.value,
        status=incident.status.value,
        check_run_id=incident.check_run_id,
        triggered_at=incident.triggered_at.isoformat() if incident.triggered_at else None,
        resolved_at=incident.resolved_at.isoformat() if incident.resolved_at else None,
        resolution_notes=incident.resolution_notes,
        remediation_attempts=[r.to_dict() for r in incident.remediation_attempts]
    )


@router.post("/incidents", response_model=IncidentResponse)
async def create_incident(request: CreateIncidentRequest, db: Session = Depends(get_db)):
    """
    Create a new incident.
    """
    try:
        severity = IncidentSeverity(request.severity)
    except ValueError:
        severity = IncidentSeverity.MEDIUM
    
    incident = Incident(
        title=request.title,
        description=request.description,
        severity=severity,
        status=IncidentStatus.OPEN,
        check_run_id=request.check_run_id,
        triggered_at=datetime.utcnow()
    )
    
    db.add(incident)
    db.commit()
    db.refresh(incident)
    
    # Record metric
    record_incident(severity.value)
    
    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity.value,
        status=incident.status.value,
        check_run_id=incident.check_run_id,
        triggered_at=incident.triggered_at.isoformat(),
        resolved_at=None,
        resolution_notes=None,
        remediation_attempts=[]
    )


@router.post("/remediate", response_model=RemediationResponse)
async def remediate_incident(request: RemediateRequest, db: Session = Depends(get_db)):
    """
    Trigger remediation for an incident.
    """
    # Verify incident exists
    incident = db.query(Incident).filter(Incident.id == request.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Validate strategy
    try:
        strategy = RemediationStrategy(request.strategy)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid strategy: {request.strategy}")
    
    # Update incident status
    incident.status = IncidentStatus.REMEDIATING
    db.commit()
    
    # Execute remediation
    result = await execute_remediation(
        strategy=request.strategy,
        incident_id=request.incident_id,
        dry_run=request.dry_run
    )
    
    # Record attempt in database
    attempt = RemediationAttempt(
        incident_id=incident.id,
        strategy=strategy,
        dry_run=request.dry_run,
        success=result.success,
        details=str(result.details) if result.details else None,
        attempted_at=result.timestamp,
        completed_at=datetime.utcnow()
    )
    db.add(attempt)
    
    # Update incident status based on result
    if result.success and not request.dry_run:
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.utcnow()
    elif not result.success:
        incident.status = IncidentStatus.ESCALATED
    
    db.commit()
    
    # Record metric
    record_remediation(request.strategy, result.success, result.duration_seconds or 0)
    
    return RemediationResponse(
        strategy=result.strategy,
        success=result.success,
        dry_run=result.dry_run,
        details=result.details,
        error=result.error,
        duration_seconds=result.duration_seconds,
        timestamp=result.timestamp.isoformat()
    )


@router.post("/auto-remediate")
async def auto_remediate(request: AutoRemediateRequest, db: Session = Depends(get_db)):
    """
    Trigger automatic remediation with retries.
    """
    # Verify incident exists
    incident = db.query(Incident).filter(Incident.id == request.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get check type from associated run
    check_type = "unknown"
    if incident.check_run_id:
        run = db.query(CheckRun).filter(CheckRun.id == incident.check_run_id).first()
        if run and run.health_check:
            check_type = run.health_check.check_type.value
    
    # Update status
    incident.status = IncidentStatus.REMEDIATING
    db.commit()
    
    # Run auto-remediation
    results = await auto_remediate_incident(
        incident_id=request.incident_id,
        check_type=check_type,
        strategy=request.strategy,
        dry_run=request.dry_run
    )
    
    # Record all attempts
    for result in results:
        try:
            strategy = RemediationStrategy(result.strategy)
        except ValueError:
            strategy = RemediationStrategy.RESTART_SERVICE
            
        attempt = RemediationAttempt(
            incident_id=incident.id,
            strategy=strategy,
            dry_run=result.dry_run,
            success=result.success,
            details=str(result.details) if result.details else None,
            attempted_at=result.timestamp,
            completed_at=datetime.utcnow()
        )
        db.add(attempt)
    
    # Update incident based on final result
    final_success = results[-1].success if results else False
    if final_success and not request.dry_run:
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.utcnow()
    elif not final_success:
        incident.status = IncidentStatus.ESCALATED
    
    db.commit()
    
    return {
        "incident_id": request.incident_id,
        "attempts": len(results),
        "final_success": final_success,
        "results": [r.to_dict() for r in results]
    }


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: int, 
    request: ResolveIncidentRequest,
    db: Session = Depends(get_db)
):
    """
    Manually resolve an incident.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident.status = IncidentStatus.RESOLVED
    incident.resolved_at = datetime.utcnow()
    incident.resolution_notes = request.resolution_notes
    
    db.commit()
    
    return {"status": "resolved", "incident_id": incident_id}


@router.get("/remediation-audit")
async def get_remediation_audit(limit: int = Query(default=100, le=500)):
    """
    Get remediation audit log.
    """
    return remediator.get_audit_log(limit)


@router.get("/incidents/summary")
async def get_incidents_summary(db: Session = Depends(get_db)):
    """
    Get summary statistics for incidents.
    """
    from sqlalchemy import func
    
    total = db.query(func.count(Incident.id)).scalar()
    
    by_status = dict(
        db.query(Incident.status, func.count(Incident.id))
        .group_by(Incident.status)
        .all()
    )
    
    by_severity = dict(
        db.query(Incident.severity, func.count(Incident.id))
        .group_by(Incident.severity)
        .all()
    )
    
    # Recent incidents (last 24 hours)
    from datetime import timedelta
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_count = (
        db.query(func.count(Incident.id))
        .filter(Incident.triggered_at >= recent_cutoff)
        .scalar()
    )
    
    return {
        "total": total,
        "by_status": {k.value: v for k, v in by_status.items()},
        "by_severity": {k.value: v for k, v in by_severity.items()},
        "last_24_hours": recent_count,
        "timestamp": datetime.utcnow().isoformat()
    }
