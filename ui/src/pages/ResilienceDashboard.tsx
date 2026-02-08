import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
    Activity,
    ChevronLeft,
    AlertTriangle,
    Zap,
    Shield,
    Wifi,
    WifiOff
} from 'lucide-react';
import { StatCard } from '../components/StatCard';
import type { GridHealth } from '../types';

const ResilienceDashboard = () => {
    const [health, setHealth] = useState<GridHealth | null>(null);
    // Simple local history for sparkline if needed, but StatCard doesn't support it yet

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8000/ws');
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'grid_status') {
                    setHealth(data.data);
                }
            } catch (e) {
                console.error("WS invalid JSON", e);
            }
        };
        return () => ws.close();
    }, []);

    const freq = health?.frequency;
    const isIslanded = health?.island_status?.is_islanded || false;

    // Determine status color based on frequency deviation
    const freqDeviation = freq ? Math.abs(freq.value - 50.0) : 0;
    let freqStatus: 'success' | 'warning' | 'error' = 'success';
    if (freqDeviation > 0.5) freqStatus = 'error'; // +/- 0.5 Hz is critical
    else if (freqDeviation > 0.2) freqStatus = 'warning';

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200">
            <div className="max-w-7xl mx-auto p-6 space-y-8 animate-in fade-in duration-500">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3">
                            <Link to="/dashboard" className="p-2 hover:bg-white/5 rounded-xl transition-colors text-slate-400 hover:text-white">
                                <ChevronLeft className="w-6 h-6" />
                            </Link>
                            <h1 className="text-4xl font-black tracking-tighter text-white">GRID RESILIENCE</h1>
                        </div>
                        <p className="text-slate-400 font-medium pl-14">FREQUENCY STABILITY & MICROGRID CONTROL</p>
                    </div>

                    <div className={`px-6 py-4 rounded-2xl flex items-center gap-4 ${isIslanded ? 'bg-amber-500/10 border-amber-500/20' : 'bg-emerald-500/10 border-emerald-500/20'} border`}>
                        <div className="text-right">
                            <div className={`text-xs font-bold uppercase tracking-widest ${isIslanded ? 'text-amber-400' : 'text-emerald-400'}`}>Grid Mode</div>
                            <div className={`text-xl font-black ${isIslanded ? 'text-amber-500' : 'text-emerald-500'}`}>
                                {isIslanded ? 'ISLANDED' : 'CONNECTED'}
                            </div>
                        </div>
                        {isIslanded ? <WifiOff className="w-8 h-8 text-amber-500" /> : <Wifi className="w-8 h-8 text-emerald-500" />}
                    </div>
                </div>

                {freq ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {/* Main Frequency Gauge */}
                        <div className="lg:col-span-2 glass p-6 rounded-3xl relative overflow-hidden flex flex-col justify-center items-center">
                            <div className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-2">System Frequency</div>
                            <div className={`text-7xl font-black tracking-tighter ${freqStatus === 'success' ? 'text-white' :
                                freqStatus === 'warning' ? 'text-amber-400' : 'text-rose-500'
                                }`}>
                                {freq.value.toFixed(3)} <span className="text-2xl text-slate-500 font-bold">Hz</span>
                            </div>
                            <div className="mt-4 flex gap-2">
                                <div className="px-3 py-1 bg-white/5 rounded-full text-xs text-slate-400">
                                    Target: 50.00 Hz
                                </div>
                                <div className={`px-3 py-1 rounded-full text-xs font-bold ${freqDeviation < 0.05 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                                    }`}>
                                    Dev: {(freq.value - 50.0).toFixed(3)}
                                </div>
                            </div>
                        </div>

                        <StatCard
                            title="RoCoF"
                            value={freq.rocof.toFixed(4)}
                            unit="Hz/s"
                            icon={<Activity className="w-5 h-5 text-blue-400" />}
                            status={Math.abs(freq.rocof) > 0.1 ? 'warning' : 'neutral'}
                            trend="Inertia"
                            trendLabel="System"
                        />

                        <StatCard
                            title="Phase Angle"
                            value={freq.angle.toFixed(1)}
                            unit="deg"
                            icon={<Zap className="w-5 h-5 text-purple-400" />}
                            status="neutral"
                        />

                        <StatCard
                            title="Primary Response"
                            value={Math.abs(freq.value - 50.0) > 0.05 ? "ACTIVE" : "Standby"}
                            unit=""
                            icon={<Shield className="w-5 h-5 text-emerald-400" />}
                            status={Math.abs(freq.value - 50.0) > 0.05 ? 'success' : 'neutral'}
                            trend={(Math.abs(freq.value - 50.0) * 20 * 100).toFixed(0)} // Estimate response %
                            trendLabel="% Cap Used"
                        />

                        <StatCard
                            title="System Stability"
                            value={freqStatus === 'success' ? "STABLE" : "UNSTABLE"}
                            unit=""
                            icon={<AlertTriangle className="w-5 h-5 text-amber-400" />}
                            status={freqStatus}
                        />
                    </div>
                ) : (
                    <div className="p-12 text-center text-slate-500">
                        Waiting for Phasor Measurement Unit (PMU) telemetry...
                    </div>
                )}

                {/* Control Actions (Placeholder for now) */}
                <div className="p-6 glass rounded-2xl border border-white/5 opacity-50 pointer-events-none">
                    <h3 className="text-lg font-bold text-white mb-4">Operator Actions (Coming Soon)</h3>
                    <div className="flex gap-4">
                        <button className="px-4 py-2 bg-rose-500/20 text-rose-400 rounded-lg border border-rose-500/30 uppercase text-xs font-bold tracking-widest">
                            Emergency Trip
                        </button>
                        <button className="px-4 py-2 bg-amber-500/20 text-amber-400 rounded-lg border border-amber-500/30 uppercase text-xs font-bold tracking-widest">
                            Island Mode
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ResilienceDashboard;
