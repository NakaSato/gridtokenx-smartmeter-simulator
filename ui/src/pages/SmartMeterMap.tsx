import { useState, useEffect, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Link } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Layers, Plus } from 'lucide-react';
import type { Reading } from '../types';
import AddMeterModal from '../components/AddMeterModal';

// Fix Leaflet clean icon issue
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

// Custom icons based on meter type
const createCustomIcon = (color: string) => L.divIcon({
    className: "custom-marker",
    html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; box-shadow: 0 0 10px ${color}, 0 0 20px ${color}; border: 2px solid white;"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6]
});

const SmartMeterMap = () => {
    const [readings, setReadings] = useState<Reading[]>([]);
    const ws = useRef<WebSocket | null>(null);
    const [showZones, setShowZones] = useState(true);
    const [isConnected, setIsConnected] = useState(false);
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);

    // Bangkok Coordinates as center
    const center = [13.7563, 100.5018] as [number, number];

    const connectWS = useCallback(() => {
        if (ws.current) ws.current.close();
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => setIsConnected(true);
        ws.current.onclose = () => {
            setIsConnected(false);
            setTimeout(connectWS, 5000);
        };

        ws.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                let newReadings: Reading[] = [];
                if (data.type === 'meter_reading') newReadings = [data.reading];
                else if (data.type === 'meter_readings') newReadings = data.readings || [];

                setReadings(prev => {
                    // Merge new readings with existing ones
                    const map = new Map(prev.map(r => [r.meter_id, r]));
                    newReadings.forEach(r => map.set(r.meter_id, r));
                    return Array.from(map.values());
                });
            } catch (e) {
                console.error(e);
            }
        };
    }, []);

    useEffect(() => {
        connectWS();
        return () => ws.current?.close();
    }, [connectWS]);

    // Generate fake coordinates for demo purposes if not present
    // In a real app, reading.location would parse to coords
    const getCoordinates = (_id: string, index: number) => {
        // Deterministic pseudo-random based on ID or index
        const lat = 13.7563 + (Math.sin(index) * 0.05);
        const lng = 100.5018 + (Math.cos(index) * 0.05);
        return [lat, lng] as [number, number];
    };

    const getMeterColor = (type: string) => {
        if (type.includes('Solar')) return '#f59e0b'; // amber (Solar)
        if (type.includes('Battery')) return '#10b981'; // emerald (Battery)
        if (type.includes('Hybrid')) return '#a855f7'; // purple (Hybrid)
        return '#3b82f6'; // blue (Grid/Consumer)
    };

    return (
        <div className="h-screen w-full relative bg-slate-950">
            {/* Header Overlay */}
            <div className="absolute top-0 left-0 right-0 z-[1000] p-4 flex justify-between items-start pointer-events-none">
                <div className="pointer-events-auto flex items-center gap-4">
                    <Link to="/" className="glass p-3 rounded-xl hover:bg-white/10 transition-colors text-slate-300">
                        <ArrowLeft className="w-6 h-6" />
                    </Link>
                    <div className="glass px-6 py-3 rounded-xl">
                        <h1 className="text-xl font-black text-white">Smart Meter Map</h1>
                        <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
                            <span className="text-xs font-bold text-slate-400">{readings.length} meters online</span>
                        </div>
                    </div>
                </div>

                <div className="pointer-events-auto flex gap-2">
                    <button
                        onClick={() => setIsAddModalOpen(true)}
                        className="glass px-4 py-2 rounded-xl flex items-center gap-2 text-sm font-bold text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/20 border border-emerald-500/30 transition-all"
                    >
                        <Plus className="w-4 h-4" />
                        Add Meter
                    </button>
                    <button
                        onClick={() => setShowZones(!showZones)}
                        className={`glass px-4 py-2 rounded-xl flex items-center gap-2 text-sm font-bold transition-all ${showZones ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/50' : 'text-slate-400'}`}
                    >
                        <Layers className="w-4 h-4" />
                        {showZones ? 'Hide Zones' : 'Show Zones'}
                    </button>
                    <button
                        onClick={() => setReadings([])}
                        className="glass px-4 py-2 rounded-xl flex items-center gap-2 text-sm font-bold text-slate-400 hover:text-white transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Refresh
                    </button>
                </div>
            </div>

            <AddMeterModal
                isOpen={isAddModalOpen}
                onClose={() => setIsAddModalOpen(false)}
                onSuccess={(data) => {
                    console.log("Meter added:", data);
                    // Optionally trigger a refresh or add to local state
                    // connectWS(); // triggering ws reconnect might force update
                }}
            />

            {/* Map */}
            <MapContainer
                center={center}
                zoom={13}
                scrollWheelZoom={true}
                style={{ height: '100%', width: '100%', background: '#020617' }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />

                {readings.map((reading, idx) => {
                    const pos = getCoordinates(reading.meter_id, idx);
                    const color = getMeterColor(reading.meter_type);

                    return (
                        <Marker key={reading.meter_id} position={pos} icon={createCustomIcon(color)}>
                            <Popup className="glass-popup">
                                <div className="p-2 space-y-2">
                                    <div className="flex items-center justify-between border-b border-slate-700 pb-2 mb-2">
                                        <span className="font-bold text-slate-900">{reading.meter_id}</span>
                                        <span className="text-xs bg-slate-200 px-2 py-0.5 rounded-full text-slate-600">{reading.meter_type}</span>
                                    </div>
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        <div className="space-y-1">
                                            <div className="text-slate-500">Generation</div>
                                            <div className="font-bold text-emerald-600">{reading.energy_generated.toFixed(2)} kWh</div>
                                        </div>
                                        <div className="space-y-1">
                                            <div className="text-slate-500">Consumption</div>
                                            <div className="font-bold text-rose-600">{reading.energy_consumed.toFixed(2)} kWh</div>
                                        </div>
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}

                {/* Fake Microgrid Zone Overlay */}
                {showZones && (
                    <Circle
                        center={center}
                        radius={3000}
                        pathOptions={{ color: '#6366f1', fillColor: '#6366f1', fillOpacity: 0.1, dashArray: '10, 10' }}
                    />
                )}
            </MapContainer>

            {/* Legend Overlay */}
            <div className="absolute bottom-6 right-6 z-[1000] glass p-5 rounded-xl space-y-5 w-72 backdrop-blur-md border border-white/10 shadow-2xl">

                {/* Meter Types */}
                <div className="space-y-3">
                    <h3 className="text-sm font-bold text-white mb-2">Meter Types</h3>
                    <div className="space-y-2 text-xs font-medium text-slate-300">
                        <div className="flex items-center gap-3">
                            <div className="w-3 h-3 rounded-full bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)] border border-white/20" />
                            Solar Prosumer
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)] border border-white/20" />
                            Grid Consumer
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="w-3 h-3 rounded-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)] border border-white/20" />
                            Hybrid Prosumer
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] border border-white/20" />
                            Battery Storage
                        </div>
                    </div>
                </div>

                <div className="h-px bg-white/10 w-full" />

                {/* Wheeling Charges */}
                <div className="space-y-3">
                    <h3 className="text-sm font-bold text-white mb-2">Wheeling Charges (THB/kWh)</h3>
                    <div className="space-y-2 text-xs font-medium text-slate-300">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                                <span>Intra-Zone (Same)</span>
                            </div>
                            <span className="font-bold text-emerald-400">0.50 ฿</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-sky-400" />
                                <span>Adjacent (&lt;2km)</span>
                            </div>
                            <span className="font-bold text-sky-400">1.00 ฿</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-amber-400" />
                                <span>Cross-Zone (2-5km)</span>
                            </div>
                            <span className="font-bold text-amber-400">1.50 ฿</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-rose-400" />
                                <span>Remote (&gt;5km)</span>
                            </div>
                            <span className="font-bold text-rose-400">2.00 ฿</span>
                        </div>
                    </div>
                </div>

                <div className="h-px bg-white/10 w-full" />

                {/* Technical Losses */}
                <div className="space-y-3">
                    <h3 className="text-sm font-bold text-white mb-2">Technical Losses (I²R)</h3>
                    <div className="space-y-2 text-xs font-medium text-slate-300">
                        <div className="flex items-center justify-between">
                            <span>Intra-Zone</span>
                            <span className="font-bold text-emerald-400">1%</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>Adjacent</span>
                            <span className="font-bold text-sky-400">2%</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>Cross-Zone</span>
                            <span className="font-bold text-amber-400">4%</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>Remote</span>
                            <span className="font-bold text-rose-400">6%</span>
                        </div>
                    </div>
                    <p className="text-[10px] text-slate-500 italic mt-2 text-right">
                        Receiver Pays Model - Buyer absorbs losses
                    </p>
                </div>
            </div>
        </div>
    );
};

export default SmartMeterMap;
