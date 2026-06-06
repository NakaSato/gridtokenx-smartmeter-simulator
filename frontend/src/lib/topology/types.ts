import type cytoscapeType from 'cytoscape';

export type VoltageState = 'under' | 'ok' | 'over';
export type TopologyNodeKind = 'transformer' | 'feeder' | 'service';

export interface SelectedNodeData {
    id: string;
    label: string;
    kind: TopologyNodeKind;
    busName?: string;
    vnKv?: number;
    voltagePu?: number;
    voltageV?: number;
    loadKw?: number;
    meterCount?: number;
    meterIds?: string[];
    solarCapacityKw?: number;
    hasSolar?: boolean;
    generationKw?: number;
    consumptionKw?: number;
    depth?: number;
    parent?: string | null;
    children?: string[];
}

export interface TopologyGraphNode extends SelectedNodeData {
    color: string;
    val: number;
    voltageState?: VoltageState;
}

export interface TopologyGraphLink {
    id: string;
    source: string;
    target: string;
    label: string;
    lineName?: string;
    utilization?: number;
    flowKw?: number;
}

export type TopologyGraphData = {
    nodes: TopologyGraphNode[];
    links: TopologyGraphLink[];
};

export type CytoscapeImport = { default?: typeof cytoscapeType } & typeof cytoscapeType;
export type CytoscapeFcoseImport = { default?: cytoscapeType.Ext } & cytoscapeType.Ext;

export interface FcoseFixedNodeConstraint {
    nodeId: string;
    position: { x: number; y: number };
}

export interface FcoseAlignmentConstraint {
    vertical?: string[][];
    horizontal?: string[][];
}

export type FcoseRelativePlacementConstraint =
    | { left: string; right: string; gap?: number }
    | { top: string; bottom: string; gap?: number };

export interface FcoseLayoutOptions {
    name: 'fcose';
    quality: 'draft' | 'default' | 'proof';
    randomize: boolean;
    animate: boolean;
    animationDuration: number;
    fit: boolean;
    padding: number;
    nodeDimensionsIncludeLabels: boolean;
    uniformNodeDimensions: boolean;
    nodeSeparation: number;
    idealEdgeLength: number;
    edgeElasticity: number;
    nodeRepulsion: number;
    gravity: number;
    numIter: number;
    tile: boolean;
    fixedNodeConstraint?: FcoseFixedNodeConstraint[];
    alignmentConstraint?: FcoseAlignmentConstraint;
    relativePlacementConstraint?: FcoseRelativePlacementConstraint[];
}

export interface GridStats {
    totalGenerationKw: number;
    totalConsumptionKw: number;
    avgVoltage: number;
    totalLossesKw: number;
    congestedLines: number;
}

export interface TopologyCounts {
    buses: number;
    lines: number;
    meters: number;
}

export interface GraphTooltipState {
    text: string;
    x: number;
    y: number;
}
