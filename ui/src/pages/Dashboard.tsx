import { useState, useEffect, useCallback, useRef } from 'react';
import {
    Play,
    Square,
    Pause,
    RotateCcw,
    Activity,
    Zap,
    Sun,
    Terminal,
    Settings,
    Search,
    Database,
    History,
    Shield,
    ShieldAlert,
    AlertTriangle,
    TrendingUp,
    Map as MapIcon,
    Plus
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Link } from 'react-router-dom';

import { MeterCard } from '../components/MeterCard';
import { StatCard } from '../components/StatCard';
import AddMeterModal from '../components/AddMeterModal';
import type { Reading } from '../types';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface LogEntry {
    timestamp: string;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error' | 'reading';
    reading?: Reading;
}

const Dashboard = () => {
    const [readings, setReadings] = useState<Reading[]>([]);
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [status, setStatus] = useState<any>({ running: false, paused: false, num_meters: 0, mode: '-', health: {} });
    const [isConnected, setIsConnected] = useState(false);
    const [meterCount, setMeterCount] = useState(20);
    const [search, setSearch] = useState('');
    const [profiles, setProfiles] = useState<string[]>([]);
    const [activeProfile, setActiveProfile] = useState<string>('');
    const [attackStatus, setAttackStatus] = useState<any>({ active: false, targets: [], mode: 'bias', bias_kw: 0.0 });
    const [analytics, setAnalytics] = useState<any>(null);
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);

    const ws = useRef<WebSocket | null>(null);
    const consoleRef = useRef<HTMLDivElement>(null);

    // Stats
    // Aggregates for Grid Intelligence
    const totalGenMW = readings.reduce((acc, r) => acc + (r.energy_generated || 0), 0) * 4.0 / 1000.0;
    const totalConsMW = readings.reduce((acc, r) => acc + (r.energy_consumed || 0), 0) * 4.0 / 1000.0;
    const totalSurpMW = totalGenMW - totalConsMW;
    const gridStability = analytics?.latest?.health_score || 98.2;

    const addLog = useCallback((message: string, type: LogEntry['type'], reading?: Reading) => {
        const entry: LogEntry = {
            timestamp: new Date().toLocaleTimeString(),
            message,
            type,
            reading
        };
        setLogs(prev => [entry, ...prev].slice(0, 100));
    }, []);

    const fetchStatus = useCallback(async () => {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            setStatus(data);
            if (data.num_meters) setMeterCount(data.num_meters);
        } catch (e) {
            console.error('Failed to fetch status', e);
        }
    }, []);

    const fetchProfiles = useCallback(async () => {
        try {
            const res = await fetch('/api/profiles');
            const data = await res.json();
            setProfiles(data.profiles || []);
        } catch (e) {
            console.error('Failed to fetch profiles', e);
        }
    }, []);

    const fetchAnalytics = useCallback(async () => {
        try {
            const res = await fetch('/api/analytics/report');
            const data = await res.json();
            setAnalytics(data);
        } catch (e) {
            console.error('Failed to fetch analytics', e);
        }
    }, []);

    const connectWS = useCallback(() => {
        if (ws.current) ws.current.close();

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
            setIsConnected(true);
            addLog('WebSocket connected', 'success');
        };

        ws.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'meter_readings' || Array.isArray(data)) {
                    const newReadings = data.readings || data;
                    setReadings(newReadings);
                } else if (data.type === 'meter_reading') {
                    setReadings(prev => {
                        const idx = prev.findIndex(r => r.meter_id === data.reading.meter_id);
                        if (idx >= 0) {
                            const updated = [...prev];
                            updated[idx] = data.reading;
                            return updated;
                        }
                        return [...prev, data.reading];
                    });
                } else if (data.type === 'grid_status') {
                    setAnalytics((prev: any) => ({ ...prev, latest: data.data }));
                    addLog(`Grid estimation converged: ${data.data.health}`, 'info');
                }
            } catch (e) {
                addLog('Error parsing message', 'error');
            }
        };

        ws.current.onclose = () => {
            setIsConnected(false);
            addLog('WebSocket disconnected. Retrying...', 'warning');
            setTimeout(connectWS, 5000);
        };
    }, [addLog]);

    useEffect(() => {
        fetchStatus();
        fetchProfiles();
        fetchAnalytics();
        connectWS();
        return () => ws.current?.close();
    }, [connectWS, fetchStatus, fetchProfiles, fetchAnalytics]);

    // Controls
    const handleControl = async (action: string) => {
        try {
            addLog(`Sending ${action} command...`, 'info');
            const res = await fetch(`/api/control/${action}`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                addLog(`${action} successful`, 'success');
                fetchStatus();
            } else {
                addLog(`${action} failed: ${data.message}`, 'error');
            }
        } catch (e) {
            addLog(`Error during ${action}`, 'error');
        }
    };

    const updateMeters = async () => {
        try {
            addLog(`Updating meter count to ${meterCount}...`, 'info');
            const res = await fetch('/api/control/meters', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ num_meters: meterCount })
            });
            const data = await res.json();
            if (data.success) {
                addLog('Meter count updated', 'success');
                setTimeout(fetchStatus, 1000);
            }
        } catch (e) {
            addLog('Error updating meters', 'error');
        }
    };

    const toggleMode = async (mode: 'random' | 'playback', profile?: string) => {
        try {
            addLog(`Switching to ${mode} mode...`, 'info');
            const res = await fetch('/api/control/mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode, profile })
            });
            const data = await res.json();
            if (data.success) {
                addLog(`Mode switched to ${mode}`, 'success');
                fetchStatus();
                if (profile) setActiveProfile(profile);
            } else {
                addLog(`Failed to switch mode: ${data.message}`, 'error');
            }
        } catch (e) {
            addLog('Error switching mode', 'error');
        }
    };

    const handleAttack = async (active: boolean) => {
        try {
            const config = {
                active,
                targets: [], // Target all for demo
                mode: 'bias',
                bias: 5.0, // 5kW bias injection
                stealthy: false
            };

            addLog(`${active ? 'Starting' : 'Stopping'} FDI attack simulation...`, active ? 'warning' : 'info');
            const res = await fetch('/api/control/attack', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            const data = await res.json();
            if (data.success) {
                setAttackStatus(data.status);
                addLog(`Attack simulation ${active ? 'active' : 'stopped'}`, active ? 'error' : 'success');
            }
        } catch (e) {
            addLog('Error controlling attack', 'error');
        }
    };

    const filteredMeters = readings.filter(r =>
        r.meter_id.toLowerCase().includes(search.toLowerCase()) ||
        r.location.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="max-w-7xl mx-auto p-6 space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div className="space-y-2">
                    <h1 className="text-6xl font-black tracking-tighter gradient-text drop-shadow-sm">GRIDTOKENX</h1>
                    <p className="text-slate-400 font-medium">REAL-TIME SMART METER SIMULATOR</p>
                </div>

                <Link to="/map" className="glass px-6 py-4 rounded-2xl flex items-center gap-3 hover:bg-white/5 transition-all group">
                    <div className="p-2 bg-indigo-500/20 rounded-xl group-hover:bg-indigo-500/30 transition-colors">
                        <MapIcon className="w-6 h-6 text-indigo-400" />
                    </div>
                    <div className="text-right hidden md:block">
                        <div className="text-xs font-black uppercase tracking-widest text-slate-500">View</div>
                        <div className="text-lg font-black text-white">Grid Map</div>
                    </div>
                </Link>
            </div>

            {/* Control Panel */}
            <div className="glass rounded-3xl p-6 flex flex-wrap items-center justify-between gap-6 shadow-2xl">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => handleControl('start')}
                        disabled={status.running}
                        className={cn(
                            "p-4 rounded-2xl flex items-center justify-center transition-all shadow-lg active:scale-95",
                            status.running ? "bg-slate-800 text-slate-600 grayscale" : "bg-emerald-500 text-white hover:bg-emerald-400 hover:shadow-emerald-500/20"
                        )}
                    >
                        <Play className="fill-current w-5 h-5" />
                    </button>
                    <button
                        onClick={() => handleControl('pause')}
                        disabled={!status.running || status.paused}
                        className={cn(
                            "p-4 rounded-2xl flex items-center justify-center transition-all shadow-lg active:scale-95",
                            (!status.running || status.paused) ? "bg-slate-800 text-slate-600 grayscale" : "bg-amber-500 text-white hover:bg-amber-400 hover:shadow-amber-500/20"
                        )}
                    >
                        <Pause className="fill-current w-5 h-5" />
                    </button>
                    <button
                        onClick={() => handleControl('resume')}
                        disabled={!status.paused}
                        className={cn(
                            "p-4 rounded-2xl flex items-center justify-center transition-all shadow-lg active:scale-95",
                            !status.paused ? "bg-slate-800 text-slate-600 grayscale" : "bg-blue-500 text-white hover:bg-blue-400 hover:shadow-blue-500/20"
                        )}
                    >
                        <Play className="fill-current w-5 h-5" />
                    </button>
                    <button
                        onClick={() => handleControl('stop')}
                        disabled={!status.running}
                        className={cn(
                            "p-4 rounded-2xl flex items-center justify-center transition-all shadow-lg active:scale-95",
                            !status.running ? "bg-slate-800 text-slate-600 grayscale" : "bg-rose-500 text-white hover:bg-rose-400 hover:shadow-rose-500/20"
                        )}
                    >
                        <Square className="fill-current w-5 h-5" />
                    </button>
                    <button
                        onClick={() => handleControl('restart')}
                        className="p-4 rounded-2xl bg-indigo-500 text-white hover:bg-indigo-400 transition-all shadow-lg shadow-indigo-500/20 active:scale-95"
                    >
                        <RotateCcw className="w-5 h-5" />
                    </button>
                </div>

                {/* Mode Selector */}
                <div className="flex items-center gap-4 bg-slate-900/50 p-2 rounded-2xl border border-white/5">
                    <div
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-xl transition-all cursor-pointer",
                            status.mode === 'random' ? "bg-emerald-500/10 text-emerald-400" : "hover:bg-white/5 text-slate-500"
                        )}
                        onClick={() => toggleMode('random')}
                    >
                        <Zap className="w-4 h-4" />
                        <span className="text-xs font-black uppercase tracking-widest leading-none">Random</span>
                    </div>
                    <div className="h-6 w-px bg-white/10" />
                    <div
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-xl transition-all cursor-pointer",
                            status.mode === 'playback' ? "bg-blue-500/10 text-blue-400" : "hover:bg-white/5 text-slate-500"
                        )}
                        onClick={() => toggleMode('playback', activeProfile || profiles[0])}
                    >
                        <History className="w-4 h-4" />
                        <span className="text-xs font-black uppercase tracking-widest leading-none">Playback</span>
                    </div>
                </div>

                {/* Profile Selector */}
                {status.mode === 'playback' && (
                    <div className="flex items-center gap-4 bg-slate-900/50 p-2 rounded-2xl border border-white/5 animate-in slide-in-from-left-4 duration-300">
                        <div className="flex items-center gap-3 px-4 py-2">
                            <Database className="w-4 h-4 text-slate-500" />
                            <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">Profile</span>
                        </div>
                        <div className="h-8 w-px bg-white/10" />
                        <select
                            value={activeProfile}
                            onChange={(e) => toggleMode('playback', e.target.value)}
                            className="bg-transparent outline-none font-bold text-sm text-blue-400 px-2 cursor-pointer"
                        >
                            <option value="" disabled className="bg-slate-900 text-slate-500 text-sm">Select Profile</option>
                            {profiles.map(p => (
                                <option key={p} value={p} className="bg-slate-900 text-white text-sm">{p}</option>
                            ))}
                        </select>
                        <button
                            onClick={() => fetchProfiles()}
                            className="p-2 hover:bg-white/5 rounded-xl transition-colors"
                            title="Refresh profiles"
                        >
                            <RotateCcw className="w-3 h-3 text-slate-500" />
                        </button>
                    </div>
                )}

                <div className="flex items-center gap-4 bg-slate-900/50 p-2 rounded-2xl border border-white/5">
                    <div className="flex items-center gap-3 px-4 py-2">
                        <Settings className="w-4 h-4 text-slate-500" />
                        <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">Meters</span>
                    </div>
                    <div className="h-8 w-px bg-white/10" />
                    <div className="flex items-center gap-2 pl-2 pr-4">
                        <input
                            type="number"
                            value={meterCount}
                            onChange={(e) => setMeterCount(parseInt(e.target.value))}
                            className="bg-transparent w-12 text-center outline-none font-bold text-sm"
                            placeholder="0"
                        />
                        <button
                            onClick={updateMeters}
                            className="p-1 px-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors text-emerald-400 font-bold text-[10px] uppercase"
                        >
                            Sync
                        </button>
                    </div>
                    <div className="h-8 w-px bg-white/10" />
                    <button
                        onClick={() => setIsAddModalOpen(true)}
                        className="p-2 hover:bg-emerald-500/20 rounded-xl transition-colors group mr-2"
                        title="Add New Meter"
                    >
                        <Plus className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
                    </button>
                </div>

                <div className="flex items-center gap-6 px-4">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => handleAttack(!attackStatus.active)}
                            className={cn(
                                "flex items-center gap-2 px-4 py-2 rounded-xl border transition-all active:scale-95",
                                attackStatus.active
                                    ? "bg-rose-500/20 border-rose-500/50 text-rose-400 animate-pulse"
                                    : "bg-slate-900/50 border-white/5 text-slate-500 hover:border-rose-500/30 hover:text-rose-400"
                            )}
                        >
                            {attackStatus.active ? <ShieldAlert className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
                            <span className="text-xs font-black uppercase tracking-widest leading-none">
                                {attackStatus.active ? 'Mitigating Attack' : 'Infect Grid'}
                            </span>
                        </button>
                    </div>
                    <div className="h-6 w-px bg-white/10" />
                    <div className="flex items-center gap-2">
                        <div className={cn("w-2 h-2 rounded-full", isConnected ? "bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse" : "bg-rose-500")} />
                        <span className="text-xs font-black uppercase tracking-widest text-slate-400">{isConnected ? 'Live' : 'Offline'}</span>
                    </div>
                </div>
            </div>

            {/* Analytics Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in slide-in-from-bottom-4 duration-500">
                <div className="glass rounded-3xl p-6 bg-gradient-to-br from-indigo-500/10 to-transparent border-indigo-500/20 col-span-2">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <TrendingUp className="text-indigo-400" />
                            <h3 className="text-sm font-black uppercase tracking-widest text-slate-400">Grid Performance Analytics</h3>
                        </div>
                        {analytics?.latest && (
                            <div className="flex items-center gap-4">
                                <div className="text-right">
                                    <div className="text-[10px] font-black uppercase tracking-widest text-slate-500">Tech Losses</div>
                                    <div className="text-lg font-black text-rose-400">{(analytics.latest.loss_mw * 1000).toFixed(1)} <span className="text-xs">kW</span></div>
                                </div>
                                <div className="w-px h-8 bg-white/10" />
                                <div className="text-right">
                                    <div className="text-[10px] font-black uppercase tracking-widest text-slate-500">Efficiency</div>
                                    <div className="text-lg font-black text-emerald-400">{(100 - analytics.latest.loss_pct).toFixed(2)} %</div>
                                </div>
                            </div>
                        )}
                    </div>
                    <div className="grid grid-cols-4 gap-4">
                        <div className="bg-slate-900/40 p-4 rounded-2xl border border-white/5 space-y-1">
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Peak Loss</span>
                            <div className="text-xl font-black">{analytics?.max_loss_observed ? (analytics.max_loss_observed * 1000).toFixed(1) : '0.0'} <span className="text-xs text-slate-500">kW</span></div>
                        </div>
                        <div className="bg-slate-900/40 p-4 rounded-2xl border border-white/5 space-y-1">
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Avg Voltage</span>
                            <div className="text-xl font-black text-blue-400">{analytics?.latest?.avg_v?.toFixed(3) || '0.000'} <span className="text-xs text-slate-500">p.u.</span></div>
                        </div>
                        <div className="bg-slate-900/40 p-4 rounded-2xl border border-white/5 space-y-1">
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Max V</span>
                            <div className="text-xl font-black text-indigo-400">{analytics?.max_v_observed?.toFixed(3) || '0.000'}</div>
                        </div>
                        <div className="bg-slate-900/40 p-4 rounded-2xl border border-white/5 space-y-1">
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Min V</span>
                            <div className="text-xl font-black text-amber-400">{analytics?.min_v_observed?.toFixed(3) || '0.000'}</div>
                        </div>
                    </div>
                </div>

                <div className={cn(
                    "glass rounded-3xl p-6 border transition-all",
                    (analytics?.latest?.violations > 0) ? "bg-amber-500/10 border-amber-500/50" : "bg-emerald-500/5 border-emerald-500/20"
                )}>
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <AlertTriangle className={analytics?.latest?.violations > 0 ? "text-amber-400" : "text-emerald-400"} />
                            <h3 className="text-sm font-black uppercase tracking-widest text-slate-400">Grid Health</h3>
                        </div>
                        <div className={cn(
                            "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest",
                            analytics?.latest?.violations > 0 ? "bg-amber-500/20 text-amber-400" : "bg-emerald-500/20 text-emerald-400"
                        )}>
                            {analytics?.latest?.violations > 0 ? 'Critical' : 'Stable'}
                        </div>
                    </div>
                    <div className="text-center py-4">
                        <div className="text-5xl font-black mb-2">{analytics?.latest?.violations || 0}</div>
                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Violations Detected</div>
                    </div>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Grid Generation" value={totalGenMW.toFixed(3)} unit="MW" icon={<Sun className="text-emerald-400" />} color="emerald" />
                <StatCard title="Grid Consumption" value={totalConsMW.toFixed(3)} unit="MW" icon={<Zap className="text-blue-400" />} color="blue" />
                <StatCard title="Net Flow" value={totalSurpMW.toFixed(3)} unit="MW" icon={<Activity className="text-purple-400" />} color="purple" />
                <StatCard title="Stability Score" value={gridStability.toFixed(1)} unit="%" icon={<Shield className="text-rose-400" />} color="rose" />
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-black uppercase tracking-widest text-slate-400 flex items-center gap-3">
                            <Activity className="w-5 h-5 text-emerald-400" />
                            Live Meters
                        </h2>
                        <div className="relative group">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-emerald-400 transition-colors" />
                            <input
                                type="text"
                                placeholder="Search meters..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="bg-slate-900/50 border border-white/5 rounded-xl py-2 pl-10 pr-4 outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/50 transition-all text-sm w-64"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {filteredMeters.length > 0 ? (
                            filteredMeters.map(meter => (
                                <MeterCard key={meter.meter_id} reading={meter} />
                            ))
                        ) : (
                            <div className="col-span-full py-20 text-center glass rounded-3xl border-dashed">
                                <p className="text-slate-500 font-bold uppercase tracking-widest animate-pulse">Waiting for telemetry...</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Console */}
                <div className="space-y-6">
                    <h2 className="text-xl font-black uppercase tracking-widest text-slate-400 flex items-center gap-3">
                        <Terminal className="w-5 h-5 text-indigo-400" />
                        Console
                    </h2>
                    <div className="glass rounded-3xl overflow-hidden shadow-2xl h-[600px] flex flex-col border border-indigo-500/20">
                        <div className="bg-slate-900/80 p-4 border-b border-white/5 flex justify-between items-center">
                            <span className="text-[10px] font-black uppercase tracking-widest text-indigo-400">System Logs</span>
                            <button
                                onClick={() => setLogs([])}
                                className="text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors"
                            >
                                Clear
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 space-y-2 font-mono text-[11px]" ref={consoleRef}>
                            {logs.map((log, i) => (
                                <div key={i} className="flex gap-3">
                                    <span className="text-slate-600 shrink-0">[{log.timestamp}]</span>
                                    <div className="space-y-1">
                                        {log.type === 'reading' && log.reading ? (
                                            <div className="flex items-center gap-2">
                                                <span className="text-blue-400 font-bold">{log.reading.meter_id}</span>
                                                <span className="text-slate-500">→</span>
                                                <span className="text-emerald-400">+{log.reading.energy_generated.toFixed(2)}</span>
                                                <span className="text-slate-500">/</span>
                                                <span className="text-rose-400">-{log.reading.energy_consumed.toFixed(2)}</span>
                                            </div>
                                        ) : (
                                            <span className={cn(
                                                log.type === 'error' && "text-rose-400",
                                                log.type === 'warning' && "text-amber-400",
                                                log.type === 'success' && "text-emerald-400",
                                                log.type === 'info' && "text-blue-400"
                                            )}>
                                                {log.message}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {logs.length === 0 && <div className="text-slate-600 animate-pulse uppercase tracking-widest text-center py-10">Listening for signals...</div>}
                        </div>
                    </div>
                </div>
            </div>

            <AddMeterModal
                isOpen={isAddModalOpen}
                onClose={() => setIsAddModalOpen(false)}
                onSuccess={(data) => {
                    console.log("Meter added:", data);
                    fetchStatus(); // Refresh status to show new meter count
                }}
            />
        </div>
    );
};

export default Dashboard;
