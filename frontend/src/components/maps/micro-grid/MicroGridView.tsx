"use client";

import { useState, useEffect, useMemo, useCallback } from 'react';
import Map, { Source, Layer, NavigationControl } from 'react-map-gl';
import type { ViewStateChangeEvent } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { MAPBOX_TOKEN } from '@/lib/mapbox';
import { useMapStyle } from '@/hooks/useMapStyle';
import { usePersistedViewState } from '@/hooks/usePersistedViewState';
import { useElectricalGridData } from '@/components/maps/electrical-grid/useElectricalGridData';
import { SearchFilterPanel } from './SearchFilterPanel';
import { createLineLayer, createGlowLayer, createHouseLayer, createHouseGlowLayer } from './mapLayers';
import { MICROGRID_CENTER, filterMetersInBoundary, PCC } from './geo';
import { Zap, Sun, Battery, Plug, Globe, Moon, Satellite, Link2, Link2Off, Layers, RefreshCw, Loader2, CircuitBoard, MapPin } from 'lucide-react';

interface MeterFeature {
    id: string;
    meter_type: string;
    gen_kwh: number;
    cons_kwh: number;
    voltage_v: number;
    lon: number;
    lat: number;
}

const METER_ICONS: Record<string, typeof Zap> = {
    Solar_Prosumer: Sun,
    Battery_Storage: Battery,
    Grid_Consumer: Plug,
    Hybrid_Prosumer: Zap,
    EV_Charger: Zap,
};

export function MicroGridView() {
    const { getApiUrl, getWsUrl } = useNetwork();
    const [meters, setMeters] = useState<MeterFeature[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
    const [hoverInfo, setHoverInfo] = useState<{ meter: MeterFeature; x: number; y: number } | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState<'all' | 'producer' | 'consumer'>('all');
    const [viewState, setViewState] = usePersistedViewState('micro-grid', { longitude: MICROGRID_CENTER.lon, latitude: MICROGRID_CENTER.lat, zoom: 15, pitch: 0, bearing: 0 });
    const [animTime, setAnimTime] = useState(0);

    const { mapStyle, toggle, isSatellite } = useMapStyle();
    const { infrastructure } = useElectricalGridData(getApiUrl);
    const [gridMode, setGridMode] = useState<'grid-tied' | 'islanded'>('grid-tied');
    const [showInfraMap, setShowInfraMap] = useState(true);
    const [showInfraData, setShowInfraData] = useState(true);
    const [showLegend, setShowLegend] = useState(false);
    const [apiBoundary, setApiBoundary] = useState<GeoJSON.FeatureCollection | null>(null);
    const [apiFeeders, setApiFeeders] = useState<GeoJSON.FeatureCollection>({ type: 'FeatureCollection', features: [] });
    const [apiElecStatus, setApiElecStatus] = useState<unknown>(null);

    // Fetch microgrid data from backend API
    useEffect(() => {
        const fetchMicrogridData = async () => {
            try {
                const [boundRes, feedRes, statusRes] = await Promise.all([
                    fetch('/api/microgrid/boundary', { cache: 'no-store' }),
                    fetch('/api/microgrid/feeders', { cache: 'no-store' }),
                    fetch('/api/microgrid/status', { cache: 'no-store' }),
                ]);
                if (boundRes.ok) setApiBoundary(await boundRes.json());
                if (feedRes.ok) setApiFeeders(await feedRes.json());
                if (statusRes.ok) {
                    const s = await statusRes.json();
                    setApiElecStatus(s);
                    setGridMode(s.pcc?.mode || 'grid-tied');
                }
            } catch { /* silent */ }
        };
        // Use setTimeout to avoid synchronous state update in effect
        const timeoutId = setTimeout(() => {
            fetchMicrogridData();
        }, 0);
        return () => clearTimeout(timeoutId);
    }, []);

    // Stats
    const totalGen = meters.reduce((s, m) => s + m.gen_kwh, 0);
    const totalCons = meters.reduce((s, m) => s + m.cons_kwh, 0);
    const avgVolt = meters.length ? meters.reduce((s, m) => s + m.voltage_v, 0) / meters.length : 230;
    const selfSufficiency = totalCons > 0 ? (totalGen / totalCons) * 100 : 0;

    // Fetch meters from DB first, then merge with simulation data
    const fetchDBMeters = useCallback(async () => {
        try {
            const res = await fetch('/api/meters?limit=1000', { cache: 'no-store' });
            if (res.ok) {
                const data = await res.json();
                const dbMeters = (data.meters || [])
                    .filter((m: { latitude: number; longitude: number }) => m.latitude && m.longitude)
                    .map((m: { meter_id: string; meter_type: string; rated_voltage_v: number; longitude: number; latitude: number }) => ({
                        id: m.meter_id,
                        meter_type: m.meter_type || 'Unknown',
                        gen_kwh: 0,
                        cons_kwh: 0,
                        voltage_v: m.rated_voltage_v || 230,
                        lon: m.longitude,
                        lat: m.latitude,
                    }));
                if (dbMeters.length > 0) {
                    setMeters(dbMeters);
                    setLastRefresh(new Date());
                    setLoading(false);
                    return true;
                }
            }
        } catch { /* fall through */ }
        return false;
    }, []);

    const fetchData = useCallback(async () => {
        const hasDB = await fetchDBMeters();
        if (hasDB) return; // DB meters loaded, skip simulation fetch

        try {
            const res = await fetch(getApiUrl('/api/v1/grid/export?format=geojson'));
            if (!res.ok) return;
            const data = await res.json();
            const pts = (data.features || [])
                .filter((f: GeoJSON.Feature) => f && f.geometry?.type === 'Point' && f.geometry.coordinates && Array.isArray(f.geometry.coordinates) && (f.properties as any)?.meter_id)
                .map((f: GeoJSON.Feature) => {
                    const props = f.properties as any;
                    const coords = (f.geometry as GeoJSON.Point).coordinates;
                    return {
                        id: props.meter_id,
                        meter_type: props.meter_type || 'Unknown',
                        gen_kwh: props.gen_kwh || 0,
                        cons_kwh: props.cons_kwh || 0,
                        voltage_v: props.voltage_v || 230,
                        lon: coords?.[0] || 100.65,
                        lat: coords?.[1] || 9.528326082141575,
                    };
                });
            setMeters(pts);
            setLastRefresh(new Date());
            setLoading(false);
        } catch { setLoading(false); }
    }, [getApiUrl, fetchDBMeters]);

    useEffect(() => {
        // Use setTimeout to avoid synchronous state update in effect
        const timeoutId = setTimeout(() => {
            fetchData();
        }, 0);
        return () => clearTimeout(timeoutId);
    }, [fetchData]);

    const handleRefresh = useCallback(() => {
        fetchData();
    }, [fetchData]);

    // WS updates
    useEffect(() => {
        const ws = new WebSocket(getWsUrl('/ws'));
        ws.onopen = () => { };
        ws.onerror = () => { };
        ws.onmessage = (e) => {
            try {
                const d = JSON.parse(e.data);
                if (d.type === 'meter_readings' && d.readings) {
                    setMeters(prev => prev.map(m => {
                        const r = d.readings.find((x: any) => x.meter_id === m.id);
                        if (r) return { ...m, gen_kwh: r.energy_generated || 0, cons_kwh: r.energy_consumed || 0, voltage_v: r.voltage || 230 };
                        return m;
                    }));
                }
            } catch { /* silent */ }
        };
        return () => ws.close();
    }, [getWsUrl]);

    // Animation
    useEffect(() => {
        const tick = (t: number) => { setAnimTime(t / 1000); requestAnimationFrame(tick); };
        const id = requestAnimationFrame(tick);
        return () => cancelAnimationFrame(id);
    }, []);

    // Layers
    const lineLayer = useMemo(() => createLineLayer(), []);
    const glowLayer = useMemo(() => createGlowLayer(animTime), [animTime]);
    const houseLayer = useMemo(() => createHouseLayer(), []);
    const houseGlowLayer = useMemo(() => createHouseGlowLayer(animTime), [animTime]);

    // Filter + boundary clip
    const filtered = useMemo(() => {
        return filterMetersInBoundary(meters).filter(m => {
            const matchSearch = !searchQuery || m.id.toLowerCase().includes(searchQuery.toLowerCase()) || m.meter_type.toLowerCase().includes(searchQuery.toLowerCase());
            const isProducer = m.gen_kwh > m.cons_kwh;
            const matchFilter = filterType === 'all' || (filterType === 'producer' && isProducer) || (filterType === 'consumer' && !isProducer);
            return matchSearch && matchFilter;
        });
    }, [meters, searchQuery, filterType]);

    // Boundary from API (or fallback to local)
    const boundarySource = useMemo(() => {
        if (apiBoundary && apiBoundary.features && apiBoundary.features.length > 0) return apiBoundary;
        return {
            type: 'FeatureCollection' as const,
            features: [{
                type: 'Feature' as const,
                geometry: { type: 'Polygon' as const, coordinates: [[
                    [99.9887, 9.5270], [99.9922, 9.5270],
                    [99.9922, 9.5298], [99.9887, 9.5298],
                    [99.9887, 9.5270],
                ]] },
                properties: {},
            }],
        };
    }, [apiBoundary]);

    // Feeder network from API
    const feederSource = useMemo(() => {
        return apiFeeders || { type: 'FeatureCollection', features: [] };
    }, [apiFeeders]);

    // Electrical status from API

    // GeoJSON sources
    const infraSource = useMemo(() => ({
        type: 'FeatureCollection' as const,
        features: infrastructure.map(item => ({
            type: 'Feature' as const,
            geometry: { type: 'Point' as const, coordinates: [item.longitude, item.latitude] as [number, number] },
            properties: {
                id: item.id,
                name: item.name_en || item.id,
                type: item.type,
                operator: item.operator,
                voltage_kv: item.voltage_kv,
                status: item.status,
            },
        })),
    }), [infrastructure]);

    const houseSource = useMemo(() => ({
        type: 'FeatureCollection' as const,
        features: filtered.map((m, i) => ({
            type: 'Feature' as const,
            geometry: { type: 'Point' as const, coordinates: [m.lon, m.lat] as [number, number] },
            properties: { id: m.id, phase: ['A', 'B', 'C'][i % 3], gen: m.gen_kwh, cons: m.cons_kwh, volt: m.voltage_v }
        }))
    }), [filtered]);

    // Loading
    if (loading) {
        return (
            <div className="h-full w-full flex items-center justify-center bg-slate-950">
                <div className="text-center space-y-3">
                    <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
                    <p className="text-sm font-bold text-slate-400">Loading Micro Grid...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full w-full relative bg-slate-950">
            {/* Header */}
            <div className="absolute top-0 left-0 right-0 z-[1000] bg-gradient-to-b from-black/80 to-transparent p-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Zap className="w-5 h-5 text-amber-400" />
                        <h2 className="text-white font-bold text-lg">Micro Grid</h2>
                        <span className="text-gray-400 text-sm">{meters.length} meters</span>
                    </div>
                    <div className="flex items-center gap-2">
                        {lastRefresh && (
                            <span className="text-gray-500 text-xs">
                                Updated {lastRefresh.toLocaleTimeString()}
                            </span>
                        )}
                        <button
                            onClick={handleRefresh}
                            disabled={loading}
                            className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white disabled:opacity-50 transition"
                        >
                            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                        </button>
                        <button
                            onClick={toggle}
                            className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white transition"
                        >
                            {isSatellite ? <MapPin className="w-4 h-4" /> : <CircuitBoard className="w-4 h-4" />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Stats bar */}
            <div className="absolute top-16 left-4 z-[1000] flex items-center gap-2">
                <div className="glass px-3 py-1.5 rounded-lg flex items-center gap-3 text-[10px] sm:text-xs shadow-xl">
                    <div className="flex items-center gap-1.5">
                        <div className={`w-2 h-2 rounded-full animate-pulse ${gridMode === 'grid-tied' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                        <span className="font-bold text-emerald-400">{meters.length} meters</span>
                    </div>
                    <span className="text-slate-700">·</span>
                    <span className="text-slate-400 font-medium hidden sm:inline">Gen: <b className="text-emerald-400">{totalGen.toFixed(1)}</b> kWh</span>
                    <span className="text-slate-700 hidden sm:inline">·</span>
                    <span className="text-slate-400 font-medium hidden sm:inline">Cons: <b className="text-amber-400">{totalCons.toFixed(1)}</b> kWh</span>
                    <span className="text-slate-700">·</span>
                    <span className="text-slate-400 font-medium">⚡ {avgVolt.toFixed(0)}V</span>
                    <span className="text-slate-700 hidden sm:inline">·</span>
                    <span className="text-slate-400 font-medium hidden sm:inline">Self: <b className="text-emerald-400">{selfSufficiency.toFixed(0)}%</b></span>
                </div>

                {/* Mode toggle */}
                <button
                    onClick={async () => {
                        const newMode = gridMode === 'grid-tied' ? 'islanded' : 'grid-tied';
                        try {
                            const res = await fetch('/api/microgrid/pcc/mode', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ mode: newMode }),
                            });
                            if (res.ok) {
                                setGridMode(newMode);
                                const d = await res.json() as any;
                                setApiElecStatus((prev: any) => prev ? { ...prev, pcc: d.pcc } : null);
                            }
                        } catch { setGridMode(newMode); }
                    }}
                    className={`glass px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 text-[10px] shadow-xl transition-colors ${
                        gridMode === 'grid-tied'
                            ? 'text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10'
                            : 'text-amber-400 border-amber-500/30 hover:bg-amber-500/10'
                    }`}
                    title={`Switch to ${gridMode === 'grid-tied' ? 'islanded' : 'grid-tied'} mode`}
                >
                    {gridMode === 'grid-tied' ? <Link2 className="w-3 h-3" /> : <Link2Off className="w-3 h-3" />}
                    {gridMode === 'grid-tied' ? 'GRID-TIED' : 'ISLANDED'}
                </button>

                <button
                    onClick={toggle}
                    className="glass px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 text-[10px] text-slate-400 hover:text-white transition-colors shadow-xl"
                    title="Toggle satellite view"
                >
                    <Globe className="w-3 h-3" /> {isSatellite ? <Satellite className="w-3 h-3" /> : <Moon className="w-3 h-3" />}
                </button>

                <button
                    onClick={() => setShowInfraMap(!showInfraMap)}
                    className={`glass px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 text-[10px] shadow-xl transition-colors ${
                        showInfraMap
                            ? 'text-red-400 border-red-500/30 hover:bg-red-500/10'
                            : 'text-slate-500 border-white/10 hover:text-white'
                    }`}
                    title="Toggle OpenInfraMap power lines"
                >
                    <Layers className="w-3 h-3" /> OIM
                </button>

                <button
                    onClick={() => setShowInfraData(!showInfraData)}
                    className={`glass px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 text-[10px] shadow-xl transition-colors ${
                        showInfraData
                            ? 'text-yellow-400 border-yellow-500/30 hover:bg-yellow-500/10'
                            : 'text-slate-500 border-white/10 hover:text-white'
                    }`}
                    title="Toggle infrastructure data (substations, plants, etc.)"
                >
                    <Zap className="w-3 h-3" /> Infra
                </button>

                <button
                    onClick={() => setShowLegend(!showLegend)}
                    className={`glass px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 text-[10px] shadow-xl transition-colors ${
                        showLegend ? 'text-white border-white/20' : 'text-slate-500 border-white/10 hover:text-white'
                    }`}
                    title="Toggle legend"
                >
                    <Layers className="w-3 h-3" /> Legend
                </button>
            </div>

            {/* Map */}
            <Map
                {...viewState}
                onMove={(evt: ViewStateChangeEvent) => setViewState(evt.viewState)}
                style={{ width: '100%', height: '100%' }}
                mapStyle={mapStyle}
                interactiveLayerIds={['house-points']}
                onMouseMove={(e) => {
                    try {
                        if (!e.target.isStyleLoaded()) return;
                        const features = e.target.queryRenderedFeatures(e.point, { layers: ['house-points'] });
                        if (features.length > 0 && features[0].geometry?.type === 'Point') {
                            const coords = (features[0].geometry as GeoJSON.Point).coordinates;
                            if (coords && coords.length >= 2) {
                                const meter = filtered.find(m => Math.abs(m.lon - coords[0]) < 0.001 && Math.abs(m.lat - coords[1]) < 0.001);
                                if (meter) setHoverInfo({ meter, x: e.point.x, y: e.point.y });
                            }
                        } else { setHoverInfo(null); }
                    } catch { /* layer not ready */ }
                }}
            >
                {/* Boundary outline */}
                <Source id="microgrid-boundary" type="geojson" data={boundarySource}>
                    <Layer
                        id="boundary-fill"
                        type="fill"
                        paint={{
                            'fill-color': gridMode === 'grid-tied' ? '#10b981' : '#f59e0b',
                            'fill-opacity': 0.04,
                        }}
                    />
                    <Layer
                        id="boundary-line"
                        type="line"
                        paint={{
                            'line-color': gridMode === 'grid-tied' ? '#10b981' : '#f59e0b',
                            'line-width': 1.5,
                            'line-opacity': 0.3,
                            'line-dasharray': [4, 3],
                        }}
                    />
                </Source>

                {/* OpenInfraMap power lines layer */}
                {showInfraMap && (
                <Source
                    id="openinframap-power"
                    type="vector"
                    tiles={[
                        'https://openinframap.org/tiles/power/{z}/{x}/{y}.mvt',
                    ]}
                    maxzoom={18}
                >
                    {/* Power lines */}
                    <Layer
                        id="oim-power-line"
                        type="line"
                        source-layer="power_line"
                        paint={{
                            'line-color': '#ef4444',
                            'line-width': 1.5,
                            'line-opacity': 0.6,
                        }}
                    />
                    {/* Power towers */}
                    <Layer
                        id="oim-power-tower"
                        type="circle"
                        source-layer="power_tower"
                        paint={{
                            'circle-radius': 3,
                            'circle-color': '#f59e0b',
                            'circle-opacity': 0.7,
                        }}
                    />
                    {/* Power poles */}
                    <Layer
                        id="oim-power-pole"
                        type="circle"
                        source-layer="power_pole"
                        paint={{
                            'circle-radius': 2,
                            'circle-color': '#6366f1',
                            'circle-opacity': 0.6,
                        }}
                    />
                    {/* Substations */}
                    <Layer
                        id="oim-substation"
                        type="circle"
                        source-layer="substation"
                        paint={{
                            'circle-radius': 5,
                            'circle-color': '#10b981',
                            'circle-stroke-width': 1.5,
                            'circle-stroke-color': '#fff',
                        }}
                    />
                    {/* Power plants */}
                    <Layer
                        id="oim-power-plant"
                        type="circle"
                        source-layer="power_plant"
                        paint={{
                            'circle-radius': 6,
                            'circle-color': '#f43f5e',
                            'circle-stroke-width': 2,
                            'circle-stroke-color': '#fff',
                        }}
                    />
                </Source>
                )}

                {/* Feeder network */}
                <Source id="feeder-lines" type="geojson" data={feederSource}>
                    <Layer
                        id="feeder-main"
                        type="line"
                        filter={['!', ['has', 'cross_link']]}
                        paint={{
                            'line-color': '#6366f1',
                            'line-width': 1.5,
                            'line-opacity': 0.5,
                        }}
                    />
                    <Layer
                        id="feeder-cross"
                        type="line"
                        filter={['==', ['get', 'cross_link'], true]}
                        paint={{
                            'line-color': '#8b5cf6',
                            'line-width': 1,
                            'line-opacity': 0.25,
                            'line-dasharray': [2, 2],
                        }}
                    />
                </Source>

                {/* PCC marker */}
                <Source id="pcc-point" type="geojson" data={{
                    type: 'FeatureCollection',
                    features: [{
                        type: 'Feature',
                        geometry: { type: 'Point', coordinates: [PCC.lon, PCC.lat] },
                        properties: {},
                    }],
                }}>
                    <Layer
                        id="pcc-glow"
                        type="circle"
                        paint={{
                            'circle-radius': 14,
                            'circle-color': gridMode === 'grid-tied' ? '#10b981' : '#f59e0b',
                            'circle-opacity': 0.15,
                        }}
                    />
                    <Layer
                        id="pcc-dot"
                        type="circle"
                        paint={{
                            'circle-radius': 6,
                            'circle-color': gridMode === 'grid-tied' ? '#10b981' : '#f59e0b',
                            'circle-stroke-width': 2,
                            'circle-stroke-color': '#fff',
                        }}
                    />
                </Source>

                <Source id="grid-lines" type="geojson" data={{ type: 'FeatureCollection', features: [] }}>
                    <Layer {...glowLayer} />
                    <Layer {...lineLayer} />
                </Source>
                <Source id="house-points" type="geojson" data={houseSource}>
                    <Layer {...houseGlowLayer} />
                    <Layer {...houseLayer} />
                </Source>

                {/* Electrical infrastructure from API */}
                {showInfraData && (
                <Source id="infra-points" type="geojson" data={infraSource}>
                    <Layer
                        id="infra-glow"
                        type="circle"
                        paint={{
                            'circle-radius': ['match', ['get', 'type'],
                                'power_plant', 14, 'transmission_substation', 11,
                                'distribution_substation', 8, 'solar_farm', 10, 6],
                            'circle-color': ['match', ['get', 'operator'], 'EGAT', '#ef4444', 'PEA', '#10b981', '#3b82f6'],
                            'circle-opacity': 0.15,
                        }}
                    />
                    <Layer
                        id="infra-dot"
                        type="circle"
                        paint={{
                            'circle-radius': ['match', ['get', 'type'],
                                'power_plant', 7, 'transmission_substation', 6,
                                'distribution_substation', 4, 'solar_farm', 5,
                                'transmission_tower', 3, 'distribution_pole', 2, 3],
                            'circle-color': ['match', ['get', 'operator'], 'EGAT', '#ef4444', 'PEA', '#10b981', '#3b82f6'],
                            'circle-stroke-width': 1.5,
                            'circle-stroke-color': '#fff',
                            'circle-opacity': 0.85,
                        }}
                    />
                </Source>
                )}

                <NavigationControl position="bottom-right" />
            </Map>

            {/* Legend panel */}
            {showLegend && (
                <div className="absolute bottom-24 left-4 z-[1000] glass rounded-xl p-3 w-48 shadow-2xl text-[10px]">
                    <p className="text-slate-400 font-bold uppercase tracking-widest mb-2">Operators</p>
                    {[['EGAT','#ef4444'],['MEA','#3b82f6'],['PEA','#10b981']].map(([name,color])=>(
                        <div key={name} className="flex items-center gap-1.5 mb-1">
                            <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{background:color}}/>
                            <span className="text-slate-300">{name}</span>
                        </div>
                    ))}
                    <p className="text-slate-400 font-bold uppercase tracking-widest mt-2 mb-2">Infrastructure</p>
                    {[
                        ['Transmission Substation','#ef4444'],
                        ['Distribution Substation','#10b981'],
                        ['Transmission Tower','#f59e0b'],
                        ['Distribution Pole','#6366f1'],
                        ['Power Plant','#f43f5e'],
                        ['Solar Farm','#facc15'],
                        ['Battery Storage','#06b6d4'],
                        ['EV Charging Station','#a78bfa'],
                    ].map(([name,color])=>(
                        <div key={name} className="flex items-center gap-1.5 mb-1">
                            <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{background:color}}/>
                            <span className="text-slate-300">{name}</span>
                        </div>
                    ))}
                    <p className="text-slate-400 font-bold uppercase tracking-widest mt-2 mb-2">Voltage Levels</p>
                    {[
                        ['500 kV','#dc2626'],
                        ['230 kV','#f59e0b'],
                        ['115 kV','#3b82f6'],
                        ['33 kV','#06b6d4'],
                        ['22 kV','#10b981'],
                    ].map(([name,color])=>(
                        <div key={name} className="flex items-center gap-1.5 mb-1">
                            <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{background:color}}/>
                            <span className="text-slate-300">{name}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Hover popup */}
            {hoverInfo && (
                <div
                    className="absolute z-[1100] pointer-events-none"
                    style={{ left: hoverInfo.x + 12, top: hoverInfo.y - 12 }}
                >
                    <div className="glass px-3 py-2 rounded-lg shadow-xl min-w-[180px]">
                        <div className="flex items-center gap-2 mb-1">
                            {(() => { const Icon = METER_ICONS[hoverInfo.meter.meter_type] || Zap; return <Icon className="w-3.5 h-3.5 text-emerald-400" />; })()}
                            <span className="text-xs font-bold text-white truncate">{hoverInfo.meter.id}</span>
                        </div>
                        <div className="text-[10px] text-slate-400">{hoverInfo.meter.meter_type.replace('_', ' ')}</div>
                        <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5">
                            <span className="text-slate-500">Gen</span>
                            <span className="text-right text-[10px] font-bold text-emerald-400">{hoverInfo.meter.gen_kwh.toFixed(2)} kWh</span>
                            <span className="text-slate-500">Cons</span>
                            <span className="text-right text-[10px] font-bold text-amber-400">{hoverInfo.meter.cons_kwh.toFixed(2)} kWh</span>
                            <span className="text-slate-500">Net</span>
                            <span className={`text-right text-[10px] font-bold ${hoverInfo.meter.gen_kwh > hoverInfo.meter.cons_kwh ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {(hoverInfo.meter.gen_kwh - hoverInfo.meter.cons_kwh).toFixed(2)} kWh
                            </span>
                            <span className="text-slate-500">Volt</span>
                            <span className="text-right text-[10px] font-bold text-blue-400">{hoverInfo.meter.voltage_v.toFixed(0)} V</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Search / Filter */}
            <div className="absolute bottom-20 right-4 sm:bottom-6 sm:right-6 z-[1000]">
                <SearchFilterPanel searchQuery={searchQuery} filterType={filterType} onSearchChange={setSearchQuery} onFilterChange={setFilterType} />
            </div>
        </div>
    );
}
