import { useState, useEffect, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Circle, Marker, Popup, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Home, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useNetwork } from '../context/NetworkContext';
import { MapHeader } from '../features/smart-meter-map/MapHeader';
import { MapLegend } from '../features/smart-meter-map/MapLegend';
import { MapInfoCard } from '../features/smart-meter-map/MapInfoCard';
import { SecurityAlert } from '../features/smart-meter-map/SecurityAlert';
import { ElectricalGridOverlay } from '../features/smart-meter-map/ElectricalGridOverlay';
import { ElectricalGridLayerControl } from '../features/smart-meter-map/ElectricalGridLayerControl';
import { createCustomIcon, getMeterColor, getMeterSize } from '../features/smart-meter-map/utils';
import type { MeterData as BaseMeterData } from '../features/smart-meter-map/types';
import type { ElectricalInfrastructure } from '../features/electrical-grid-map/types';

interface MeterData extends BaseMeterData {
    nodal_price?: number;
    total_consumption_kwh?: number;
}

// Set Leaflet default icon
L.Marker.prototype.options.icon = L.icon({
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const SmartMeterMap = () => {
    const { getApiUrl, getWsUrl } = useNetwork();
    const [meters, setMeters] = useState<MeterData[]>([]);
    const [showZones, setShowZones] = useState(true);
    const [isConnected, setIsConnected] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [carbonIntensity, setCarbonIntensity] = useState(250);
    const [isUnderAttack, setIsUnderAttack] = useState(false);
    const [anomalyScore, setAnomalyScore] = useState(0);
    const [healthScore, setHealthScore] = useState(100);
    const [carbonSaved, setCarbonSaved] = useState(0);
    const [showHeatmap, setShowHeatmap] = useState(false);
    const [heatmapMode, setHeatmapMode] = useState<'voltage' | 'congestion'>('voltage');
    const [gridGeoJson, setGridGeoJson] = useState<GeoJSON.FeatureCollection | null>(null);
    
    // Electrical Grid Overlay State
    const [showElectricalGrid, setShowElectricalGrid] = useState(false);
    const [electricalGridFilters, setElectricalGridFilters] = useState({
        operators: ['EGAT', 'MEA', 'PEA'] as ('EGAT' | 'MEA' | 'PEA')[],
        types: [] as string[]
    });
    const [selectedInfrastructure, setSelectedInfrastructure] = useState<ElectricalInfrastructure | null>(null);
    
    const wsRef = useRef<WebSocket | null>(null);

    const center = [13.7563, 100.6610] as [number, number];

    const fetchMeters = useCallback(async (silent = false) => {
        try {
            if (!silent) {
                console.log('[SmartMeterMap] Fetching meters...');
                setLoading(true);
            }
            setError(null);

            const res = await fetch(getApiUrl('/api/v1/meters'));
            if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            const data = await res.json();
            if (!silent) console.log('[SmartMeterMap] Meters response:', data.meters?.length || 0, 'meters');

            if (data.meters && data.meters.length > 0) {
                const geoRes = await fetch(getApiUrl('/api/v1/grid/export?format=geojson'));
                if (!geoRes.ok) throw new Error(`HTTP ${geoRes.status}: ${geoRes.statusText}`);
                const geoData = await geoRes.json();
                if (!silent) console.log('[SmartMeterMap] GeoJSON response:', geoData.features?.length || 0, 'features');
                setGridGeoJson(geoData);

                // Create a map of meter locations from geojson
                const locationMap = new Map<string, {
                    latitude: number;
                    longitude: number;
                    location_name: string;
                    phase: string;
                }>();
                geoData.features?.forEach((feature: {
                    properties?: { meter_id?: string; name?: string; phase?: string };
                    geometry?: { coordinates: [number, number] };
                }) => {
                    if (feature.properties?.meter_id) {
                        const [lng, lat] = feature.geometry?.coordinates || [100.6610, 13.7563];
                        locationMap.set(feature.properties.meter_id, {
                            latitude: lat,
                            longitude: lng,
                            location_name: feature.properties?.name || 'Unknown',
                            phase: feature.properties?.phase || 'A'
                        });
                    }
                });
                console.log('[SmartMeterMap] Location map size:', locationMap.size);

                const mappedMeters = data.meters.map((m: { meter_id: string; meter_type?: string; location?: string }) => {
                    const loc = locationMap.get(m.meter_id) || {
                        latitude: 13.7563,
                        longitude: 100.6610,
                        location_name: m.location || 'Unknown',
                        phase: 'A'
                    };
                    return {
                        meter_id: m.meter_id,
                        location_name: loc.location_name,
                        latitude: loc.latitude,
                        longitude: loc.longitude,
                        phase: loc.phase,
                        meter_type: m.meter_type || 'Unknown',
                        generation: 0,
                        consumption: 0,
                        voltage: 230
                    };
                });
                console.log('[SmartMeterMap] Mapped meters:', mappedMeters.length);
                setMeters(mappedMeters);
            }
        } catch (err) {
            console.error('[SmartMeterMap] Failed to fetch meters:', err);
            setError(err instanceof Error ? err.message : 'Failed to load meter data');
        } finally {
            setLoading(false);
        }
    }, [getApiUrl]);

    useEffect(() => {
        fetchMeters(false);
        const interval = setInterval(() => fetchMeters(true), 5000);
        return () => clearInterval(interval);
    }, [fetchMeters]);

    useEffect(() => {
        const wsUrl = getWsUrl('/ws');
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => setIsConnected(true);
        wsRef.current.onclose = () => setIsConnected(false);
        wsRef.current.onerror = () => setIsConnected(false);

        wsRef.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.type === 'meter_readings' && data.readings) {
                    setMeters(prev => prev.map(meter => {
                        const reading = data.readings.find((r: { meter_id: string; energy_generated?: number; energy_consumed?: number; nodal_price?: number; voltage?: number; is_compromised?: boolean }) => r.meter_id === meter.meter_id);
                        if (reading) {
                            return {
                                ...meter,
                                generation: reading.energy_generated || 0,
                                consumption: reading.energy_consumed || 0,
                                nodal_price: reading.nodal_price || 0,
                                total_consumption_kwh: reading.energy_consumed || 0, 
                                voltage: reading.voltage || 230,
                                is_compromised: reading.is_compromised || false
                            };
                        }
                        return meter;
                    }));
                }

                if (data.type === 'grid_status') {
                    if (data.carbon_intensity !== undefined) setCarbonIntensity(data.carbon_intensity);
                    if (data.is_under_attack !== undefined) setIsUnderAttack(data.is_under_attack);
                    if (data.anomaly_score !== undefined) setAnomalyScore(data.anomaly_score);
                    if (data.health_score !== undefined) setHealthScore(data.health_score);
                    if (data.vpp && data.vpp.carbon_saved_g !== undefined) {
                        setCarbonSaved(data.vpp.carbon_saved_g);
                    }
                }
            } catch (e) {
                console.error('WS error:', e);
            }
        };
        return () => wsRef.current?.close();
    }, [getWsUrl]);

    useEffect(() => {
        if (showHeatmap) {
            const interval = setInterval(() => {
                fetchMeters(); 
            }, 5000);
            return () => clearInterval(interval);
        }
    }, [showHeatmap, fetchMeters]);

    // Show loading state
    if (loading) {
        return (
            <div className="h-screen w-full flex items-center justify-center bg-slate-950">
                <div className="text-center space-y-4">
                    <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
                    <h2 className="text-xl font-bold text-white">Loading Village Map</h2>
                    <p className="text-slate-400">Fetching meter data...</p>
                </div>
            </div>
        );
    }

    // Show error state
    if (error) {
        return (
            <div className="h-screen w-full flex items-center justify-center bg-slate-950">
                <div className="text-center space-y-4 max-w-md p-6">
                    <div className="w-16 h-16 bg-rose-500/20 rounded-full flex items-center justify-center mx-auto">
                        <svg className="w-8 h-8 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h2 className="text-xl font-bold text-white">Failed to Load Map</h2>
                    <p className="text-slate-400">{error}</p>
                    <button
                        onClick={() => {
                            setError(null);
                            setLoading(true);
                            fetchMeters();
                        }}
                        className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl transition-colors"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen w-full relative bg-slate-950">
            <MapHeader
                metersCount={meters.length}
                isConnected={isConnected}
                showZones={showZones}
                onToggleZones={() => setShowZones(!showZones)}
                onRefresh={() => fetchMeters(false)}
                carbonIntensity={carbonIntensity}
                showHeatmap={showHeatmap}
                onToggleHeatmap={() => setShowHeatmap(!showHeatmap)}
                heatmapMode={heatmapMode}
                onToggleHeatmapMode={() => setHeatmapMode(prev => prev === 'voltage' ? 'congestion' : 'voltage')}
            />

            <SecurityAlert 
                isUnderAttack={isUnderAttack}
                anomalyScore={anomalyScore}
                compromisedCount={meters.filter(m => m.is_compromised).length}
            />

            <MapInfoCard 
                metersCount={meters.length} 
                healthScore={healthScore}
                carbonSaved={carbonSaved}
                anomalyCount={meters.filter(m => m.is_compromised).length}
            />

            <MapLegend meters={meters} />

            <MapContainer
                center={center}
                zoom={16}
                scrollWheelZoom={true}
                zoomControl={false}
                style={{ height: '100%', width: '100%', background: '#020617' }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />

                {showHeatmap && gridGeoJson && (
                    <GeoJSON 
                        key={`grid-heatmap-${heatmapMode}-${gridGeoJson.features?.length || 0}`}
                        data={gridGeoJson}
                        style={(feature) => {
                            if (feature?.properties.element_type === 'line') {
                                const loading = feature.properties.loading_percent || 0;
                                if (heatmapMode === 'congestion') {
                                    // Green (0%) to Yellow (50%) to Red (100%)
                                    const color = loading > 80 ? '#f43f5e' : loading > 40 ? '#f59e0b' : '#10b981';
                                    const weight = loading > 80 ? 4 : loading > 40 ? 3 : 2;
                                    return { color, weight, opacity: 0.8, dashArray: loading > 80 ? '5, 5' : undefined };
                                }
                                return { color: '#475569', weight: 1.5, opacity: 0.4 };
                            }
                            return {};
                        }}
                        pointToLayer={(feature, latlng) => {
                            if (feature.properties.element_type === 'bus') {
                                const vm_pu = feature.properties.vm_pu || 1.0;
                                if (heatmapMode === 'voltage') {
                                    // Blue (0.9) to Green (1.0) to Red (1.1)
                                    const color = vm_pu < 0.95 ? '#3b82f6' : vm_pu > 1.05 ? '#f43f5e' : '#10b981';
                                    const radius = 6 + Math.abs(1.0 - vm_pu) * 40;
                                    return L.circleMarker(latlng, {
                                        radius,
                                        fillColor: color,
                                        color: '#fff',
                                        weight: 1,
                                        opacity: 1,
                                        fillOpacity: 0.8
                                    });
                                }
                                // Default bus marker if heatmap active but not in voltage mode
                                return L.circleMarker(latlng, {
                                    radius: 3,
                                    fillColor: '#94a3b8',
                                    color: '#fff',
                                    weight: 1,
                                    opacity: 0.6,
                                    fillOpacity: 0.4
                                });
                            }
                            return L.marker(latlng);
                        }}
                    />
                )}

                {/* Electrical Grid Infrastructure Overlay */}
                {showElectricalGrid && (
                    <ElectricalGridOverlay
                        visible={showElectricalGrid}
                        operators={electricalGridFilters.operators}
                        types={electricalGridFilters.types}
                        onInfrastructureClick={setSelectedInfrastructure}
                    />
                )}

                {meters.map((meter) => {
                    const pos = [meter.latitude, meter.longitude] as [number, number];
                    const color = meter.is_compromised ? '#f43f5e' : getMeterColor(meter.meter_type, meter.generation, meter.consumption);
                    const size = getMeterSize(meter.generation, meter.consumption);
                    const netEnergy = meter.generation - meter.consumption;
                    const voltagePercent = ((meter.voltage / 230) * 100).toFixed(1);
                    const isProducer = netEnergy > 0;
                    const isProsumer = meter.generation > 0 && !isProducer;

                    return (
                        <Marker key={meter.meter_id} position={pos} icon={createCustomIcon(color, size)}>
                            <Popup className="glass-popup" maxWidth={280}>
                                <div className="p-0 min-w-[240px] overflow-hidden">
                                    {/* Header */}
                                    <div className="bg-gradient-to-r from-slate-900 to-slate-800 p-3 border-b border-white/10">
                                        <div className="flex items-center gap-2">
                                            <div className={`p-1.5 rounded-lg ${
                                                isProducer ? 'bg-emerald-500/20' : isProsumer ? 'bg-amber-500/20' : 'bg-blue-500/20'
                                            }`}>
                                                <Home className={`w-4 h-4 ${
                                                    isProducer ? 'text-emerald-400' : isProsumer ? 'text-amber-400' : 'text-blue-400'
                                                }`} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h3 className="font-black text-white text-sm truncate">{meter.location_name}</h3>
                                                <div className="flex items-center gap-2 mt-0.5">
                                                    <span className="text-[10px] font-bold text-slate-400">Phase {meter.phase}</span>
                                                    <span className={`text-[10px] font-black px-1.5 py-0.5 rounded ${
                                                        isProducer ? 'bg-emerald-500/20 text-emerald-400' : isProsumer ? 'bg-amber-500/20 text-amber-400' : 'bg-blue-500/20 text-blue-400'
                                                    }`}>
                                                        {isProducer ? 'Producer' : isProsumer ? 'Prosumer' : 'Consumer'}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Price & Utility Comparison (Phase 27) */}
                                    <div className="p-3 bg-slate-900/50 space-y-3">
                                        <div className="grid grid-cols-2 gap-2">
                                            <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
                                                <div className="text-[9px] uppercase font-black text-indigo-400 mb-0.5">Nodal Price</div>
                                                <div className="text-lg font-black text-white">{(meter.nodal_price || 0).toFixed(2)} ฿</div>
                                                <div className="text-[9px] font-bold text-slate-500">per kWh</div>
                                            </div>
                                            <div className="p-2 rounded-xl bg-white/5 border border-white/10">
                                                <div className="text-[9px] uppercase font-black text-slate-400 mb-0.5">Utility Ref</div>
                                                <div className="text-lg font-black text-slate-300">4.42 ฿</div>
                                                <div className="text-[9px] font-bold text-slate-500">MEA/PEA</div>
                                            </div>
                                        </div>

                                        <div className={`flex items-center justify-between p-2 rounded-xl text-[10px] font-black uppercase tracking-tight ${
                                            (meter.nodal_price || 0) <= 4.42 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                                        }`}>
                                            <span>
                                                {(meter.nodal_price || 0) <= 4.42 
                                                    ? `Saving ${(4.42 - (meter.nodal_price || 0)).toFixed(2)} ฿ vs Utility`
                                                    : `Surcharge ${((meter.nodal_price || 0) - 4.42).toFixed(2)} ฿ (Congestion)`
                                                }
                                            </span>
                                        </div>
                                        
                                        <div className="grid grid-cols-2 gap-2">
                                            <div className="p-2 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                                                <div className="text-[9px] uppercase font-black text-emerald-600 mb-0.5">Generation</div>
                                                <div className="text-lg font-black text-emerald-400">{meter.generation.toFixed(2)}</div>
                                                <div className="text-[9px] font-bold text-emerald-600">kWh</div>
                                            </div>
                                            <div className="p-2 rounded-xl bg-rose-500/5 border border-rose-500/20">
                                                <div className="text-[9px] uppercase font-black text-rose-600 mb-0.5">Consumption</div>
                                                <div className="text-lg font-black text-rose-400">{meter.consumption.toFixed(2)}</div>
                                                <div className="text-[9px] font-bold text-rose-600">kWh</div>
                                            </div>
                                        </div>

                                        {/* Net Energy */}
                                        <div className={`p-2 rounded-xl border ${
                                            isProducer 
                                                ? 'bg-gradient-to-r from-emerald-500/10 to-emerald-600/10 border-emerald-500/30' 
                                                : 'bg-gradient-to-r from-rose-500/10 to-rose-600/10 border-rose-500/30'
                                        }`}>
                                            <div className="flex items-center justify-between">
                                                <span className="text-[10px] font-bold text-slate-400">Net Energy</span>
                                                <span className={`text-sm font-black ${
                                                    isProducer ? 'text-emerald-400' : 'text-rose-400'
                                                }`}>
                                                    {netEnergy > 0 ? '+' : ''}{netEnergy.toFixed(2)} kWh
                                                </span>
                                            </div>
                                        </div>

                                        {/* Voltage */}
                                        <div className="flex items-center justify-between p-2 rounded-xl bg-slate-800/50 border border-white/5">
                                            <div className="flex items-center gap-1.5">
                                                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_6px_rgba(59,130,246,0.6)]" />
                                                <span className="text-[10px] font-bold text-slate-400">Voltage</span>
                                            </div>
                                            <span className="text-xs font-black text-blue-400">{voltagePercent}% pu</span>
                                        </div>

                                        {/* View Details Link (Phase 28) */}
                                        <Link 
                                            to={`/meter/${meter.meter_id}`}
                                            className="flex items-center justify-center gap-2 w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-black uppercase tracking-widest rounded-xl transition-all shadow-lg shadow-indigo-500/20 active:scale-95 group"
                                        >
                                            View Full Analytics
                                            <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                                        </Link>
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}

                {showZones && (
                    <Circle
                        center={center}
                        radius={800}
                        pathOptions={{ color: '#6366f1', fillColor: '#6366f1', fillOpacity: 0.05, dashArray: '10, 10' }}
                    />
                )}
            </MapContainer>

            <MapLegend meters={meters} />
            <MapInfoCard metersCount={meters.length} />

            {/* Electrical Grid Layer Control - Bottom Left */}
            <div className="absolute bottom-4 left-4 z-[1000] flex flex-col gap-2">
                <ElectricalGridLayerControl
                    visible={showElectricalGrid}
                    onToggleVisible={() => setShowElectricalGrid(!showElectricalGrid)}
                    onFilterChange={(filters) => setElectricalGridFilters(filters)}
                />
            </div>
        </div>
    );
};

export default SmartMeterMap;
