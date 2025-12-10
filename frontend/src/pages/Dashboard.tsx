import React, { useState, useEffect, useCallback } from 'react';
import HealthCheckCard from '../components/HealthCheckCard';
import PlotlyChart from '../components/PlotlyChart';
import {
    getHealthChecks,
    runHealthCheck,
    runAllHealthChecks,
    getIncidentsSummary,
    getIncidents,
    injectFailure,
    clearFailures,
    getModelHealth,
    HealthCheck,
    Incident
} from '../api';
import { Data } from 'plotly.js';

const Dashboard: React.FC = () => {
    const [healthChecks, setHealthChecks] = useState<HealthCheck[]>([]);
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [incidentSummary, setIncidentSummary] = useState<{ total: number; by_status: Record<string, number> } | null>(null);
    const [runningChecks, setRunningChecks] = useState<Set<number>>(new Set());
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
    const [latencyHistory, setLatencyHistory] = useState<Array<{ timestamp: string; value: number }>>([]);

    const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 4000);
    };

    const fetchData = useCallback(async () => {
        try {
            console.log('Fetching data from API...');
            const [checks, incs, summary] = await Promise.all([
                getHealthChecks(),
                getIncidents(),
                getIncidentsSummary()
            ]);
            console.log('Received health checks:', checks);
            setHealthChecks(checks);
            setIncidents(incs.slice(0, 5));
            setIncidentSummary(summary);
            setError(null);

            // Extract latency history from checks
            const latencyCheck = checks.find(c => c.check_type === 'latency');
            if (latencyCheck?.last_run?.result_value) {
                setLatencyHistory(prev => {
                    const newEntry = {
                        timestamp: latencyCheck.last_run!.started_at,
                        value: latencyCheck.last_run!.result_value!
                    };
                    const updated = [...prev, newEntry].slice(-20);
                    return updated;
                });
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error';
            console.error('Failed to fetch data:', errorMessage, err);
            setError(`Failed to connect to backend: ${errorMessage}`);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const handleRunCheck = async (checkId: number) => {
        setRunningChecks(prev => new Set(prev).add(checkId));
        try {
            const result = await runHealthCheck(checkId);
            showToast(
                result.passed ? `${result.check_name} passed` : `${result.check_name} failed`,
                result.passed ? 'success' : 'error'
            );
            fetchData();
        } catch (error) {
            showToast('Failed to run check', 'error');
        } finally {
            setRunningChecks(prev => {
                const next = new Set(prev);
                next.delete(checkId);
                return next;
            });
        }
    };

    const handleRunAllChecks = async () => {
        try {
            const result = await runAllHealthChecks();
            showToast(`Completed ${result.total} checks: ${result.passed} passed, ${result.failed} failed`,
                result.failed > 0 ? 'error' : 'success');
            fetchData();
        } catch (error) {
            showToast('Failed to run checks', 'error');
        }
    };

    const handleInjectFailure = async (type: string, severity: string) => {
        try {
            await injectFailure(type, severity);
            showToast(`Injected ${severity} ${type} failure`, 'info');
        } catch (error) {
            showToast('Failed to inject failure', 'error');
        }
    };

    const handleClearFailures = async () => {
        try {
            await clearFailures();
            showToast('Cleared all failures', 'success');
        } catch (error) {
            showToast('Failed to clear failures', 'error');
        }
    };

    const getStatusCounts = () => {
        const counts = { passed: 0, failed: 0, pending: 0 };
        healthChecks.forEach(check => {
            if (!check.last_run) counts.pending++;
            else if (check.last_run.status === 'passed') counts.passed++;
            else counts.failed++;
        });
        return counts;
    };

    const statusCounts = getStatusCounts();

    // Chart data
    const latencyChartData: Data[] = latencyHistory.length > 0 ? [{
        x: latencyHistory.map(h => new Date(h.timestamp)),
        y: latencyHistory.map(h => h.value),
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Latency',
        line: { color: '#FF5A00', width: 2, shape: 'spline' },
        marker: { color: '#FF5A00', size: 6 },
        fill: 'tozeroy',
        fillcolor: 'rgba(255, 90, 0, 0.1)',
    }] : [];

    const checkTypeChartData: Data[] = [{
        labels: healthChecks.map(c => c.name.split(' ').slice(0, 2).join(' ')),
        values: healthChecks.map(c => c.last_run?.result_value || 0),
        type: 'pie',
        hole: 0.6,
        marker: {
            colors: ['#FF5A00', '#00AEEF', '#10B981', '#F59E0B'],
        },
        textinfo: 'label',
        textposition: 'outside',
        textfont: { color: '#94A3B8', size: 10 },
    }];

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
                <div className="spinner" />
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '400px', gap: '16px' }}>
                <div style={{ color: '#EF4444', fontSize: '18px' }}>⚠️ Connection Error</div>
                <div style={{ color: '#94A3B8', fontSize: '14px', maxWidth: '400px', textAlign: 'center' }}>{error}</div>
                <button className="btn btn-primary" onClick={fetchData}>Retry Connection</button>
                <div style={{ color: '#64748B', fontSize: '12px', marginTop: '8px' }}>
                    Make sure the backend is running at http://localhost:8000
                </div>
            </div>
        );
    }

    return (
        <div style={{ padding: '24px', maxWidth: '1600px', margin: '0 auto' }}>
            {/* Header */}
            <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ fontSize: '24px', marginBottom: '4px' }}>AI Pipeline Dashboard</h1>
                    <p style={{ color: '#64748B', fontSize: '14px' }}>
                        Real-time monitoring of ML/LLM inference pipelines
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                    <button className="btn btn-secondary" onClick={handleClearFailures}>
                        Clear Failures
                    </button>
                    <button className="btn btn-primary" onClick={handleRunAllChecks}>
                        Run All Checks
                    </button>
                </div>
            </div>

            {/* Status Summary Cards */}
            <div className="grid grid-cols-4" style={{ marginBottom: '24px' }}>
                <div className="card" style={{ padding: '20px', background: 'rgba(16, 185, 129, 0.1)', borderColor: 'rgba(16, 185, 129, 0.2)' }}>
                    <div style={{ fontSize: '12px', color: '#10B981', marginBottom: '4px' }}>Passing</div>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: '#34D399' }}>{statusCounts.passed}</div>
                </div>
                <div className="card" style={{ padding: '20px', background: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.2)' }}>
                    <div style={{ fontSize: '12px', color: '#EF4444', marginBottom: '4px' }}>Failing</div>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: '#F87171' }}>{statusCounts.failed}</div>
                </div>
                <div className="card" style={{ padding: '20px', background: 'rgba(245, 158, 11, 0.1)', borderColor: 'rgba(245, 158, 11, 0.2)' }}>
                    <div style={{ fontSize: '12px', color: '#F59E0B', marginBottom: '4px' }}>Open Incidents</div>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: '#FBBF24' }}>{incidentSummary?.by_status?.open || 0}</div>
                </div>
                <div className="card" style={{ padding: '20px', background: 'rgba(59, 130, 246, 0.1)', borderColor: 'rgba(59, 130, 246, 0.2)' }}>
                    <div style={{ fontSize: '12px', color: '#3B82F6', marginBottom: '4px' }}>Total Checks</div>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: '#60A5FA' }}>{healthChecks.length}</div>
                </div>
            </div>

            {/* Main Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 1fr', gap: '24px' }}>
                {/* Left: Health Checks */}
                <div>
                    <h3 style={{ marginBottom: '16px', fontSize: '16px' }}>Health Checks</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {healthChecks.map(check => (
                            <HealthCheckCard
                                key={check.id}
                                check={check}
                                onRun={handleRunCheck}
                                isRunning={runningChecks.has(check.id)}
                            />
                        ))}
                    </div>
                </div>

                {/* Center: Charts */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    <div className="card">
                        <h4 style={{ marginBottom: '12px', fontSize: '14px' }}>Inference Latency Trend</h4>
                        {latencyHistory.length > 0 ? (
                            <PlotlyChart data={latencyChartData} height={250} showLegend={false} />
                        ) : (
                            <div style={{ height: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748B' }}>
                                Run latency checks to see trend data
                            </div>
                        )}
                    </div>

                    <div className="card">
                        <h4 style={{ marginBottom: '12px', fontSize: '14px' }}>Check Distribution</h4>
                        <PlotlyChart data={checkTypeChartData} height={250} showLegend={false} />
                    </div>

                    {/* Demo Controls */}
                    <div className="card" style={{ background: 'rgba(255, 90, 0, 0.05)', borderColor: 'rgba(255, 90, 0, 0.2)' }}>
                        <h4 style={{ marginBottom: '16px', fontSize: '14px', color: '#FF5A00' }}>Demo Controls</h4>
                        <p style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '12px' }}>
                            Inject failures to demonstrate monitoring and remediation capabilities
                        </p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            <button className="btn btn-secondary btn-sm" onClick={() => handleInjectFailure('latency', 'high')}>
                                Inject Latency
                            </button>
                            <button className="btn btn-secondary btn-sm" onClick={() => handleInjectFailure('correctness', 'medium')}>
                                Inject Correctness
                            </button>
                            <button className="btn btn-secondary btn-sm" onClick={() => handleInjectFailure('drift', 'medium')}>
                                Inject Drift
                            </button>
                            <button className="btn btn-secondary btn-sm" onClick={() => handleInjectFailure('error', 'high')}>
                                Inject Errors
                            </button>
                        </div>
                    </div>
                </div>

                {/* Right: Incidents */}
                <div>
                    <h3 style={{ marginBottom: '16px', fontSize: '16px' }}>Recent Incidents</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {incidents.length === 0 ? (
                            <div className="card" style={{ padding: '24px', textAlign: 'center' }}>
                                <div style={{ color: '#10B981', fontSize: '24px', marginBottom: '8px' }}>✓</div>
                                <div style={{ color: '#64748B', fontSize: '14px' }}>No active incidents</div>
                            </div>
                        ) : (
                            incidents.map(incident => (
                                <div key={incident.id} className="card" style={{ padding: '16px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                                        <span className={`badge badge-${incident.severity === 'high' || incident.severity === 'critical' ? 'error' : incident.severity === 'medium' ? 'warning' : 'info'}`}>
                                            {incident.severity}
                                        </span>
                                        <span className={`badge badge-${incident.status === 'resolved' ? 'success' : 'warning'}`}>
                                            {incident.status}
                                        </span>
                                    </div>
                                    <h5 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '4px', color: '#F1F5F9' }}>
                                        {incident.title}
                                    </h5>
                                    <p style={{ fontSize: '11px', color: '#64748B' }}>
                                        {new Date(incident.triggered_at).toLocaleString()}
                                    </p>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            {/* Toast notification */}
            {toast && (
                <div className={`toast`} style={{
                    borderLeft: `4px solid ${toast.type === 'success' ? '#10B981' : toast.type === 'error' ? '#EF4444' : '#3B82F6'}`
                }}>
                    {toast.message}
                </div>
            )}
        </div>
    );
};

export default Dashboard;
