"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSimulatorApi } from '@/hooks/useSimulatorApi';
import type { GridTopologyBus, GridTopologyLine, MeterSummary } from '@/lib/api/types';
import type { Core, EventObject } from 'cytoscape';
import type {
    CytoscapeFcoseImport,
    CytoscapeImport,
    SelectedNodeData,
    TopologyGraphData,
    TopologyGraphLink,
    TopologyGraphNode,
    TopologyNodeKind,
} from '@/lib/topology/types';
import {
    cytoscapeStyles,
    emptyGraph,
    getCytoscapeElements,
    getFcoseLayoutOptions,
    getTreeLayoutOptions,
    buildDepthMap,
    getFlowText,
    getLinkColor,
    getLinkFlow,
    getLinkLabel,
    isBusyLink,
    orientLink,
    getNodeColor,
    getNodeLabel,
    getNodeSize,
    getTopologySignature,
    isOverloaded,
    toKw,
    voltageState,
} from '@/lib/topology/graph';
import { TopologyHeader } from '@/components/topology/TopologyHeader';
import { GraphTooltip } from '@/components/topology/GraphTooltip';
import { GraphLoadingState } from '@/components/topology/GraphLoadingState';
import { GraphZoomControls } from '@/components/topology/GraphZoomControls';
import { GridStatsPanel } from '@/components/topology/GridStatsPanel';
import { SelectedNodePanel } from '@/components/topology/SelectedNodePanel';
import { GraphLegend } from '@/components/topology/GraphLegend';

let fcoseRegistered = false;

const GridTopologyView = () => {
    const api = useSimulatorApi();
    const graphContainerRef = useRef<HTMLDivElement>(null);
    const cyRef = useRef<Core | null>(null);
    const resizeObsRef = useRef<ResizeObserver | null>(null);
    const rafRef = useRef<number | null>(null);

    const [ready, setReady] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [graphData, setGraphData] = useState<TopologyGraphData>(emptyGraph);
    const [counts, setCounts] = useState({ buses: 0, lines: 0, meters: 0 });
    const [scale, setScale] = useState(1);
    const [stats, setStats] = useState({
        totalGenerationKw: 0,
        totalConsumptionKw: 0,
        avgVoltage: 230,
        totalLossesKw: 0,
        transformerLossKw: 0,
        transformerLoadingPct: 0,
        curtailedKw: 0,
        frequencyHz: 50,
        congestedLines: 0,
    });
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
    const [tooltip, setTooltip] = useState<{ text: string; x: number; y: number } | null>(null);
    const [layoutGraphData, setLayoutGraphData] = useState<TopologyGraphData>(emptyGraph);
    const topologySignatureRef = useRef('');

    useEffect(() => {
        let mounted = true;
        let pollId: ReturnType<typeof setInterval> | null = null;

        const init = async () => {
            setReady(false);
            setError(null);

            const [topo, metersData] = await Promise.all([
                api.getGridTopology().catch(() => null),
                api.listMeters({ limit: 10000 }).catch(() => null),
            ]);
            if (!mounted) return;

            const meterTypeById: Record<string, string> = {};
            (metersData?.meters ?? []).forEach((meter: MeterSummary) => {
                meterTypeById[meter.meter_id] = meter.meter_type || 'Grid_Consumer';
            });

            const nodes: TopologyGraphNode[] = [];
            const links: TopologyGraphLink[] = [];
            const seenMeters = new Set<string>();

            const buses: Record<string, GridTopologyBus> = topo?.buses ?? {};
            const lines: GridTopologyLine[] = topo?.lines ?? [];

            Object.entries(buses).forEach(([idx, bus]) => {
                const nodeId = `bus-${idx}`;
                const kind: TopologyNodeKind = bus.kind === 'transformer' || bus.type === 't'
                    ? 'transformer'
                    : bus.kind === 'feeder' || bus.vn_kv > 1.0 ? 'feeder' : 'service';
                const depth = bus.depth ?? (kind === 'transformer' ? 0 : kind === 'feeder' ? 1 : 2);
                const meterIds = bus.meter_ids ?? [];
                meterIds.forEach((meterId: string) => seenMeters.add(meterId));

                nodes.push({
                    id: nodeId,
                    label: bus.name,
                    kind,
                    busName: bus.name,
                    vnKv: bus.vn_kv,
                    voltagePu: bus.voltage_pu ?? 1.0,
                    voltageV: (bus.voltage_pu ?? 1.0) * bus.vn_kv * 1000,
                    voltageState: voltageState(bus.voltage_pu ?? 1.0),
                    loadKw: bus.load_kw ?? bus.static_load_kw ?? 0,
                    meterCount: meterIds.length,
                    meterIds,
                    // Backend has_solar / solar_capacity_kw is the real PV layout:
                    // the meter population assigns rooftop PV to a partial subset
                    // of buses (PV_BUS_PENETRATION) plus any GLM-authored PV.
                    solarCapacityKw: bus.solar_capacity_kw ?? bus.topology_solar_capacity_kw ?? 0,
                    hasSolar: bus.has_solar ?? (bus.solar_capacity_kw ?? 0) > 0,
                    generationKw: 0,
                    consumptionKw: 0,
                    color: kind === 'transformer' ? '#e0a92e' : kind === 'feeder' ? '#5f93c0' : '#868d95',
                    depth,
                    parent: bus.parent ? `bus-${bus.parent}` : null,
                    children: (bus.children ?? []).map((child) => `bus-${child}`),
                    val: kind === 'transformer' ? 13 : kind === 'feeder' ? 9 : Math.max(5, 4 + Math.sqrt(meterIds.length)),
                });
            });

            lines.forEach((line, i) => {
                links.push({
                    id: `line-${i}`,
                    source: `bus-${line.from_bus}`,
                    target: `bus-${line.to_bus}`,
                    label: line.name,
                    lineName: line.name,
                    utilization: 0,
                    flowKw: 0,
                });
            });

            setCounts({
                buses: Object.keys(buses).length,
                lines: lines.length,
                meters: Math.max(Object.keys(meterTypeById).length, seenMeters.size),
            });
            setGraphData({ nodes, links });
            setReady(true);

            if (nodes.length === 0) {
                setError('Grid topology data is unavailable from the simulator API.');
            }

            const poll = async () => {
                if (!mounted) return;
                const tele = await api.getGridTelemetry().catch(() => null);
                if (!tele || !mounted) return;

                const teleSummary = tele.summary ?? {};

                setGraphData((prev) => {
                    const readingByMeterId = new Map(
                        (tele.readings ?? [])
                            .map((reading) => [reading.meter_serial ?? reading.meter_id, reading] as const)
                            .filter(([meterId]) => Boolean(meterId))
                    );

                    const nodesNext = prev.nodes.map((node) => {
                        const bus = node.busName ? tele.buses?.[node.busName] : undefined;
                        const pu = bus?.voltage_pu ?? node.voltagePu ?? 1.0;
                        const busReadings = (node.meterIds ?? [])
                            .map((meterId) => readingByMeterId.get(meterId))
                            .filter((reading) => Boolean(reading));
                        const generationKw = busReadings.reduce(
                            (sum, reading) => sum + toKw(reading?.energy_generated || 0, reading?.interval_seconds || 15),
                            0
                        );
                        const consumptionKw = busReadings.reduce(
                            (sum, reading) => sum + toKw(reading?.energy_consumed || 0, reading?.interval_seconds || 15),
                            0
                        );

                        return {
                            ...node,
                            voltagePu: pu,
                            voltageV: pu * (node.vnKv || 0.23) * 1000,
                            voltageState: voltageState(pu),
                            loadKw: bus?.load_kw ?? node.loadKw ?? 0,
                            generationKw,
                            consumptionKw,
                            // Real transformer physics live only on the feeder-head node.
                            ...(node.kind === 'transformer'
                                ? {
                                      transformerLoadingPct: teleSummary.transformer_loading_pct ?? 0,
                                      transformerLossKw: teleSummary.transformer_loss_kw ?? 0,
                                  }
                                : {}),
                        };
                    });

                    const linksNext = prev.links.map((link) => {
                        if (!link.lineName) return link;
                        const line = tele.lines?.[link.lineName];
                        if (!line) return link;
                        return {
                            ...link,
                            utilization: line.utilization_pct ?? 0,
                            flowKw: line.flow_kw ?? 0,
                            lossKw: line.loss_kw ?? 0,
                        };
                    });

                    return { nodes: nodesNext, links: linksNext };
                });

                const readings = tele.readings ?? [];
                const summary = tele.summary ?? {};
                const congested = Object.values(tele.lines ?? {}).filter((line) => (line.utilization_pct ?? 0) > 80).length;
                if (readings.length > 0) {
                    setStats({
                        totalGenerationKw: readings.reduce((sum, reading) => sum + toKw(reading.energy_generated || 0, reading.interval_seconds || 15), 0),
                        totalConsumptionKw: readings.reduce((sum, reading) => sum + toKw(reading.energy_consumed || 0, reading.interval_seconds || 15), 0),
                        avgVoltage: readings.reduce((sum, reading) => sum + (reading.voltage || 230), 0) / readings.length,
                        totalLossesKw: summary.total_losses_kw ?? 0,
                        transformerLossKw: summary.transformer_loss_kw ?? 0,
                        transformerLoadingPct: summary.transformer_loading_pct ?? 0,
                        curtailedKw: summary.total_curtailed_kw ?? 0,
                        frequencyHz: summary.frequency_hz ?? 50,
                        congestedLines: congested,
                    });
                } else {
                    setStats((prev) => ({
                        ...prev,
                        totalLossesKw: summary.total_losses_kw ?? prev.totalLossesKw,
                        transformerLossKw: summary.transformer_loss_kw ?? prev.transformerLossKw,
                        transformerLoadingPct: summary.transformer_loading_pct ?? prev.transformerLoadingPct,
                        curtailedKw: summary.total_curtailed_kw ?? prev.curtailedKw,
                        frequencyHz: summary.frequency_hz ?? prev.frequencyHz,
                        congestedLines: congested,
                    }));
                }
            };

            poll();
            pollId = setInterval(poll, 2000);
        };

        init().catch((e) => {
            console.error('[topo] init failed:', e);
            if (mounted) {
                setError(e instanceof Error ? e.message : 'Grid topology failed to load.');
                setReady(true);
            }
        });

        return () => {
            mounted = false;
            if (pollId) clearInterval(pollId);
        };
    }, [api]);

    const topologySignature = useMemo(() => getTopologySignature(graphData), [graphData]);

    useEffect(() => {
        if (topologySignatureRef.current !== topologySignature) {
            topologySignatureRef.current = topologySignature;
            setLayoutGraphData(graphData);
        }
    }, [graphData, topologySignature]);

    useEffect(() => {
        if (!ready || layoutGraphData.nodes.length === 0 || !graphContainerRef.current) return undefined;

        let disposed = false;

        const mountGraph = async () => {
            const [cytoscapeImport, fcoseImport] = await Promise.all([
                import('cytoscape') as Promise<CytoscapeImport>,
                import('cytoscape-fcose') as Promise<CytoscapeFcoseImport>,
            ]);
            if (disposed || !graphContainerRef.current) return;

            const cytoscape = cytoscapeImport.default ?? cytoscapeImport;
            const fcose = fcoseImport.default ?? fcoseImport;

            if (!fcoseRegistered) {
                cytoscape.use(fcose);
                fcoseRegistered = true;
            }

            cyRef.current?.destroy();

            const cy = cytoscape({
                container: graphContainerRef.current,
                elements: getCytoscapeElements(layoutGraphData),
                style: cytoscapeStyles,
                layout: { name: 'preset' },
                minZoom: 0.12,
                maxZoom: 2.4,
                wheelSensitivity: 0.22,
                autoungrabify: false,
                boxSelectionEnabled: false,
                textureOnViewport: true,
                hideEdgesOnViewport: true,
                pixelRatio: 1,
                motionBlur: false,
            });

            cyRef.current = cy;
            cy.on('tap', 'node', (event: EventObject) => {
                const node = event.target;
                setSelectedNodeId(node.id());
                // Auto-frame the tapped node and its immediate neighbours so the
                // selection animates into focus instead of staying wherever it
                // happened to sit on the canvas.
                cy.animate(
                    { fit: { eles: node.closedNeighborhood(), padding: 140 } },
                    { duration: 360, easing: 'ease-in-out-cubic' },
                );
            });
            cy.on('tap', (event: EventObject) => {
                if (event.target === cy) setSelectedNodeId(null);
            });
            cy.on('mouseover', 'node, edge', (event: EventObject) => {
                const text = event.target.data('tooltip') as string | undefined;
                const oe = event.originalEvent as MouseEvent | undefined;
                if (text && oe) setTooltip({ text, x: oe.clientX, y: oe.clientY });
            });
            cy.on('mouseout', 'node, edge', () => setTooltip(null));
            cy.on('zoom', () => setScale(Number(cy.zoom().toFixed(2))));

            // Primary = breadthfirst (clean top-down tiers, no node overlap). If it
            // somehow throws, fall back to fcose rather than blanking the graph —
            // nodes are already in `cy`.
            try {
                cy.layout(getTreeLayoutOptions(layoutGraphData)).run();
            } catch (layoutError) {
                console.error('[topo] tree layout failed, using fcose fallback:', layoutError);
                cy.layout(getFcoseLayoutOptions(layoutGraphData, graphContainerRef.current)).run();
            }

            // The container can be measured at 0px while React/CSS is still settling,
            // which leaves cytoscape's canvas at height 0 (blank graph) forever, since
            // it never re-measures on its own. Re-sync on every container resize.
            const observer = new ResizeObserver(() => {
                cy.resize();
                cy.fit(undefined, 80);
            });
            observer.observe(graphContainerRef.current);
            resizeObsRef.current = observer;

            // Fake electrical current: march each energized edge's dash offset every
            // frame. Direction = power-flow sign, step = utilization-scaled speed.
            let lastFrameT = 0;
            const animateFlow = (t: number) => {
                const liveCy = cyRef.current;
                if (!liveCy || disposed) return;
                // Normalize the per-frame step to a 60fps baseline so flow speed is
                // identical on 60/120/144Hz displays. First frame: dt≈1 (no jump).
                const dtScale = lastFrameT ? Math.min(4, (t - lastFrameT) / (1000 / 60)) : 1;
                lastFrameT = t;
                // 0..1 pulse for overloaded transformers (~1.8s period).
                const pulse = 0.5 + 0.5 * Math.sin(t / 280);
                liveCy.batch(() => {
                    liveCy.edges('[energized]').forEach((edge) => {
                        const speed = (edge.data('flowSpeed') as number) || 0;
                        const dir = (edge.data('flowDir') as number) || 1;
                        const next = ((edge.scratch('_dash') as number) || 0) - speed * dir * dtScale;
                        edge.scratch('_dash', next);
                        edge.style('line-dash-offset', next);
                    });
                    liveCy.nodes('[?overloaded]').forEach((node) => {
                        node.style('border-width', 4 + pulse * 6);
                        node.style('underlay-opacity', 0.25 + pulse * 0.4);
                        node.style('underlay-padding', 4 + pulse * 10);
                    });
                });
                rafRef.current = requestAnimationFrame(animateFlow);
            };
            rafRef.current = requestAnimationFrame(animateFlow);
        };

        mountGraph().catch((e) => {
            console.error('[topo] cytoscape failed:', e);
            if (!disposed) setError(e instanceof Error ? e.message : 'Network graph renderer failed to load.');
        });

        return () => {
            disposed = true;
            setTooltip(null);
            if (rafRef.current !== null) {
                cancelAnimationFrame(rafRef.current);
                rafRef.current = null;
            }
            resizeObsRef.current?.disconnect();
            resizeObsRef.current = null;
            if (cyRef.current) {
                cyRef.current.destroy();
                cyRef.current = null;
            }
        };
    }, [layoutGraphData, ready]);

    useEffect(() => {
        const cy = cyRef.current;
        if (!cy || graphData.nodes.length === 0) return;

        cy.batch(() => {
            graphData.nodes.forEach((node) => {
                const ele = cy.getElementById(node.id);
                if (!ele.empty()) {
                    const overloaded = isOverloaded(node);
                    ele.data({
                        ...node,
                        displayColor: getNodeColor(node),
                        overloaded,
                        tooltip: getNodeLabel(node),
                        size: getNodeSize(node),
                        meterText: `${(node.loadKw ?? 0).toFixed(1)} kW | ${node.meterCount ?? 0} m`,
                    });
                    // Pulse writes inline border/underlay; clear it once the
                    // transformer drops back under rating so it reverts to base style.
                    if (!overloaded) {
                        ele.removeStyle('border-width underlay-opacity underlay-padding');
                    }
                }
            });

            const depthById = buildDepthMap(graphData.nodes);
            graphData.links.forEach((link) => {
                const ele = cy.getElementById(link.id);
                if (!ele.empty()) {
                    // Endpoints are fixed at build (already oriented downhill); here
                    // only the live flow sign needs normalizing to feeder direction.
                    const dl = { ...link, flowKw: orientLink(link, depthById).flowKw };
                    ele.data({
                        ...dl,
                        color: getLinkColor(dl),
                        flowText: getFlowText(dl),
                        busy: isBusyLink(dl),
                        width: (link.utilization ?? 0) > 80 ? 5 : (link.utilization ?? 0) > 40 ? 4 : 2,
                        tooltip: getLinkLabel(dl),
                        ...getLinkFlow(dl),
                    });
                }
            });
        });
    }, [graphData]);

    useEffect(() => {
        const cy = cyRef.current;
        if (!cy) return;

        cy.batch(() => {
            cy.elements().removeClass('dimmed active-neighborhood');

            if (selectedNodeId) {
                const selected = cy.getElementById(selectedNodeId);
                cy.elements().addClass('dimmed');
                selected.closedNeighborhood().removeClass('dimmed').addClass('active-neighborhood');
                selected.select();
            } else {
                cy.elements().unselect();
            }
        });
    }, [topologySignature, selectedNodeId]);

    const resetView = useCallback(() => {
        setScale(1);
        cyRef.current?.fit(undefined, 96);
    }, []);

    const setGraphZoom = useCallback((zoom: number) => {
        const cy = cyRef.current;
        if (!cy) return;
        const nextZoom = Math.max(0.12, Math.min(2.4, Number(zoom.toFixed(2))));
        cy.zoom({
            level: nextZoom,
            renderedPosition: {
                x: cy.width() / 2,
                y: cy.height() / 2,
            },
        });
        setScale(nextZoom);
    }, []);

    const graphReady = ready && graphData.nodes.length > 0;

    const selectedNode = useMemo<SelectedNodeData | null>(() => {
        if (!selectedNodeId) return null;
        const node = graphData.nodes.find((item) => item.id === selectedNodeId);
        return node ? { ...node } : null;
    }, [graphData.nodes, selectedNodeId]);

    return (
        <div className="h-screen w-full relative bg-[var(--canvas)] overflow-hidden">
            <div
                ref={graphContainerRef}
                style={{ position: 'absolute', inset: 0 }}
                className="bg-[var(--canvas)] bg-[linear-gradient(rgba(58,63,68,0.4)_1px,transparent_1px),linear-gradient(90deg,rgba(58,63,68,0.4)_1px,transparent_1px)] bg-[size:28px_28px]"
                role="img"
                aria-label="Electrical grid graph"
            />

            <GraphTooltip tooltip={tooltip} />

            <TopologyHeader counts={counts} />

            {!graphReady && <GraphLoadingState error={error} />}

            <GraphZoomControls scale={scale} onReset={resetView} onZoom={setGraphZoom} />

            <GridStatsPanel stats={stats} />

            <SelectedNodePanel node={selectedNode} onClose={() => setSelectedNodeId(null)} />

            <GraphLegend />
        </div>
    );
};

export default GridTopologyView;
