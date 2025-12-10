/**
 * API client for CrowdStrike AI Pipeline Health Monitor
 */

const API_BASE = '/api';

export interface HealthCheck {
    id: number;
    name: string;
    description: string | null;
    check_type: string;
    enabled: boolean;
    interval_seconds: number;
    threshold_value: number | null;
    remediation_strategy: string | null;
    last_run: CheckRun | null;
}

export interface CheckRun {
    id: number;
    health_check_id: number;
    health_check_name: string | null;
    status: string;
    result_value: number | null;
    result_details: string | null;
    error_message: string | null;
    started_at: string;
    completed_at: string | null;
}

export interface Incident {
    id: number;
    title: string;
    description: string | null;
    severity: string;
    status: string;
    check_run_id: number | null;
    triggered_at: string;
    resolved_at: string | null;
    resolution_notes: string | null;
    remediation_attempts: RemediationAttempt[];
}

export interface RemediationAttempt {
    id: number;
    incident_id: number;
    strategy: string;
    dry_run: boolean;
    success: boolean;
    details: string | null;
    attempted_at: string;
    completed_at: string | null;
}

export interface RunCheckResult {
    check_name: string;
    check_type: string;
    passed: boolean;
    result_value: number | null;
    details: Record<string, unknown> | null;
    error: string | null;
    latency_ms: number | null;
    timestamp: string;
}

export interface InfrastructureSummary {
    total_instances: number;
    by_provider: Record<string, {
        instance_count: number;
        avg_cpu_util: number;
        avg_memory_util: number;
    }>;
    idle_count: number;
    overutilized_count: number;
    timestamp: string;
}

export interface RightsizingOpportunity {
    instance_id: string;
    provider: string;
    current_type: string;
    recommended_type: string;
    current_cpu_util: number;
    estimated_monthly_savings: number;
    confidence: string;
}

export interface CostSummary {
    total_instances: number;
    estimated_hourly_cost: number;
    estimated_monthly_cost: number;
    potential_monthly_savings: number;
    by_provider: Record<string, {
        instances: number;
        hourly_cost: number;
        monthly_cost: number;
    }>;
}

// API Functions
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
        ...options,
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
}

// Health Checks
export async function getHealthChecks(): Promise<HealthCheck[]> {
    return fetchAPI<HealthCheck[]>('/healthchecks');
}

export async function runHealthCheck(checkId?: number, checkType?: string): Promise<RunCheckResult> {
    return fetchAPI<RunCheckResult>('/healthchecks/run', {
        method: 'POST',
        body: JSON.stringify({ check_id: checkId, check_type: checkType }),
    });
}

export async function runAllHealthChecks(): Promise<{
    total: number;
    passed: number;
    failed: number;
    results: Array<{ check_id: number; check_name: string; passed: boolean }>;
}> {
    return fetchAPI('/healthchecks/run-all', { method: 'POST' });
}

export async function getCheckHistory(checkId: number, limit = 50): Promise<CheckRun[]> {
    return fetchAPI<CheckRun[]>(`/healthchecks/${checkId}/history?limit=${limit}`);
}

// Incidents
export async function getIncidents(status?: string, severity?: string): Promise<Incident[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (severity) params.append('severity', severity);

    const query = params.toString();
    return fetchAPI<Incident[]>(`/incidents${query ? `?${query}` : ''}`);
}

export async function createIncident(title: string, description?: string, severity = 'medium'): Promise<Incident> {
    return fetchAPI<Incident>('/incidents', {
        method: 'POST',
        body: JSON.stringify({ title, description, severity }),
    });
}

export async function remediate(incidentId: number, strategy: string, dryRun = false): Promise<{
    strategy: string;
    success: boolean;
    dry_run: boolean;
    details: Record<string, unknown> | null;
    error: string | null;
}> {
    return fetchAPI('/remediate', {
        method: 'POST',
        body: JSON.stringify({ incident_id: incidentId, strategy, dry_run: dryRun }),
    });
}

export async function resolveIncident(incidentId: number, notes?: string): Promise<{ status: string }> {
    return fetchAPI(`/incidents/${incidentId}/resolve`, {
        method: 'POST',
        body: JSON.stringify({ resolution_notes: notes }),
    });
}

export async function getIncidentsSummary(): Promise<{
    total: number;
    by_status: Record<string, number>;
    by_severity: Record<string, number>;
    last_24_hours: number;
}> {
    return fetchAPI('/incidents/summary');
}

// Infrastructure
export async function getInfrastructureSummary(): Promise<InfrastructureSummary> {
    return fetchAPI<InfrastructureSummary>('/infrastructure/summary');
}

export async function getInstanceMetrics(provider?: string): Promise<Array<{
    instance_id: string;
    provider: string;
    instance_type: string;
    cpu_util: number;
    memory_util: number;
}>> {
    const query = provider ? `?provider=${provider}` : '';
    return fetchAPI(`/infrastructure/metrics${query}`);
}

export async function getRightsizingOpportunities(): Promise<RightsizingOpportunity[]> {
    return fetchAPI<RightsizingOpportunity[]>('/rightsizing/opportunities');
}

export async function getCostSummary(): Promise<CostSummary> {
    return fetchAPI<CostSummary>('/infrastructure/cost-summary');
}

// Failure Injection (Demo)
export async function injectFailure(failureType: string, severity = 'medium'): Promise<{
    injected: string;
    severity: string;
    timestamp: string;
}> {
    return fetchAPI('/inject-failure', {
        method: 'POST',
        body: JSON.stringify({ failure_type: failureType, severity }),
    });
}

export async function clearFailures(): Promise<{ status: string }> {
    return fetchAPI('/clear-failures', { method: 'POST' });
}

export async function getModelHealth(): Promise<{
    status: string;
    endpoint: string;
    model_version: string;
    cache_size: number;
    failure_mode: {
        latency_multiplier: number;
        error_rate: number;
        drift_enabled: boolean;
        correctness_flip_rate: number;
    };
}> {
    return fetchAPI('/model-health');
}
