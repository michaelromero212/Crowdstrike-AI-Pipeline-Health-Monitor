"""
Prometheus metrics exporter for CrowdStrike AI Pipeline Health Monitor.
Exposes metrics at /metrics endpoint for monitoring and observability.
"""

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime

# Application info
app_info = Info('pipeline_monitor', 'CrowdStrike AI Pipeline Health Monitor')
app_info.info({
    'version': '0.1.0',
    'environment': 'demo'
})

# Health check metrics
health_check_runs_total = Counter(
    'health_check_runs_total',
    'Total number of health check runs',
    ['check_name', 'check_type', 'status']
)

health_check_latency_ms = Histogram(
    'health_check_latency_ms',
    'Health check execution latency in milliseconds',
    ['check_name', 'check_type'],
    buckets=[10, 25, 50, 100, 200, 500, 1000, 2500, 5000]
)

health_check_status = Gauge(
    'health_check_status',
    'Current status of health check (1=passed, 0=failed)',
    ['check_name', 'check_type']
)

health_check_last_result = Gauge(
    'health_check_last_result_value',
    'Last result value from health check',
    ['check_name', 'check_type']
)

# Incident metrics
incidents_total = Counter(
    'incidents_total',
    'Total number of incidents created',
    ['severity']
)

incidents_active = Gauge(
    'incidents_active',
    'Number of currently active incidents',
    ['severity']
)

# Remediation metrics
remediation_attempts_total = Counter(
    'remediation_attempts_total',
    'Total remediation attempts',
    ['strategy', 'success']
)

remediation_duration_seconds = Histogram(
    'remediation_duration_seconds',
    'Remediation execution duration in seconds',
    ['strategy'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60]
)

# Infrastructure metrics (for cloud monitoring demo)
instance_cpu_utilization = Gauge(
    'instance_cpu_utilization_percent',
    'CPU utilization percentage',
    ['instance_id', 'provider', 'instance_type']
)

instance_memory_utilization = Gauge(
    'instance_memory_utilization_percent',
    'Memory utilization percentage',
    ['instance_id', 'provider', 'instance_type']
)

volume_usage_bytes = Gauge(
    'volume_usage_bytes',
    'Volume used space in bytes',
    ['volume_id', 'provider', 'volume_type']
)

volume_unused_bytes = Gauge(
    'volume_unused_bytes',
    'Volume unused space in bytes',
    ['volume_id', 'provider', 'volume_type']
)


def record_health_check_run(check_name: str, check_type: str, status: str, 
                             latency_ms: float = None, result_value: float = None):
    """Record metrics for a health check run."""
    health_check_runs_total.labels(
        check_name=check_name,
        check_type=check_type,
        status=status
    ).inc()
    
    if latency_ms is not None:
        health_check_latency_ms.labels(
            check_name=check_name,
            check_type=check_type
        ).observe(latency_ms)
    
    health_check_status.labels(
        check_name=check_name,
        check_type=check_type
    ).set(1 if status == 'passed' else 0)
    
    if result_value is not None:
        health_check_last_result.labels(
            check_name=check_name,
            check_type=check_type
        ).set(result_value)


def record_incident(severity: str):
    """Record a new incident creation."""
    incidents_total.labels(severity=severity).inc()


def update_active_incidents(severity_counts: dict):
    """Update gauge for active incidents by severity."""
    for severity, count in severity_counts.items():
        incidents_active.labels(severity=severity).set(count)


def record_remediation(strategy: str, success: bool, duration_seconds: float):
    """Record a remediation attempt."""
    remediation_attempts_total.labels(
        strategy=strategy,
        success=str(success).lower()
    ).inc()
    
    remediation_duration_seconds.labels(strategy=strategy).observe(duration_seconds)


def update_instance_metrics(instance_id: str, provider: str, instance_type: str,
                            cpu_util: float, memory_util: float):
    """Update infrastructure instance metrics."""
    instance_cpu_utilization.labels(
        instance_id=instance_id,
        provider=provider,
        instance_type=instance_type
    ).set(cpu_util)
    
    instance_memory_utilization.labels(
        instance_id=instance_id,
        provider=provider,
        instance_type=instance_type
    ).set(memory_util)


def update_volume_metrics(volume_id: str, provider: str, volume_type: str,
                          used_bytes: float, unused_bytes: float):
    """Update storage volume metrics."""
    volume_usage_bytes.labels(
        volume_id=volume_id,
        provider=provider,
        volume_type=volume_type
    ).set(used_bytes)
    
    volume_unused_bytes.labels(
        volume_id=volume_id,
        provider=provider,
        volume_type=volume_type
    ).set(unused_bytes)


def get_metrics():
    """Generate Prometheus metrics output."""
    return generate_latest()


def get_metrics_content_type():
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST
