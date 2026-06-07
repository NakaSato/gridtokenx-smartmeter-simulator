import type { BreadthFirstLayoutOptions, EdgeDefinition, ElementDefinition, NodeDefinition, StylesheetJson } from 'cytoscape';
import type {
    FcoseLayoutOptions,
    TopologyGraphData,
    TopologyGraphLink,
    TopologyGraphNode,
    VoltageState,
} from './types';

export const emptyGraph: TopologyGraphData = { nodes: [], links: [] };

/** Convert per-interval energy (kWh) to average power (kW). Mirrors backend `_to_kw`. */
export const toKw = (energyKwh: number, intervalSeconds: number): number =>
    intervalSeconds > 0 ? (energyKwh * 3600) / intervalSeconds : 0;

export const voltageState = (pu: number): VoltageState =>
    pu < 0.95 ? 'under' : pu > 1.05 ? 'over' : 'ok';

export const getLinkColor = (link: TopologyGraphLink): string => {
    const utilization = link.utilization ?? 0;
    if (utilization > 80) return '#ef4444';
    if (utilization > 40) return '#f59e0b';
    return '#64748b';
};

// Per-edge "current" animation params. dir follows power-flow sign, speed scales
// with line utilization → busier lines visibly flow faster. Consumed by the rAF
// loop that marches line-dash-offset to fake electrical current.
export const getLinkFlow = (link: TopologyGraphLink): { energized: number; flowDir: number; flowSpeed: number; reverse: number } => {
    const flow = link.flowKw ?? 0;
    const util = link.utilization ?? 0;
    const energized = Math.abs(flow) > 0.05 ? 1 : 0;
    const reverse = flow < -0.05 ? 1 : 0;
    return {
        energized,
        flowDir: flow >= 0 ? 1 : -1,
        flowSpeed: energized ? Math.min(3.4, 0.6 + (util / 100) * 3) : 0,
        // Static arrowhead flips to point upstream when a bus backfeeds PV up
        // the feeder (negative p_from). Consumed by the edge[reverse] style.
        reverse,
    };
};

export const getNodeColor = (node: TopologyGraphNode): string => {
    if (node.voltageState === 'under') return '#3b82f6';
    if (node.voltageState === 'over') return '#ef4444';
    return node.color;
};

// Transformer drawing >100% of rating. Drives the pulsing red ring so an
// overloaded substation is impossible to miss during a contingency study.
export const isOverloaded = (node: TopologyGraphNode): boolean =>
    node.kind === 'transformer' && (node.transformerLoadingPct ?? 0) > 100;

export const getNodeLabel = (node: TopologyGraphNode): string => [
    node.busName || node.label,
    `${node.kind.toUpperCase()} BUS`,
    `Voltage: ${(node.voltageV ?? 0).toFixed(1)} V (${(node.voltagePu ?? 1).toFixed(3)} pu, ${(node.voltageState ?? 'ok').toUpperCase()})`,
    `Load: ${(node.loadKw ?? 0).toFixed(2)} kW`,
    `Meters: ${node.meterCount ?? 0}`,
    `Generation: ${(node.generationKw ?? 0).toFixed(2)} kW`,
    `Consumption: ${(node.consumptionKw ?? 0).toFixed(2)} kW`,
    (node.solarCapacityKw ?? 0) > 0 ? `Solar: ${(node.solarCapacityKw ?? 0).toFixed(1)} kW` : '',
    node.kind === 'transformer' && node.transformerLoadingPct !== undefined
        ? `Transformer: ${(node.transformerLoadingPct ?? 0).toFixed(0)}% load, ${(node.transformerLossKw ?? 0).toFixed(2)} kW loss`
        : '',
].filter(Boolean).join('\n');

// Edge tooltip: signed power flow (reverse = PV backfeed up the feeder), thermal
// utilization, and series I^2R loss — all live from the simulation power flow.
export const getLinkLabel = (link: TopologyGraphLink): string => {
    const flow = link.flowKw ?? 0;
    return [
        link.label,
        `Flow: ${flow.toFixed(2)} kW${flow < -0.05 ? ' (reverse)' : ''}`,
        `Utilization: ${(link.utilization ?? 0).toFixed(1)}%`,
        `Loss: ${(link.lossKw ?? 0).toFixed(3)} kW`,
    ].join('\n');
};

// node id -> feeder depth (0 = substation). Used to orient edges downhill.
export const buildDepthMap = (nodes: TopologyGraphNode[]): Record<string, number> =>
    Object.fromEntries(nodes.map((node) => [node.id, node.depth ?? 0]));

// Defensive normalization for any edge NOT already oriented by the backend. The
// `/grid/topology` + `/grid/telemetry` endpoints emit endpoints + flow already
// oriented parent(shallow)→child(deep) (downstream load +, negative = reverse), so
// for live data this is a no-op. Kept only to harden against an un-oriented source:
// flip when the source is deeper than the target and swing the flow sign to match.
export const orientLink = (
    link: TopologyGraphLink,
    depthById: Record<string, number>,
): { source: string; target: string; flowKw: number; flipped: boolean } => {
    const flip = (depthById[link.source] ?? 0) > (depthById[link.target] ?? 0);
    return {
        source: flip ? link.target : link.source,
        target: flip ? link.source : link.target,
        flowKw: (link.flowKw ?? 0) * (flip ? -1 : 1),
        flipped: flip,
    };
};

// Signed power on the line, blank below a deadband so idle edges stay clean.
export const getFlowText = (link: TopologyGraphLink): string =>
    Math.abs(link.flowKw ?? 0) > 0.05 ? `${(link.flowKw ?? 0).toFixed(1)} kW` : '';

// Busy lines (>60% thermal) label their flow even without hover/selection so
// congestion is readable at a glance.
export const isBusyLink = (link: TopologyGraphLink): boolean =>
    (link.utilization ?? 0) > 60;

export const getNodeSize = (node: TopologyGraphNode): number =>
    node.kind === 'transformer' ? 42 : node.kind === 'feeder' ? 34 : Math.max(24, Math.min(32, 22 + Math.sqrt(node.meterCount ?? 0) * 2));

export const getTopologySignature = (graphData: TopologyGraphData): string => [
    graphData.nodes.map((node) => `${node.id}:${node.kind}:${node.depth ?? 0}:${node.parent ?? ''}`).sort().join('|'),
    graphData.links.map((link) => `${link.id}:${link.source}>${link.target}`).sort().join('|'),
].join('::');

// Unordered bus-pair key, so A→B and B→A count as the same corridor.
const linkPairKey = (link: TopologyGraphLink): string =>
    [link.source, link.target].sort().join('~');

export const getCytoscapeElements = (graphData: TopologyGraphData): ElementDefinition[] => {
    // Count links per bus pair. Pairs with >1 line are drawn as beziers so the
    // parallel circuits fan out instead of stacking on one straight overlap.
    const pairCount = new Map<string, number>();
    graphData.links.forEach((link) => {
        const key = linkPairKey(link);
        pairCount.set(key, (pairCount.get(key) ?? 0) + 1);
    });
    const depthById = buildDepthMap(graphData.nodes);
    const nodes: NodeDefinition[] = graphData.nodes.map((node) => ({
        group: 'nodes',
        data: {
            ...node,
            id: node.id,
            parent: undefined,
            topologyParent: node.parent,
            displayColor: getNodeColor(node),
            overloaded: isOverloaded(node),
            label: node.label,
            tooltip: getNodeLabel(node),
            size: getNodeSize(node),
            meterText: `${(node.loadKw ?? 0).toFixed(1)} kW | ${node.meterCount ?? 0} m`,
        },
        classes: `topology-node ${node.kind}`,
    }));
    const links: EdgeDefinition[] = graphData.links.map((link) => {
        const oriented = orientLink(link, depthById);
        // Edge with downhill endpoints + flow sign normalized to feeder direction.
        const dl: TopologyGraphLink = { ...link, flowKw: oriented.flowKw };
        return {
            group: 'edges',
            data: {
                ...link,
                id: link.id,
                source: oriented.source,
                target: oriented.target,
                flipped: oriented.flipped,
                flowKw: oriented.flowKw,
                color: getLinkColor(dl),
                width: (link.utilization ?? 0) > 80 ? 5 : (link.utilization ?? 0) > 40 ? 4 : 2,
                flowText: getFlowText(dl),
                busy: isBusyLink(dl),
                parallel: (pairCount.get(linkPairKey(link)) ?? 0) > 1,
                tooltip: getLinkLabel(dl),
                ...getLinkFlow(dl),
            },
            classes: 'topology-line',
        };
    });

    return [...nodes, ...links];
};

// Primary layout: a real hierarchical tier layout. fcose is a force solver and
// packs same-depth nodes on top of each other; breadthfirst lays the feeder tree
// into clean top-down tiers with guaranteed no node overlap.
export const getTreeLayoutOptions = (graphData: TopologyGraphData): BreadthFirstLayoutOptions => {
    const root = graphData.nodes.find((node) => node.kind === 'transformer') ?? graphData.nodes[0];
    const large = graphData.nodes.length > 120;
    return {
        name: 'breadthfirst',
        directed: true,
        roots: root ? [root.id] : undefined,
        spacingFactor: 1.6,
        padding: 80,
        fit: true,
        animate: !large,
        animationDuration: 480,
        avoidOverlap: true,
        nodeDimensionsIncludeLabels: true,
        circle: false,
        grid: false,
    };
};

export const getFcoseLayoutOptions = (graphData: TopologyGraphData, container: HTMLDivElement): FcoseLayoutOptions => {
    const root = graphData.nodes.find((node) => node.kind === 'transformer') ?? graphData.nodes[0];
    const nodeCount = graphData.nodes.length;
    const large = nodeCount > 120;

    const depthGroups = new Map<number, string[]>();
    graphData.nodes.forEach((node) => {
        const depth = node.depth ?? (node.kind === 'transformer' ? 0 : node.kind === 'feeder' ? 1 : 2);
        depthGroups.set(depth, [...(depthGroups.get(depth) ?? []), node.id]);
    });

    // Align same-depth backbone nodes onto one horizontal row (top-down tree).
    // Force-aligning a large service-bus layer packs dozens into one row → overlap.
    const horizontal = [...depthGroups.entries()]
        .sort(([a], [b]) => a - b)
        .filter(([, ids]) => ids.length > 1 && ids.length <= 10)
        .map(([, ids]) => ids);

    // Relative placement enforces top→down hierarchy flow, but each edge adds a
    // solver constraint. Skip on big graphs where plain fcose lays trees out fine.
    const relativePlacementConstraint = large ? [] : graphData.links.flatMap((link) => (
        link.source === link.target ? [] : [{ top: link.source, bottom: link.target, gap: 220 }]
    ));

    return {
        name: 'fcose',
        quality: large ? 'draft' : 'default',
        randomize: false,
        animate: !large,
        animationDuration: 480,
        fit: true,
        padding: 80,
        nodeDimensionsIncludeLabels: true,
        uniformNodeDimensions: false,
        nodeSeparation: large ? 220 : 220,
        idealEdgeLength: large ? 220 : 210,
        edgeElasticity: 0.4,
        nodeRepulsion: large ? 18000 : 16000,
        gravity: 0.2,
        numIter: large ? 1000 : 1600,
        tile: true,
        fixedNodeConstraint: root ? [{ nodeId: root.id, position: { x: container.clientWidth / 2, y: 80 } }] : undefined,
        alignmentConstraint: horizontal.length > 0 ? { horizontal } : undefined,
        relativePlacementConstraint,
    };
};

export const cytoscapeStyles: StylesheetJson = [
    {
        selector: 'node',
        style: {
            width: 'data(size)',
            height: 'data(size)',
            label: '',
            'background-color': 'data(displayColor)',
            'border-color': '#020617',
            'border-width': 2,
            color: '#e2e8f0',
            'font-size': 10,
            'font-weight': 800,
            'text-background-color': '#020617',
            'text-background-opacity': 0.72,
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            'text-margin-x': 8,
            'text-margin-y': -2,
            'text-halign': 'right',
            'text-valign': 'center',
            'min-zoomed-font-size': 7,
            'overlay-opacity': 0,
        },
    },
    {
        selector: 'node.transformer',
        style: {
            shape: 'round-rectangle',
            'border-width': 3,
            label: 'data(label)',
        },
    },
    {
        selector: 'node.feeder',
        style: {
            shape: 'ellipse',
            label: 'data(label)',
        },
    },
    {
        selector: 'node.service',
        style: {
            shape: 'ellipse',
        },
    },
    {
        // Solar-bearing buses (backend has_solar / solar_capacity_kw) get an
        // emerald ring + glow so PV nodes stand out at a glance.
        selector: 'node[?hasSolar]',
        style: {
            'border-color': '#34d399',
            'border-width': 4,
            'underlay-color': '#34d399',
            'underlay-opacity': 0.35,
            'underlay-padding': 6,
        },
    },
    {
        selector: 'edge',
        style: {
            width: 'data(width)',
            label: '',
            'curve-style': 'straight',
            'line-color': 'data(color)',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': 'data(color)',
            'arrow-scale': 0.9,
            'font-size': 8,
            'font-weight': 800,
            color: '#94a3b8',
            'text-background-color': '#020617',
            'text-background-opacity': 0.65,
            'text-background-padding': '2px',
            'line-opacity': 0.88,
            'overlay-opacity': 0,
        },
    },
    {
        // Parallel circuits between the same bus pair: bezier so cytoscape fans
        // them apart instead of overlapping on one straight line. Singles keep
        // the cleaner straight style from the base edge selector.
        selector: 'edge[?parallel]',
        style: {
            'curve-style': 'bezier',
            'control-point-step-size': 40,
        },
    },
    {
        // Busy lines (>60% util) show their flow kW without hover. Zoom-cull so
        // labels vanish when zoomed out instead of cluttering the overview.
        selector: 'edge[?busy]',
        style: {
            label: 'data(flowText)',
            'text-rotation': 'autorotate',
            'min-zoomed-font-size': 7,
        },
    },
    {
        selector: 'edge[energized]',
        style: {
            'line-style': 'dashed',
            'line-dash-pattern': [6, 14],
            'line-cap': 'round',
            'line-opacity': 1,
        },
    },
    {
        // Reverse flow (PV backfeed up the feeder): swing the arrowhead to the
        // source end so the static glyph points the real power-flow direction,
        // matching the backward dash animation.
        selector: 'edge[?reverse]',
        style: {
            'target-arrow-shape': 'none',
            'source-arrow-shape': 'triangle',
            'source-arrow-color': 'data(color)',
        },
    },
    {
        // Overloaded transformer (>100% rating). Static red ring as a baseline;
        // the rAF loop pulses border-width / underlay on top of this.
        selector: 'node[?overloaded]',
        style: {
            'border-color': '#ef4444',
            'border-width': 5,
            'underlay-color': '#ef4444',
            'underlay-opacity': 0.4,
            'underlay-padding': 8,
        },
    },
    {
        selector: '.dimmed',
        style: {
            opacity: 0.22,
            'text-opacity': 0.18,
        },
    },
    {
        selector: 'node.active-neighborhood',
        style: {
            opacity: 1,
            'text-opacity': 1,
            label: 'data(label)',
        },
    },
    {
        selector: 'edge.active-neighborhood',
        style: {
            opacity: 1,
            'text-opacity': 1,
            label: 'data(flowText)',
        },
    },
    {
        selector: 'node:selected',
        style: {
            'border-color': '#ffffff',
            'border-width': 4,
        },
    },
];
