import React, { useState, useEffect } from 'react';
import {
    getIncidents,
    getIncidentsSummary,
    remediate,
    resolveIncident,
    Incident
} from '../api';

const Incidents: React.FC = () => {
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [summary, setSummary] = useState<{ total: number; by_status: Record<string, number>; by_severity: Record<string, number> } | null>(null);
    const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
    const [loading, setLoading] = useState(true);
    const [filterStatus, setFilterStatus] = useState<string>('all');
    const [toast, setToast] = useState<string | null>(null);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, [filterStatus]);

    const fetchData = async () => {
        try {
            const [incs, sum] = await Promise.all([
                getIncidents(filterStatus === 'all' ? undefined : filterStatus),
                getIncidentsSummary()
            ]);
            setIncidents(incs);
            setSummary(sum);
        } catch (error) {
            console.error('Failed to fetch incidents:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRemediate = async (incidentId: number, strategy: string, dryRun: boolean = false) => {
        try {
            const result = await remediate(incidentId, strategy, dryRun);
            setToast(result.success ? 'Remediation successful' : 'Remediation failed');
            setTimeout(() => setToast(null), 3000);
            fetchData();
            setSelectedIncident(null);
        } catch (error) {
            setToast('Error executing remediation');
            setTimeout(() => setToast(null), 3000);
        }
    };

    const handleResolve = async (incidentId: number) => {
        try {
            await resolveIncident(incidentId, 'Manually resolved');
            setToast('Incident resolved');
            setTimeout(() => setToast(null), 3000);
            fetchData();
            setSelectedIncident(null);
        } catch (error) {
            setToast('Failed to resolve incident');
            setTimeout(() => setToast(null), 3000);
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'critical': return '#EF4444';
            case 'high': return '#F59E0B';
            case 'medium': return '#3B82F6';
            default: return '#64748B';
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'resolved': return '#10B981';
            case 'remediating': return '#F59E0B';
            case 'escalated': return '#EF4444';
            default: return '#3B82F6';
        }
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
                <div className="spinner" />
            </div>
        );
    }

    return (
        <div style={{ padding: '24px', maxWidth: '1600px', margin: '0 auto' }}>
            {/* Header */}
            <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ fontSize: '24px', marginBottom: '4px' }}>Incident Management</h1>
                    <p style={{ color: '#64748B', fontSize: '14px' }}>
                        Track and remediate pipeline incidents
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                    {['all', 'open', 'remediating', 'resolved', 'escalated'].map(status => (
                        <button
                            key={status}
                            className={`btn ${filterStatus === status ? 'btn-primary' : 'btn-secondary'} btn-sm`}
                            onClick={() => setFilterStatus(status)}
                        >
                            {status.charAt(0).toUpperCase() + status.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-4" style={{ marginBottom: '24px' }}>
                <div className="card" style={{ padding: '20px' }}>
                    <div style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '4px' }}>Total Incidents</div>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: '#F1F5F9' }}>{summary?.total || 0}</div>
                </div>
                <div className="card" style={{ padding: '20px', background: 'rgba(59, 130, 246, 0.1)' }}>
                    <div style={{ fontSize: '12px', color: '#60A5FA', marginBottom: '4px' }}>Open</div>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: '#3B82F6' }}>
                        {summary?.by_status?.open || 0}
                    </div>
                </div>
                <div className="card" style={{ padding: '20px', background: 'rgba(245, 158, 11, 0.1)' }}>
                    <div style={{ fontSize: '12px', color: '#FBBF24', marginBottom: '4px' }}>Remediating</div>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: '#F59E0B' }}>
                        {summary?.by_status?.remediating || 0}
                    </div>
                </div>
                <div className="card" style={{ padding: '20px', background: 'rgba(16, 185, 129, 0.1)' }}>
                    <div style={{ fontSize: '12px', color: '#34D399', marginBottom: '4px' }}>Resolved</div>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: '#10B981' }}>
                        {summary?.by_status?.resolved || 0}
                    </div>
                </div>
            </div>

            {/* Main Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: selectedIncident ? '1fr 400px' : '1fr', gap: '24px' }}>
                {/* Incidents List */}
                <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
                    <table className="table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Title</th>
                                <th>Severity</th>
                                <th>Status</th>
                                <th>Triggered</th>
                                <th>Attempts</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {incidents.length === 0 ? (
                                <tr>
                                    <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: '#64748B' }}>
                                        No incidents found
                                    </td>
                                </tr>
                            ) : (
                                incidents.map(incident => (
                                    <tr
                                        key={incident.id}
                                        style={{
                                            cursor: 'pointer',
                                            background: selectedIncident?.id === incident.id ? 'rgba(255, 90, 0, 0.1)' : 'transparent'
                                        }}
                                        onClick={() => setSelectedIncident(incident)}
                                    >
                                        <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>#{incident.id}</td>
                                        <td style={{ maxWidth: '300px' }}>
                                            <div style={{ fontWeight: 500, color: '#F1F5F9', fontSize: '13px' }}>{incident.title}</div>
                                            {incident.description && (
                                                <div style={{ fontSize: '11px', color: '#64748B', marginTop: '2px' }}>
                                                    {incident.description.substring(0, 60)}...
                                                </div>
                                            )}
                                        </td>
                                        <td>
                                            <span style={{
                                                padding: '4px 8px',
                                                borderRadius: '12px',
                                                fontSize: '11px',
                                                fontWeight: 500,
                                                background: `${getSeverityColor(incident.severity)}20`,
                                                color: getSeverityColor(incident.severity),
                                            }}>
                                                {incident.severity}
                                            </span>
                                        </td>
                                        <td>
                                            <span style={{
                                                padding: '4px 8px',
                                                borderRadius: '12px',
                                                fontSize: '11px',
                                                fontWeight: 500,
                                                background: `${getStatusColor(incident.status)}20`,
                                                color: getStatusColor(incident.status),
                                            }}>
                                                {incident.status}
                                            </span>
                                        </td>
                                        <td style={{ fontSize: '12px', color: '#94A3B8' }}>
                                            {new Date(incident.triggered_at).toLocaleString()}
                                        </td>
                                        <td style={{ fontSize: '12px' }}>
                                            {incident.remediation_attempts?.length || 0}
                                        </td>
                                        <td onClick={e => e.stopPropagation()}>
                                            {incident.status !== 'resolved' && (
                                                <button
                                                    className="btn btn-primary btn-sm"
                                                    onClick={() => setSelectedIncident(incident)}
                                                >
                                                    Remediate
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Incident Detail Panel */}
                {selectedIncident && (
                    <div className="card" style={{ alignSelf: 'start' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                            <h3 style={{ fontSize: '16px' }}>Incident Details</h3>
                            <button
                                onClick={() => setSelectedIncident(null)}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: '#64748B',
                                    cursor: 'pointer',
                                    fontSize: '20px'
                                }}
                            >
                                ×
                            </button>
                        </div>

                        <div style={{ marginBottom: '16px' }}>
                            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>{selectedIncident.title}</h4>
                            <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                                <span className={`badge badge-${selectedIncident.severity === 'high' || selectedIncident.severity === 'critical' ? 'error' : 'warning'}`}>
                                    {selectedIncident.severity}
                                </span>
                                <span className={`badge badge-${selectedIncident.status === 'resolved' ? 'success' : 'info'}`}>
                                    {selectedIncident.status}
                                </span>
                            </div>
                            {selectedIncident.description && (
                                <p style={{ fontSize: '13px', color: '#94A3B8', lineHeight: 1.5 }}>
                                    {selectedIncident.description}
                                </p>
                            )}
                        </div>

                        <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                            <div style={{ fontSize: '11px', color: '#64748B', marginBottom: '4px' }}>Triggered</div>
                            <div style={{ fontSize: '13px', color: '#F1F5F9' }}>
                                {new Date(selectedIncident.triggered_at).toLocaleString()}
                            </div>
                            {selectedIncident.resolved_at && (
                                <>
                                    <div style={{ fontSize: '11px', color: '#64748B', marginBottom: '4px', marginTop: '8px' }}>Resolved</div>
                                    <div style={{ fontSize: '13px', color: '#10B981' }}>
                                        {new Date(selectedIncident.resolved_at).toLocaleString()}
                                    </div>
                                </>
                            )}
                        </div>

                        {/* Remediation Attempts */}
                        {selectedIncident.remediation_attempts && selectedIncident.remediation_attempts.length > 0 && (
                            <div style={{ marginBottom: '16px' }}>
                                <h5 style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '8px' }}>Remediation History</h5>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    {selectedIncident.remediation_attempts.map((attempt, idx) => (
                                        <div key={idx} style={{
                                            padding: '8px 12px',
                                            background: 'rgba(0,0,0,0.2)',
                                            borderRadius: '6px',
                                            borderLeft: `3px solid ${attempt.success ? '#10B981' : '#EF4444'}`
                                        }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                <span style={{ fontSize: '12px', fontWeight: 500, color: '#F1F5F9' }}>{attempt.strategy}</span>
                                                <span className={`badge badge-${attempt.success ? 'success' : 'error'}`} style={{ fontSize: '10px' }}>
                                                    {attempt.success ? 'Success' : 'Failed'}
                                                </span>
                                            </div>
                                            <div style={{ fontSize: '10px', color: '#64748B' }}>
                                                {new Date(attempt.attempted_at).toLocaleString()}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Actions */}
                        {selectedIncident.status !== 'resolved' && (
                            <div>
                                <h5 style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '8px' }}>Remediation Actions</h5>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    <button
                                        className="btn btn-primary"
                                        onClick={() => handleRemediate(selectedIncident.id, 'restart_service')}
                                    >
                                        Restart Service
                                    </button>
                                    <button
                                        className="btn btn-secondary"
                                        onClick={() => handleRemediate(selectedIncident.id, 'clear_cache')}
                                    >
                                        Clear Cache
                                    </button>
                                    <button
                                        className="btn btn-secondary"
                                        onClick={() => handleRemediate(selectedIncident.id, 'rollback_model')}
                                    >
                                        Rollback Model
                                    </button>
                                    <button
                                        className="btn btn-secondary"
                                        onClick={() => handleRemediate(selectedIncident.id, 'restart_service', true)}
                                    >
                                        Dry Run (Preview)
                                    </button>
                                    <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)', margin: '4px 0' }} />
                                    <button
                                        className="btn btn-secondary"
                                        style={{ color: '#10B981' }}
                                        onClick={() => handleResolve(selectedIncident.id)}
                                    >
                                        Mark as Resolved
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Toast */}
            {toast && (
                <div className="toast">
                    {toast}
                </div>
            )}
        </div>
    );
};

export default Incidents;
