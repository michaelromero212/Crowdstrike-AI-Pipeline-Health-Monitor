import React, { useState, useEffect } from 'react';
import PlotlyChart from '../components/PlotlyChart';
import {
    getInfrastructureSummary,
    getInstanceMetrics,
    getRightsizingOpportunities,
    getCostSummary,
    InfrastructureSummary,
    RightsizingOpportunity,
    CostSummary
} from '../api';
import { Data } from 'plotly.js';

const Infrastructure: React.FC = () => {
    const [summary, setSummary] = useState<InfrastructureSummary | null>(null);
    const [opportunities, setOpportunities] = useState<RightsizingOpportunity[]>([]);
    const [costSummary, setCostSummary] = useState<CostSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedProvider, setSelectedProvider] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [summaryData, opps, costs] = await Promise.all([
                    getInfrastructureSummary(),
                    getRightsizingOpportunities(),
                    getCostSummary()
                ]);
                setSummary(summaryData);
                setOpportunities(opps);
                setCostSummary(costs);
            } catch (error) {
                console.error('Failed to fetch infrastructure data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
                <div className="spinner" />
            </div>
        );
    }

    const providers = summary?.by_provider ? Object.keys(summary.by_provider) : [];

    const utilizationChartData: Data[] = [
        {
            x: providers,
            y: providers.map(p => summary?.by_provider[p]?.avg_cpu_util || 0),
            name: 'Avg CPU %',
            type: 'bar',
            marker: { color: '#00AEEF' },
        },
        {
            x: providers,
            y: providers.map(p => summary?.by_provider[p]?.avg_memory_util || 0),
            name: 'Avg Memory %',
            type: 'bar',
            marker: { color: '#FF5A00' },
        },
    ];

    const costChartData: Data[] = costSummary ? [
        {
            labels: Object.keys(costSummary.by_provider),
            values: Object.values(costSummary.by_provider).map(p => p.monthly_cost),
            type: 'pie',
            hole: 0.5,
            marker: {
                colors: ['#FF5A00', '#00AEEF', '#10B981'],
            },
            textinfo: 'label+percent',
            textfont: { color: '#F1F5F9', size: 11 },
        },
    ] : [];

    const savingsChartData: Data[] = [{
        x: opportunities.slice(0, 10).map(o => o.instance_id.slice(-8)),
        y: opportunities.slice(0, 10).map(o => o.estimated_monthly_savings),
        type: 'bar',
        marker: {
            color: opportunities.slice(0, 10).map(o =>
                o.confidence === 'high' ? '#10B981' : '#F59E0B'
            ),
        },
        text: opportunities.slice(0, 10).map(o => `$${o.estimated_monthly_savings}`),
        textposition: 'outside',
        textfont: { color: '#94A3B8', size: 10 },
    }];

    return (
        <div style={{ padding: '24px', maxWidth: '1600px', margin: '0 auto' }}>
            {/* Header */}
            <div style={{ marginBottom: '24px' }}>
                <h1 style={{ fontSize: '24px', marginBottom: '4px' }}>Infrastructure Overview</h1>
                <p style={{ color: '#64748B', fontSize: '14px' }}>
                    Multi-cloud resource utilization and optimization opportunities
                </p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-4" style={{ marginBottom: '24px' }}>
                <div className="card" style={{ padding: '20px' }}>
                    <div style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '4px' }}>Total Instances</div>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: '#F1F5F9' }}>{summary?.total_instances || 0}</div>
                </div>
                <div className="card" style={{ padding: '20px', background: 'rgba(239, 68, 68, 0.1)' }}>
                    <div style={{ fontSize: '12px', color: '#F87171', marginBottom: '4px' }}>Idle Instances</div>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: '#EF4444' }}>{summary?.idle_count || 0}</div>
                </div>
                <div className="card" style={{ padding: '20px', background: 'rgba(245, 158, 11, 0.1)' }}>
                    <div style={{ fontSize: '12px', color: '#FBBF24', marginBottom: '4px' }}>Overutilized</div>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: '#F59E0B' }}>{summary?.overutilized_count || 0}</div>
                </div>
                <div className="card" style={{ padding: '20px', background: 'rgba(16, 185, 129, 0.1)' }}>
                    <div style={{ fontSize: '12px', color: '#34D399', marginBottom: '4px' }}>Potential Savings</div>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: '#10B981' }}>
                        ${costSummary?.potential_monthly_savings?.toFixed(0) || 0}/mo
                    </div>
                </div>
            </div>

            {/* Main Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
                {/* Left Column */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    {/* Utilization by Provider */}
                    <div className="card">
                        <h4 style={{ marginBottom: '16px', fontSize: '14px' }}>Average Utilization by Provider</h4>
                        <PlotlyChart data={utilizationChartData} height={280} />
                    </div>

                    {/* Rightsizing Opportunities */}
                    <div className="card">
                        <h4 style={{ marginBottom: '16px', fontSize: '14px' }}>Top Rightsizing Opportunities</h4>
                        <PlotlyChart
                            data={savingsChartData}
                            height={250}
                            title="Estimated Monthly Savings ($)"
                            showLegend={false}
                        />
                    </div>

                    {/* Opportunities Table */}
                    <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Instance ID</th>
                                    <th>Provider</th>
                                    <th>Current Type</th>
                                    <th>Recommended</th>
                                    <th>CPU Util</th>
                                    <th>Savings/mo</th>
                                    <th>Confidence</th>
                                </tr>
                            </thead>
                            <tbody>
                                {opportunities.slice(0, 8).map(opp => (
                                    <tr key={opp.instance_id}>
                                        <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{opp.instance_id}</td>
                                        <td><span className="badge badge-info">{opp.provider}</span></td>
                                        <td style={{ fontSize: '13px' }}>{opp.current_type}</td>
                                        <td style={{ fontSize: '13px', color: '#10B981' }}>{opp.recommended_type}</td>
                                        <td style={{ fontSize: '13px' }}>{opp.current_cpu_util.toFixed(1)}%</td>
                                        <td style={{ fontSize: '13px', fontWeight: 600, color: '#10B981' }}>
                                            ${opp.estimated_monthly_savings.toFixed(2)}
                                        </td>
                                        <td>
                                            <span className={`badge badge-${opp.confidence === 'high' ? 'success' : 'warning'}`}>
                                                {opp.confidence}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Right Column */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    {/* Cost Distribution */}
                    <div className="card">
                        <h4 style={{ marginBottom: '16px', fontSize: '14px' }}>Monthly Cost Distribution</h4>
                        {costSummary && <PlotlyChart data={costChartData} height={280} showLegend={false} />}
                        <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(0, 0, 0, 0.2)', borderRadius: '8px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                <span style={{ fontSize: '12px', color: '#94A3B8' }}>Est. Monthly Cost</span>
                                <span style={{ fontSize: '14px', fontWeight: 600, color: '#F1F5F9' }}>
                                    ${costSummary?.estimated_monthly_cost?.toFixed(2) || 0}
                                </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span style={{ fontSize: '12px', color: '#94A3B8' }}>Est. Hourly Cost</span>
                                <span style={{ fontSize: '14px', fontWeight: 600, color: '#F1F5F9' }}>
                                    ${costSummary?.estimated_hourly_cost?.toFixed(2) || 0}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Provider Breakdown */}
                    <div className="card">
                        <h4 style={{ marginBottom: '16px', fontSize: '14px' }}>Provider Summary</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {providers.map(provider => (
                                <div
                                    key={provider}
                                    style={{
                                        padding: '12px',
                                        background: 'rgba(0, 0, 0, 0.2)',
                                        borderRadius: '8px',
                                        cursor: 'pointer',
                                        border: selectedProvider === provider ? '1px solid #FF5A00' : '1px solid transparent',
                                    }}
                                    onClick={() => setSelectedProvider(selectedProvider === provider ? null : provider)}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                        <span style={{ fontWeight: 600, textTransform: 'uppercase', color: '#F1F5F9' }}>{provider}</span>
                                        <span style={{ fontSize: '12px', color: '#94A3B8' }}>
                                            {summary?.by_provider[provider]?.instance_count || 0} instances
                                        </span>
                                    </div>
                                    <div style={{ display: 'flex', gap: '16px' }}>
                                        <div>
                                            <div style={{ fontSize: '10px', color: '#64748B' }}>CPU</div>
                                            <div style={{ fontSize: '14px', color: '#00AEEF' }}>
                                                {summary?.by_provider[provider]?.avg_cpu_util?.toFixed(1) || 0}%
                                            </div>
                                        </div>
                                        <div>
                                            <div style={{ fontSize: '10px', color: '#64748B' }}>Memory</div>
                                            <div style={{ fontSize: '14px', color: '#FF5A00' }}>
                                                {summary?.by_provider[provider]?.avg_memory_util?.toFixed(1) || 0}%
                                            </div>
                                        </div>
                                        <div>
                                            <div style={{ fontSize: '10px', color: '#64748B' }}>Monthly</div>
                                            <div style={{ fontSize: '14px', color: '#F1F5F9' }}>
                                                ${costSummary?.by_provider[provider]?.monthly_cost?.toFixed(0) || 0}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="card">
                        <h4 style={{ marginBottom: '16px', fontSize: '14px' }}>Quick Actions</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <button className="btn btn-primary" style={{ width: '100%' }}>
                                Generate Optimization Report
                            </button>
                            <button className="btn btn-secondary" style={{ width: '100%' }}>
                                Export CSV Report
                            </button>
                            <button className="btn btn-secondary" style={{ width: '100%' }}>
                                Download Ansible Playbook
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Infrastructure;
