import { useState, useEffect, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Circle, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Home } from 'lucide-react';
import { useNetwork } from '../context/NetworkContext';
import { MapHeader } from './SmartMeterMap/MapHeader';
import { MapLegend } from './SmartMeterMap/MapLegend';
import { MapInfoCard } from './SmartMeterMap/MapInfoCard';
import { createCustomIcon, getMeterColor, getMeterSize } from './SmartMeterMap/utils';
import type { MeterData } from './SmartMeterMap/types';

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
    const [showZones, setShowZones] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const wsRef = useRef<WebSocket | null>(null);

    const center = [13.7563, 100.6610] as [number, number];

    const fetchMeters = useCallback(async () => {
        try {
            console.log('[SmartMeterMap] Fetching meters...');
            setLoading(true);
            setError(null);
            
            const res = await fetch(getApiUrl('/api/meters'));
            if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            const data = await res.json();
            console.log('[SmartMeterMap] Meters response:', data.meters?.length || 0, 'meters');

            if (data.meters && data.meters.length > 0) {
                console.log('[SmartMeterMap] Fetching grid geojson...');
                const geoRes = await fetch(getApiUrl('/api/grid/geojson'));
                if (!geoRes.ok) throw new Error(`HTTP ${geoRes.status}: ${geoRes.statusText}`);
                const geoData = await geoRes.json();
                console.log('[SmartMeterMap] GeoJSON response:', geoData.features?.length || 0, 'features');

                // Create a map of meter locations from geojson
                const locationMap = new Map();
                geoData.features?.forEach((feature: any) => {
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

                const mappedMeters = data.meters.map((m: any) => {
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
        fetchMeters();
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
                        const reading = data.readings.find((r: any) => r.meter_id === meter.meter_id);
                        if (reading) {
                            return {
                                ...meter,
                                generation: reading.energy_generated || 0,
                                consumption: reading.energy_consumed || 0,
                                voltage: reading.voltage || 230
                            };
                        }
                        return meter;
                    }));
                }
            } catch (e) {
                console.error('WS error:', e);
            }
        };

        return () => wsRef.current?.close();
    }, [getWsUrl]);

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
                onRefresh={fetchMeters}
            />

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

                {meters.map((meter) => {
                    const pos = [meter.latitude, meter.longitude] as [number, number];
                    const color = getMeterColor(meter.meter_type, meter.generation, meter.consumption);
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

                                    {/* Energy Stats */}
                                    <div className="p-3 bg-slate-900/50">
                                        <div className="grid grid-cols-2 gap-2 mb-3">
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
                                        <div className={`p-2 rounded-xl mb-2 border ${
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
        </div>
    );
};

export default SmartMeterMap;
