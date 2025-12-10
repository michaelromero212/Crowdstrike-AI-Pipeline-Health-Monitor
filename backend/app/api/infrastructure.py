"""
Infrastructure metrics API routes for CrowdStrike AI Pipeline Health Monitor.
Exposes cloud metrics, rightsizing recommendations, and optimization reports.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.services.cloud_ingestor import cloud_ingestor
from app.services.rightsizing import rightsizing_engine

router = APIRouter()


class InstanceMetricResponse(BaseModel):
    instance_id: str
    provider: str
    resource_type: str
    instance_type: str
    region: str
    cpu_util: float
    memory_util: float
    disk_iops: float
    network_in_bytes: float
    network_out_bytes: float
    ts: str


class RightsizingOpportunity(BaseModel):
    instance_id: str
    provider: str
    current_type: str
    recommended_type: str
    current_cpu_util: float
    current_cost_per_hour: float
    recommended_cost_per_hour: float
    estimated_monthly_savings: float
    confidence: str


@router.get("/infrastructure/instances")
async def list_instances(provider: Optional[str] = Query(default=None)):
    """
    List all cloud instances, optionally filtered by provider.
    """
    instances = cloud_ingestor.get_instances(provider)
    return {
        "total": len(instances),
        "instances": [
            {
                "instance_id": i["instance_id"],
                "provider": i["provider"],
                "instance_type": i["instance_type"],
                "region": i["region"],
                "resource_type": i["resource_type"],
                "specs": i["specs"],
                "utilization_profile": i["utilization_profile"]
            }
            for i in instances
        ]
    }


@router.get("/infrastructure/metrics", response_model=List[InstanceMetricResponse])
async def get_instance_metrics(
    provider: Optional[str] = Query(default=None),
    instance_id: Optional[str] = Query(default=None)
):
    """
    Get current metrics for cloud instances.
    """
    if instance_id:
        metrics = cloud_ingestor.collect_metrics(instance_id)
    else:
        metrics = cloud_ingestor.collect_metrics()
        if provider:
            metrics = [m for m in metrics if m["provider"] == provider]
    
    return [
        InstanceMetricResponse(
            instance_id=m["instance_id"],
            provider=m["provider"],
            resource_type=m["resource_type"],
            instance_type=m["instance_type"],
            region=m["region"],
            cpu_util=m["cpu_util"],
            memory_util=m["memory_util"],
            disk_iops=m["disk_iops"],
            network_in_bytes=m["network_in_bytes"],
            network_out_bytes=m["network_out_bytes"],
            ts=m["ts"].isoformat()
        )
        for m in metrics
    ]


@router.get("/infrastructure/summary")
async def get_infrastructure_summary():
    """
    Get summary statistics across all cloud infrastructure.
    """
    return cloud_ingestor.get_summary_stats()


@router.get("/infrastructure/idle")
async def get_idle_instances(threshold: float = Query(default=10)):
    """
    Get instances with CPU utilization below threshold.
    """
    idle = cloud_ingestor.get_idle_instances(threshold)
    return {
        "threshold_cpu": threshold,
        "count": len(idle),
        "instances": idle
    }


@router.get("/rightsizing/opportunities", response_model=List[RightsizingOpportunity])
async def get_rightsizing_opportunities(limit: int = Query(default=20, le=100)):
    """
    Get rightsizing opportunities with estimated savings.
    """
    opportunities = cloud_ingestor.get_rightsizing_opportunities()[:limit]
    return [
        RightsizingOpportunity(
            instance_id=o["instance_id"],
            provider=o["provider"],
            current_type=o["current_type"],
            recommended_type=o["recommended_type"],
            current_cpu_util=o["current_cpu_util"],
            current_cost_per_hour=o["current_cost_per_hour"],
            recommended_cost_per_hour=o["recommended_cost_per_hour"],
            estimated_monthly_savings=o["estimated_monthly_savings"],
            confidence=o["confidence"]
        )
        for o in opportunities
    ]


@router.get("/rightsizing/analysis/{instance_id}")
async def analyze_instance(instance_id: str):
    """
    Get detailed rightsizing analysis for a specific instance.
    """
    return rightsizing_engine.analyze_instance(instance_id)


@router.get("/rightsizing/report")
async def generate_rightsizing_report():
    """
    Generate a comprehensive rightsizing report.
    """
    return rightsizing_engine.generate_report()


@router.get("/rightsizing/report/csv", response_class=PlainTextResponse)
async def export_rightsizing_csv():
    """
    Export rightsizing recommendations as CSV.
    """
    csv_content = rightsizing_engine.export_csv_report()
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=rightsizing_report.csv"}
    )


@router.get("/rightsizing/playbook", response_class=PlainTextResponse)
async def generate_ansible_playbook():
    """
    Generate Ansible playbook for recommended changes.
    """
    opportunities = cloud_ingestor.get_rightsizing_opportunities()
    playbook = rightsizing_engine.generate_ansible_playbook(opportunities)
    return PlainTextResponse(
        content=playbook,
        media_type="text/yaml",
        headers={"Content-Disposition": "attachment; filename=rightsizing_playbook.yml"}
    )


@router.get("/infrastructure/cost-summary")
async def get_cost_summary():
    """
    Get estimated cost summary across all infrastructure.
    """
    instances = cloud_ingestor.get_instances()
    
    total_hourly = 0
    by_provider = {}
    
    for instance in instances:
        provider = instance["provider"]
        cost = instance["specs"].get("cost_per_hour", 0)
        total_hourly += cost
        
        if provider not in by_provider:
            by_provider[provider] = {"instances": 0, "hourly_cost": 0}
        
        by_provider[provider]["instances"] += 1
        by_provider[provider]["hourly_cost"] += cost
    
    # Calculate monthly costs (730 hours/month average)
    return {
        "total_instances": len(instances),
        "estimated_hourly_cost": round(total_hourly, 2),
        "estimated_monthly_cost": round(total_hourly * 730, 2),
        "by_provider": {
            p: {
                "instances": v["instances"],
                "hourly_cost": round(v["hourly_cost"], 2),
                "monthly_cost": round(v["hourly_cost"] * 730, 2)
            }
            for p, v in by_provider.items()
        },
        "potential_monthly_savings": sum(
            o["estimated_monthly_savings"] 
            for o in cloud_ingestor.get_rightsizing_opportunities()
        ),
        "timestamp": datetime.utcnow().isoformat()
    }
