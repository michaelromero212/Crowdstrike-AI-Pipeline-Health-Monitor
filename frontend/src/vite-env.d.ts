/// <reference types="vite/client" />

declare module 'react-plotly.js' {
    import { Component } from 'react';
    import { Data, Layout, Config, PlotlyHTMLElement } from 'plotly.js';

    interface PlotParams {
        data: Data[];
        layout?: Partial<Layout>;
        config?: Partial<Config>;
        style?: React.CSSProperties;
        className?: string;
        useResizeHandler?: boolean;
        onInitialized?: (figure: Readonly<{ data: Data[]; layout: Partial<Layout> }>, graphDiv: PlotlyHTMLElement) => void;
        onUpdate?: (figure: Readonly<{ data: Data[]; layout: Partial<Layout> }>, graphDiv: PlotlyHTMLElement) => void;
        onPurge?: (graphDiv: PlotlyHTMLElement) => void;
        onError?: (err: Error) => void;
    }

    export default class Plot extends Component<PlotParams> { }
}
