import React from 'react';
import { HealthCheck } from '../api';

interface HealthCheckCardProps {
    check: HealthCheck;
    onRun: (checkId: number) => void;
    isRunning?: boolean;
}

const HealthCheckCard: React.FC<HealthCheckCardProps> = ({ check, onRun, isRunning }) => {
    const getStatusColor = () => {
        if (!check.last_run) return '#64748B';
        switch (check.last_run.status) {
            case 'passed': return '#10B981';
            case 'failed': return '#EF4444';
            case 'running': return '#F59E0B';
            default: return '#64748B';
        }
    };

    const getStatusLabel = () => {
        if (!check.last_run) return 'Not Run';
        switch (check.last_run.status) {
            case 'passed': return 'Passed';
            case 'failed': return 'Failed';
            case 'running': return 'Running';
            default: return check.last_run.status;
        }
    };

    const getCheckTypeIcon = (type: string) => {
        switch (type) {
            case 'latency': return '⚡';
            case 'correctness': return '✓';
            case 'drift': return '📊';
            case 'resource': return '🖥️';
            default: return '•';
        }
    };

    const formatValue = () => {
        if (!check.last_run?.result_value) return 'N/A';

        switch (check.check_type) {
            case 'latency':
                return `${check.last_run.result_value.toFixed(1)}ms`;
            case 'correctness':
                return `${(check.last_run.result_value * 100).toFixed(1)}%`;
            case 'drift':
                return `KS: ${check.last_run.result_value.toFixed(3)}`;
            case 'resource':
                return `${check.last_run.result_value.toFixed(1)}%`;
            default:
                return check.last_run.result_value.toFixed(2);
        }
    };

    const formatTime = (isoString: string) => {
        const date = new Date(isoString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div className="card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '20px' }}>{getCheckTypeIcon(check.check_type)}</span>
                    <div>
                        <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#F1F5F9', margin: 0 }}>
                            {check.name}
                        </h4>
                        <span style={{ fontSize: '12px', color: '#64748B', textTransform: 'capitalize' }}>
                            {check.check_type} Check
                        </span>
                    </div>
                </div>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '4px 10px',
                    borderRadius: '12px',
                    background: `${getStatusColor()}20`,
                }}>
                    <div style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        background: getStatusColor(),
                    }} />
                    <span style={{ fontSize: '12px', color: getStatusColor(), fontWeight: 500 }}>
                        {getStatusLabel()}
                    </span>
                </div>
            </div>

            {check.description && (
                <p style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '12px', lineHeight: 1.4 }}>
                    {check.description}
                </p>
            )}

            <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px',
                padding: '12px',
                background: 'rgba(0, 0, 0, 0.2)',
                borderRadius: '8px',
                marginBottom: '12px'
            }}>
                <div>
                    <div style={{ fontSize: '11px', color: '#64748B', marginBottom: '4px' }}>Last Value</div>
                    <div style={{ fontSize: '16px', fontWeight: 600, color: '#F1F5F9' }}>
                        {formatValue()}
                    </div>
                </div>
                <div>
                    <div style={{ fontSize: '11px', color: '#64748B', marginBottom: '4px' }}>Threshold</div>
                    <div style={{ fontSize: '16px', fontWeight: 600, color: '#F1F5F9' }}>
                        {check.threshold_value ?? 'N/A'}
                        {check.check_type === 'latency' && 'ms'}
                        {check.check_type === 'resource' && '%'}
                    </div>
                </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '11px', color: '#64748B' }}>
                    {check.last_run ? `Last run: ${formatTime(check.last_run.started_at)}` : 'Never run'}
                </span>
                <button
                    className="btn btn-primary btn-sm"
                    onClick={() => onRun(check.id)}
                    disabled={isRunning}
                    style={{ opacity: isRunning ? 0.6 : 1 }}
                >
                    {isRunning ? 'Running...' : 'Run Check'}
                </button>
            </div>
        </div>
    );
};

export default HealthCheckCard;
