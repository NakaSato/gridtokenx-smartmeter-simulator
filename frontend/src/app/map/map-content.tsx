"use client";

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Map as MapIcon, Grid, Zap, Layers, Network, Globe } from 'lucide-react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { MAPBOX_TOKEN } from '@/lib/mapbox';
import { MapControls } from '@/components/maps/map-overlays/MapControls';
import { MapLegend } from '@/components/maps/map-overlays/MapLegend';
import { MapInfoCard } from '@/components/maps/map-overlays/MapInfoCard';
import { SecurityAlert } from '@/components/maps/map-overlays/SecurityAlert';
import { ElectricalGridLayerControl } from '@/components/maps/map-overlays/ElectricalGridLayerControl';
import { createCustomIcon, getMeterColor, getMeterSize } from '@/components/maps/map-overlays/utils';
import type { MeterData as BaseMeterData } from '@/components/maps/map-overlays/types';
import { MicroGridView } from '@/components/maps/micro-grid/MicroGridView';
import ElectricalGridMap from '@/components/maps/electrical-grid/ElectricalGridMap';
import { EgatTransmissionMap } from '@/components/maps/egat-transmission/EgatTransmissionMap';
import { OsmGridMap } from '@/components/maps/osm-grid/OsmGridMap';
import { MeterPopup } from '@/components/meters/MeterPopup';

export interface MeterData extends BaseMeterData {
    nodal_price?: number;
    total_consumption_kwh?: number;
    is_shed?: boolean;
}

type MapView = 'meters' | 'microgrid' | 'infra' | 'egat' | 'osm';
type MapStyle = 'dark' | 'satellite';

const TILE_URLS: Record<MapStyle, string> = {
    dark: `https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/{z}/{x}/{y}{r}?access_token=${MAPBOX_TOKEN}`,
    satellite: `https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/{z}/{x}/{y}{r}?access_token=${MAPBOX_TOKEN}`,
};

const STYLE_ICONS: Record<MapStyle, string> = {
    dark: '🌙',
    satellite: '🛰️',
};

const TABS: { id: MapView; icon: typeof MapIcon; label: string }[] = [
    { id: 'meters', icon: Zap, label: 'Smart Meters' },
    { id: 'microgrid', icon: Grid, label: 'Micro Grid' },
    { id: 'infra', icon: Layers, label: 'Infrastructure' },
    { id: 'egat', icon: Network, label: 'EGAT Grid' },
    { id: 'osm', icon: Globe, label: 'OSM Grid' },
];

function configureLeafletIcons() {
    L.Marker.prototype.options.icon = L.icon({
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
}

function MapViewPersist() {
  useMapEvents({
    moveend(e) {
      const c = e.target.getCenter();
      try { localStorage.setItem('map_view_leaflet', JSON.stringify({ lat: c.lat, lng: c.lng, zoom: e.target.getZoom() })); } catch {}
    }
  });
  return null;
}

const UnifiedMapPage = () => {
  const savedLeafletView = (() => {
    if (typeof window === 'undefined') return null;
    try { return JSON.parse(localStorage.getItem('map_view_leaflet') || ''); } catch { return null; }
  })();
  const leafletCenter: [number, number] = savedLeafletView ? [savedLeafletView.lat, savedLeafletView.lng] : [9.528326082141575, 99.99007762999207];
  const leafletZoom: number = savedLeafletView?.zoom ?? 12;
    const searchParams = useSearchParams();
    const router = useRouter();
    const activeView = (searchParams.get('view') as MapView) || 'meters';
    const { getWsUrl } = useNetwork();

    const [meters, setMeters] = useState<MeterData[]>([]);
    const [metersSource, setMetersSource] = useState<string>('loading');
    const [mapStyle, setMapStyle] = useState<MapStyle>('dark');
    const [showZones, setShowZones] = useState(true);
    const [isConnected, setIsConnected] = useState(false);
    const [carbonIntensity, setCarbonIntensity] = useState(250);
    const [isUnderAttack, setIsUnderAttack] = useState(false);
    const [anomalyScore, setAnomalyScore] = useState(0);
    const [healthScore, setHealthScore] = useState(100);
    const [carbonSaved, setCarbonSaved] = useState(0);
    const [showElectricalGrid, setShowElectricalGrid] = useState(false);
    const [electricalGridFilters, setElectricalGridFilters] = useState({
        operators: ['EGAT', 'MEA', 'PEA'] as ('EGAT' | 'MEA' | 'PEA')[],
        types: [] as string[]
    });

    const wsRef = useRef<WebSocket | null>(null);
    const mapRef = useRef<L.Map | null>(null);
    const mountedRef = useRef(false);

    useEffect(() => {
        configureLeafletIcons();
    }, []);

    useEffect(() => {
        const fetchMeters = async () => {
            try {
                const url = '/api/meters?limit=1000';
                console.log('[Map] Fetching meters from:', url);
                const res = await fetch(url, { cache: 'no-store' });
                console.log('[Map] Meters response status:', res.status);
                if (res.ok) {
                    const data = await res.json();
                    console.log('[Map] Meters received:', data.total, 'source:', data.source);
                    const dbMeters = (data.meters || []).map((m: any) => ({
                        meter_id: m.meter_id,
                        meter_type: m.meter_type,
                        latitude: m.latitude,
                        longitude: m.longitude,
                        generation: 0,
                        consumption: 0,
                        voltage: m.rated_voltage_v || 230,
                        is_compromised: false,
                    })).filter((m: any) => m.latitude && m.longitude);
                    console.log('[Map] Meters with coords:', dbMeters.length);
                    setMeters(dbMeters);
                    setMetersSource(data.source || 'db');
                }
            } catch (e) {
                console.error('[Map] Failed to fetch meters:', e);
                setMetersSource('error');
            }
        };
        fetchMeters();
    }, []);


    useEffect(() => {
        mountedRef.current = true;
        return () => { mountedRef.current = false; };
    }, []);

    useEffect(() => {
        if (meters.length > 0 && mapRef.current) {
            const bounds = L.latLngBounds(meters.map(m => [m.latitude, m.longitude]));
            if (bounds.isValid()) {
                mapRef.current.fitBounds(bounds, { padding: [60, 60], maxZoom: 17 });
            }
        }
    }, [meters]);

    useEffect(() => {
        const wsUrl = getWsUrl('/ws');
        wsRef.current = new WebSocket(wsUrl);
        wsRef.current.onopen = () => setIsConnected(true);
        wsRef.current.onclose = () => setIsConnected(false);
        wsRef.current.onerror = () => setIsConnected(false);
        wsRef.current.onmessage = (event) => {
            if (!mountedRef.current) return;
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'meter_readings' && data.readings) {
                    setMeters(prev => {
                        const existingIds = new Set(prev.map(m => m.meter_id));
                        const updates = prev.map(meter => {
                            const reading = data.readings.find((r: { meter_id: string }) => r.meter_id === meter.meter_id);
                            if (reading) {
                                return {
                                    ...meter,
                                    generation: reading.energy_generated || 0,
                                    consumption: reading.energy_consumed || 0,
                                    nodal_price: reading.nodal_price,
                                    voltage: reading.voltage || 230,
                                    is_compromised: reading.is_compromised,
                                    is_shed: reading.is_shed
                                };
                            }
                            return meter;
                        });
                        // Add new meters from WS that aren't in DB
                        for (const r of (data.readings || []) as any[]) {
                            if (r && !existingIds.has(r.meter_id) && r.latitude && r.longitude) {
                                updates.push({
                                    meter_id: r.meter_id,
                                    meter_type: r.meter_type || 'unknown',
                                    latitude: r.latitude,
                                    longitude: r.longitude,
                                    generation: r.energy_generated || 0,
                                    consumption: r.energy_consumed || 0,
                                    voltage: r.voltage || 230,
                                    is_compromised: r.is_compromised,
                                    is_shed: r.is_shed
                                } as MeterData);
                            }
                        }
                        return updates;
                    });
                }
                if (data.type === 'grid_status') {
                    if (data.carbon_intensity !== undefined) setCarbonIntensity(data.carbon_intensity);
                    if (data.is_under_attack !== undefined) setIsUnderAttack(data.is_under_attack);
                    if (data.anomaly_score !== undefined) setAnomalyScore(data.anomaly_score);
                    if (data.health_score !== undefined) setHealthScore(data.health_score);
                    if (data.vpp?.carbon_saved_g !== undefined) setCarbonSaved(data.vpp.carbon_saved_g);
                }
            } catch (e) {
                console.warn('WS parse error:', e);
            }
        };
        return () => { wsRef.current?.close(); };
    }, [getWsUrl]);

    const setActiveView = useCallback((view: MapView) => {
        router.push(`/map?view=${view}`);
    }, [router]);

    const compromisedCount = useMemo(() => meters.filter(m => m.is_compromised).length, [meters]);

    if (activeView === 'meters') {
        return (
            <div className="h-screen w-full relative bg-slate-950">
                <TabBar activeView={activeView} setActiveView={setActiveView} />
                <SecurityAlert isUnderAttack={isUnderAttack} anomalyScore={anomalyScore} compromisedCount={compromisedCount} />
                <MapControls metersCount={meters.length} isConnected={isConnected} showZones={showZones} onToggleZones={() => setShowZones(!showZones)} onRefresh={() => {}} carbonIntensity={carbonIntensity} />
                <div className="absolute top-20 left-4 z-[9998] flex flex-col gap-2">
                    <button
                        onClick={async () => {
                            try {
                                setMetersSource('loading');
                                const res = await fetch('/api/meters?limit=1000', { cache: 'no-store' });
                                if (res.ok) {
                                    const data = await res.json();
                                    const dbMeters = (data.meters || []).map((m: any) => ({
                                        meter_id: m.meter_id,
                                        meter_type: m.meter_type,
                                        latitude: m.latitude,
                                        longitude: m.longitude,
                                        generation: 0, consumption: 0,
                                        voltage: m.rated_voltage_v || 230,
                                        is_compromised: false,
                                        location_name: `${m.meter_id} — ${m.province || ''}`,
                                        phase: String(m.phase_count || 1),
                                    })).filter((m: any) => m.latitude && m.longitude);
                                    setMeters(dbMeters);
                                    setMetersSource(data.source || 'db');
                                } else { setMetersSource('error'); }
                            } catch { setMetersSource('error'); }
                        }}
                        className={`px-3 py-2 rounded-lg text-xs font-bold border backdrop-blur-xl transition-all ${
                            metersSource === 'db' ? 'bg-slate-800/80 text-white border-white/20' :
                            metersSource === 'error' ? 'bg-red-500/20 text-red-400 border-red-500/40' :
                            'bg-slate-900/80 text-slate-400 border-white/10 hover:text-white'
                        }`}
                    >
                        📡 {meters.length} meters ({metersSource})
                    </button>
                    <button
                        onClick={() => setMapStyle(mapStyle === 'dark' ? 'satellite' : 'dark')}
                        className="px-3 py-2 rounded-lg text-xs font-bold border backdrop-blur-xl bg-slate-900/80 text-slate-300 border-white/10 hover:text-white flex items-center gap-2 transition-all"
                    >
                        <Globe className="w-3.5 h-3.5" /> {STYLE_ICONS[mapStyle]} {mapStyle === 'dark' ? 'Dark' : 'Satellite'}
                    </button>
                </div>
                <MapLegend meters={meters} />
                <MapInfoCard metersCount={meters.length} healthScore={healthScore} carbonSaved={carbonSaved} anomalyCount={compromisedCount} />

                <MapContainer ref={mapRef} center={leafletCenter} zoom={leafletZoom} scrollWheelZoom={true} zoomControl={true} style={{ height: '100%', width: '100%', background: '#020617' }}>
                    <MapViewPersist />
                    <TileLayer
                        attribution='&copy; <a href="https://www.mapbox.com/about/maps/">Mapbox</a>'
                        url={TILE_URLS[mapStyle]}
                    />
                    {meters.map(meter => {
                        const pos = [meter.latitude, meter.longitude] as [number, number];
                        const color = meter.is_compromised ? '#f43f5e' : meter.is_shed ? '#64748b' : getMeterColor(meter.meter_type, meter.generation, meter.consumption);
                        const size = meter.is_shed ? 10 : getMeterSize(meter.generation, meter.consumption);
                        return (
                            <Marker key={meter.meter_id} position={pos} icon={createCustomIcon(color, meter.meter_id?.slice(-6), size)}>
                                <Popup className="glass-popup" maxWidth={280} closeButton={true}>
                                    <MeterPopup meter={meter} />
                                </Popup>
                            </Marker>
                        );
                    })}
                </MapContainer>
                {showElectricalGrid && (
                    <ElectricalGridLayerControl
                        visible={showElectricalGrid}
                        onToggleVisible={() => setShowElectricalGrid(false)}
                    />
                )}
            </div>
        );
    }

    if (activeView === 'infra') {
        return (
            <div className="h-screen w-screen relative">
                <TabBar activeView={activeView} setActiveView={setActiveView} />
                <ElectricalGridMap />
            </div>
        );
    }

    if (activeView === 'egat') {
        return (
            <div className="h-screen w-screen relative">
                <TabBar activeView={activeView} setActiveView={setActiveView} />
                <EgatTransmissionMap />
            </div>
        );
    }

    if (activeView === 'osm') {
        return (
            <div className="h-screen w-screen relative">
                <TabBar activeView={activeView} setActiveView={setActiveView} />
                <OsmGridMap />
            </div>
        );
    }

    return (
        <div className="h-screen w-screen relative">
            <TabBar activeView={activeView} setActiveView={setActiveView} />
            <MicroGridView />
        </div>
    );
};

function TabBar({ activeView, setActiveView }: { activeView: MapView; setActiveView: (v: MapView) => void }) {
    return (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[9999]">
            <div className="flex items-center gap-1 bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-xl p-1 shadow-2xl">
                {TABS.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveView(tab.id)}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-all ${activeView === tab.id ? 'bg-emerald-500/20 text-emerald-400' : 'text-slate-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <tab.icon className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">{tab.label}</span>
                    </button>
                ))}
            </div>
        </div>
    );
}

export default UnifiedMapPage;
