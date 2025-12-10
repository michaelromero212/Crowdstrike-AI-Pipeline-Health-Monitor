import React from 'react';
import Plot from 'react-plotly.js';
import { Data, Layout } from 'plotly.js';

interface PlotlyChartProps {
    data: Data[];
    title?: string;
    height?: number;
    showLegend?: boolean;
}

const PlotlyChart: React.FC<PlotlyChartProps> = ({
    data,
    title,
    height = 300,
    showLegend = true
}) => {
    const layout: Partial<Layout> = {
        title: title ? {
            text: title,
            font: { color: '#F1F5F9', size: 14 },
            x: 0,
            xanchor: 'left',
        } : undefined,
        height,
        margin: { l: 50, r: 30, t: title ? 50 : 20, b: 40 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#94A3B8', size: 11 },
        showlegend: showLegend,
        legend: {
            orientation: 'h',
            y: -0.2,
            font: { color: '#94A3B8', size: 10 },
        },
        xaxis: {
            gridcolor: 'rgba(255, 255, 255, 0.05)',
            linecolor: 'rgba(255, 255, 255, 0.1)',
            tickfont: { color: '#64748B' },
        },
        yaxis: {
            gridcolor: 'rgba(255, 255, 255, 0.05)',
            linecolor: 'rgba(255, 255, 255, 0.1)',
            tickfont: { color: '#64748B' },
        },
    };

    const config = {
        displayModeBar: false,
        responsive: true,
    };

    return (
        <Plot
            data={data}
            layout={layout}
            config={config}
            style={{ width: '100%', height: '100%' }}
        />
    );
};

// Pre-configured chart variants
export const LatencyChart: React.FC<{ history: Array<{ timestamp: string; value: number }> }> = ({ history }) => {
    const data: Data[] = [{
        x: history.map(h => new Date(h.timestamp)),
        y: history.map(h => h.value),
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Latency',
        line: { color: '#FF5A00', width: 2 },
        marker: { color: '#FF5A00', size: 6 },
        fill: 'tozeroy',
        fillcolor: 'rgba(255, 90, 0, 0.1)',
    }];

    return <PlotlyChart data={data} title="Inference Latency (ms)" />;
};

export const UtilizationChart: React.FC<{
    cpuData: number[];
    memoryData: number[];
    labels: string[]
}> = ({ cpuData, memoryData, labels }) => {
    const data: Data[] = [
        {
            x: labels,
            y: cpuData,
            type: 'bar',
            name: 'CPU %',
            marker: { color: '#00AEEF' },
        },
        {
            x: labels,
            y: memoryData,
            type: 'bar',
            name: 'Memory %',
            marker: { color: '#FF5A00' },
        },
    ];

    return <PlotlyChart data={data} title="Resource Utilization" />;
};

export const DriftChart: React.FC<{
    baseline: number[];
    current: number[];
}> = ({ baseline, current }) => {
    const data: Data[] = [
        {
            y: baseline,
            type: 'violin',
            name: 'Baseline',
            side: 'negative',
            line: { color: '#00AEEF' },
            fillcolor: 'rgba(0, 174, 239, 0.3)',
        },
        {
            y: current,
            type: 'violin',
            name: 'Current',
            side: 'positive',
            line: { color: '#FF5A00' },
            fillcolor: 'rgba(255, 90, 0, 0.3)',
        },
    ];

    return <PlotlyChart data={data} title="Distribution Comparison" height={250} />;
};

export const CostChart: React.FC<{
    providers: string[];
    costs: number[];
    savings: number[];
}> = ({ providers, costs, savings }) => {
    const data: Data[] = [
        {
            x: providers,
            y: costs,
            type: 'bar',
            name: 'Current Cost',
            marker: { color: '#64748B' },
        },
        {
            x: providers,
            y: savings,
            type: 'bar',
            name: 'Potential Savings',
            marker: { color: '#10B981' },
        },
    ];

    return <PlotlyChart data={data} title="Monthly Cost Analysis ($)" />;
};

export const IncidentTimelineChart: React.FC<{
    incidents: Array<{ date: string; count: number; severity: string }>;
}> = ({ incidents }) => {
    const severityColors: Record<string, string> = {
        critical: '#EF4444',
        high: '#F59E0B',
        medium: '#00AEEF',
        low: '#64748B',
    };

    const bySeverity = incidents.reduce((acc, inc) => {
        if (!acc[inc.severity]) acc[inc.severity] = [];
        acc[inc.severity].push(inc);
        return acc;
    }, {} as Record<string, typeof incidents>);

    const data: Data[] = Object.entries(bySeverity).map(([severity, items]) => ({
        x: items.map(i => i.date),
        y: items.map(i => i.count),
        type: 'scatter' as const,
        mode: 'markers' as const,
        name: severity.charAt(0).toUpperCase() + severity.slice(1),
        marker: {
            color: severityColors[severity] || '#64748B',
            size: 10,
        },
    }));

    return <PlotlyChart data={data} title="Incident Timeline" height={200} />;
};

export default PlotlyChart;
