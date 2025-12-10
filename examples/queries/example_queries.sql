-- CrowdStrike AI Pipeline Health Monitor - Example SQL Queries
-- These queries demonstrate infrastructure analysis capabilities

-- ============================================================
-- 1. Find idle instances (<10% CPU for analysis period)
-- ============================================================
SELECT 
    instance_id,
    provider,
    instance_type,
    AVG(cpu_util) as avg_cpu,
    COUNT(*) as sample_count
FROM instance_metrics
WHERE ts >= datetime('now', '-30 days')
GROUP BY instance_id, provider, instance_type
HAVING AVG(cpu_util) < 10
ORDER BY avg_cpu ASC
LIMIT 20;


-- ============================================================
-- 2. Top volumes by unused capacity
-- ============================================================
SELECT 
    volume_id,
    provider,
    volume_type,
    provisioned_bytes,
    used_bytes,
    (provisioned_bytes - used_bytes) as unused_bytes,
    ROUND((1.0 - used_bytes / provisioned_bytes) * 100, 2) as percent_unused
FROM volumes
WHERE provisioned_bytes > 0
ORDER BY unused_bytes DESC
LIMIT 10;


-- ============================================================
-- 3. Instances with high resource variance (unstable workloads)
-- ============================================================
SELECT 
    instance_id,
    provider,
    AVG(cpu_util) as avg_cpu,
    MAX(cpu_util) - MIN(cpu_util) as cpu_range,
    AVG(memory_util) as avg_memory
FROM instance_metrics
WHERE ts >= datetime('now', '-7 days')
GROUP BY instance_id, provider
HAVING (MAX(cpu_util) - MIN(cpu_util)) > 50
ORDER BY cpu_range DESC
LIMIT 20;


-- ============================================================
-- 4. Cost attribution by provider and resource type
-- ============================================================
-- Note: Assumes a cost_per_hour column or join with instance types
SELECT 
    provider,
    resource_type,
    COUNT(DISTINCT instance_id) as instance_count,
    AVG(cpu_util) as avg_cpu_util,
    AVG(memory_util) as avg_memory_util
FROM instance_metrics
WHERE ts >= datetime('now', '-24 hours')
GROUP BY provider, resource_type
ORDER BY provider, resource_type;


-- ============================================================
-- 5. Health check failure trends
-- ============================================================
SELECT 
    date(started_at) as check_date,
    hc.check_type,
    COUNT(*) as total_runs,
    SUM(CASE WHEN cr.status = 'passed' THEN 1 ELSE 0 END) as passed,
    SUM(CASE WHEN cr.status = 'failed' THEN 1 ELSE 0 END) as failed,
    ROUND(100.0 * SUM(CASE WHEN cr.status = 'passed' THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
FROM check_runs cr
JOIN health_checks hc ON cr.health_check_id = hc.id
WHERE started_at >= datetime('now', '-14 days')
GROUP BY date(started_at), hc.check_type
ORDER BY check_date DESC, hc.check_type;


-- ============================================================
-- 6. Incident response time analysis (MTTR)
-- ============================================================
SELECT 
    severity,
    COUNT(*) as incident_count,
    AVG(
        (julianday(resolved_at) - julianday(triggered_at)) * 24 * 60
    ) as avg_mttr_minutes,
    MIN(
        (julianday(resolved_at) - julianday(triggered_at)) * 24 * 60
    ) as min_mttr_minutes,
    MAX(
        (julianday(resolved_at) - julianday(triggered_at)) * 24 * 60
    ) as max_mttr_minutes
FROM incidents
WHERE resolved_at IS NOT NULL
GROUP BY severity
ORDER BY 
    CASE severity 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'medium' THEN 3 
        ELSE 4 
    END;


-- ============================================================
-- 7. Remediation success rate by strategy
-- ============================================================
SELECT 
    strategy,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
    ROUND(100.0 * SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM remediation_attempts
WHERE dry_run = 0
GROUP BY strategy
ORDER BY success_rate DESC;


-- ============================================================
-- 8. Peak utilization hours (for capacity planning)
-- ============================================================
SELECT 
    strftime('%H', ts) as hour_of_day,
    provider,
    AVG(cpu_util) as avg_cpu,
    MAX(cpu_util) as peak_cpu,
    AVG(memory_util) as avg_memory
FROM instance_metrics
WHERE ts >= datetime('now', '-7 days')
GROUP BY strftime('%H', ts), provider
ORDER BY provider, hour_of_day;


-- ============================================================
-- 9. Orphaned/unused resources detection
-- ============================================================
SELECT 
    v.volume_id,
    v.provider,
    v.volume_type,
    v.provisioned_bytes,
    v.attached_instance_id,
    datetime(v.last_accessed) as last_accessed,
    julianday('now') - julianday(v.last_accessed) as days_since_access
FROM volumes v
WHERE v.attached_instance_id IS NULL
   OR julianday('now') - julianday(v.last_accessed) > 30
ORDER BY days_since_access DESC;


-- ============================================================
-- 10. Infrastructure growth trend
-- ============================================================
SELECT 
    date(ts) as date,
    provider,
    COUNT(DISTINCT instance_id) as active_instances,
    AVG(cpu_util) as avg_cpu,
    AVG(memory_util) as avg_memory
FROM instance_metrics
WHERE ts >= datetime('now', '-30 days')
GROUP BY date(ts), provider
ORDER BY date DESC, provider;
