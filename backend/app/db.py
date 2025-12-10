"""
Database models and connection management for CrowdStrike AI Pipeline Health Monitor.
Uses SQLAlchemy with SQLite (demo) or PostgreSQL (production).
"""

import os
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.pool import StaticPool
import enum

# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./demo.db")

# SQLite-specific configuration for thread safety
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CheckType(enum.Enum):
    """Types of health checks supported by the system."""
    LATENCY = "latency"
    CORRECTNESS = "correctness"
    DRIFT = "drift"
    RESOURCE = "resource"


class CheckStatus(enum.Enum):
    """Status of a health check run."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class IncidentSeverity(enum.Enum):
    """Severity levels for incidents."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(enum.Enum):
    """Status of an incident."""
    OPEN = "open"
    REMEDIATING = "remediating"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class RemediationStrategy(enum.Enum):
    """Available remediation strategies."""
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    SCALE_HINT = "scale_hint"
    ROLLBACK_MODEL = "rollback_model"


class HealthCheck(Base):
    """Configuration for a health check."""
    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    check_type = Column(SQLEnum(CheckType), nullable=False)
    enabled = Column(Boolean, default=True)
    interval_seconds = Column(Integer, default=30)
    threshold_value = Column(Float)  # e.g., max latency in ms
    remediation_strategy = Column(SQLEnum(RemediationStrategy))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    runs = relationship("CheckRun", back_populates="health_check", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "check_type": self.check_type.value,
            "enabled": self.enabled,
            "interval_seconds": self.interval_seconds,
            "threshold_value": self.threshold_value,
            "remediation_strategy": self.remediation_strategy.value if self.remediation_strategy else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CheckRun(Base):
    """Individual execution of a health check."""
    __tablename__ = "check_runs"

    id = Column(Integer, primary_key=True, index=True)
    health_check_id = Column(Integer, ForeignKey("health_checks.id"), nullable=False)
    status = Column(SQLEnum(CheckStatus), default=CheckStatus.PENDING)
    result_value = Column(Float)  # e.g., actual latency measured
    result_details = Column(Text)  # JSON string with additional details
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    health_check = relationship("HealthCheck", back_populates="runs")

    def to_dict(self):
        return {
            "id": self.id,
            "health_check_id": self.health_check_id,
            "health_check_name": self.health_check.name if self.health_check else None,
            "status": self.status.value,
            "result_value": self.result_value,
            "result_details": self.result_details,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class Incident(Base):
    """An incident triggered by a failed health check."""
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    severity = Column(SQLEnum(IncidentSeverity), default=IncidentSeverity.MEDIUM)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.OPEN)
    check_run_id = Column(Integer, ForeignKey("check_runs.id"))
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)

    # Relationships
    check_run = relationship("CheckRun")
    remediation_attempts = relationship("RemediationAttempt", back_populates="incident", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "check_run_id": self.check_run_id,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "remediation_attempts": [r.to_dict() for r in self.remediation_attempts] if self.remediation_attempts else []
        }


class RemediationAttempt(Base):
    """Record of a remediation attempt for an incident."""
    __tablename__ = "remediation_attempts"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    strategy = Column(SQLEnum(RemediationStrategy), nullable=False)
    dry_run = Column(Boolean, default=False)
    success = Column(Boolean)
    details = Column(Text)  # JSON string with remediation details
    attempted_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    incident = relationship("Incident", back_populates="remediation_attempts")

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "strategy": self.strategy.value,
            "dry_run": self.dry_run,
            "success": self.success,
            "details": self.details,
            "attempted_at": self.attempted_at.isoformat() if self.attempted_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class InstanceMetric(Base):
    """Cloud infrastructure instance metrics for utilization analysis."""
    __tablename__ = "instance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(String(100), nullable=False, index=True)
    provider = Column(String(20))  # aws, gcp, oci
    resource_type = Column(String(50))  # vm, k8s-node, bare-metal
    instance_type = Column(String(50))
    region = Column(String(50))
    cpu_util = Column(Float)
    memory_util = Column(Float)
    disk_iops = Column(Float)
    network_in_bytes = Column(Float)
    network_out_bytes = Column(Float)
    ts = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "instance_id": self.instance_id,
            "provider": self.provider,
            "resource_type": self.resource_type,
            "instance_type": self.instance_type,
            "region": self.region,
            "cpu_util": self.cpu_util,
            "memory_util": self.memory_util,
            "disk_iops": self.disk_iops,
            "network_in_bytes": self.network_in_bytes,
            "network_out_bytes": self.network_out_bytes,
            "ts": self.ts.isoformat() if self.ts else None
        }


class Volume(Base):
    """Storage volume metrics for cost analysis."""
    __tablename__ = "volumes"

    id = Column(Integer, primary_key=True, index=True)
    volume_id = Column(String(100), nullable=False, unique=True)
    provider = Column(String(20))
    volume_type = Column(String(50))  # ssd, hdd, san, nas, object
    provisioned_bytes = Column(Float)
    used_bytes = Column(Float)
    attached_instance_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "volume_id": self.volume_id,
            "provider": self.provider,
            "volume_type": self.volume_type,
            "provisioned_bytes": self.provisioned_bytes,
            "used_bytes": self.used_bytes,
            "attached_instance_id": self.attached_instance_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "unused_bytes": self.provisioned_bytes - self.used_bytes if self.provisioned_bytes and self.used_bytes else 0
        }


# Dependency injection for FastAPI
def get_db():
    """Get database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def seed_demo_data(db):
    """Seed the database with demo health checks."""
    from sqlalchemy.orm import Session
    
    # Check if already seeded
    if db.query(HealthCheck).count() > 0:
        return
    
    demo_checks = [
        HealthCheck(
            name="Threat Detection Model Latency",
            description="Monitors inference latency for the threat detection ML model",
            check_type=CheckType.LATENCY,
            threshold_value=200.0,  # 200ms threshold
            remediation_strategy=RemediationStrategy.RESTART_SERVICE,
            interval_seconds=30
        ),
        HealthCheck(
            name="Malware Classifier Correctness",
            description="Validates malware classifier outputs against known samples",
            check_type=CheckType.CORRECTNESS,
            threshold_value=0.95,  # 95% accuracy threshold
            remediation_strategy=RemediationStrategy.ROLLBACK_MODEL,
            interval_seconds=60
        ),
        HealthCheck(
            name="Behavioral Analysis Drift",
            description="Detects distribution drift in behavioral analysis predictions",
            check_type=CheckType.DRIFT,
            threshold_value=0.1,  # KS statistic threshold
            remediation_strategy=RemediationStrategy.CLEAR_CACHE,
            interval_seconds=300
        ),
        HealthCheck(
            name="Inference Cluster Resources",
            description="Monitors CPU and memory usage of inference cluster",
            check_type=CheckType.RESOURCE,
            threshold_value=80.0,  # 80% utilization threshold
            remediation_strategy=RemediationStrategy.SCALE_HINT,
            interval_seconds=60
        )
    ]
    
    for check in demo_checks:
        db.add(check)
    
    db.commit()
