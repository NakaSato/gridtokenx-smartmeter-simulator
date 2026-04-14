import { memo } from 'react';
import { Play, Pause, Square, RotateCcw, Zap, History, Database, Settings, Map as MapIcon, Box, Plus, ShieldAlert, Shield } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/common';
import { ControlButton } from '@/components/ui/ControlButton';
import type { SimulatorStatus, AttackStatus, AttackMode } from '@/lib/types';

interface GridControlsProps {
    status: SimulatorStatus;
    handleControl: (action: string) => void;
    toggleMode: (mode: 'random' | 'playback', profile?: string) => void;
    profiles: string[];
    activeProfile: string;
    fetchProfiles: () => void;
    meterCount: number;
    setMeterCount: (count: number) => void;
    updateMeters: () => void;
    setIsAddModalOpen: (open: boolean) => void;
    handleAttack: (active: boolean) => void;
    attackStatus: AttackStatus;
    attackMode: AttackMode;
    setAttackMode: (mode: AttackMode) => void;
    biasKW: number;
    setBiasKW: (bias: number) => void;
    stealthy: boolean;
    setStealthy: (stealthy: boolean) => void;
    isConnected: boolean;
}

export const GridControls = memo(({
    status,
    handleControl,
    toggleMode,
    profiles,
    activeProfile,
    fetchProfiles,
    meterCount,
    setMeterCount,
    updateMeters,
    setIsAddModalOpen,
    handleAttack,
    attackStatus,
    attackMode,
    setAttackMode,
    biasKW,
    setBiasKW,
    stealthy,
    setStealthy,
    isConnected
}: GridControlsProps) => (
    <section className="glass rounded-3xl p-6 flex flex-wrap items-center justify-between gap-6 shadow-2xl border-white/5" aria-label="Simulator controls">
        <div className="flex items-center gap-3">
            <ControlButton
                onClick={() => handleControl('start')}
                disabled={status.running}
                variant="emerald"
                icon={Play}
            />
            <ControlButton
                onClick={() => handleControl('pause')}
                disabled={!status.running || status.paused}
                variant="amber"
                icon={Pause}
            />
            <ControlButton
                onClick={() => handleControl('resume')}
                disabled={!status.paused}
                variant="blue"
                icon={Play}
            />
            <ControlButton
                onClick={() => handleControl('stop')}
                disabled={!status.running}
                variant="rose"
                icon={Square}
            />
            <ControlButton
                onClick={() => handleControl('restart')}
                variant="indigo"
                icon={RotateCcw}
            />
        </div>

        {/* Mode Selector */}
        <div className="flex items-center gap-4 bg-slate-900/50 p-2 rounded-2xl border border-white/5">
            <button
                onClick={() => toggleMode('random')}
                className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-xl transition-all cursor-pointer",
                    status.mode === 'random' ? "bg-emerald-500/10 text-emerald-400" : "hover:bg-white/5 text-slate-500"
                )}
                aria-pressed={status.mode === 'random'}
            >
                <Zap className="w-4 h-4" />
                <span className="text-xs font-black uppercase tracking-widest leading-none">Random</span>
            </button>
            <div className="h-6 w-px bg-white/10" />
            <button
                onClick={() => toggleMode('playback', activeProfile || (profiles.length > 0 ? profiles[0] : undefined))}
                className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-xl transition-all cursor-pointer",
                    status.mode === 'playback' ? "bg-blue-500/10 text-blue-400" : "hover:bg-white/5 text-slate-500"
                )}
                aria-pressed={status.mode === 'playback'}
            >
                <History className="w-4 h-4" />
                <span className="text-xs font-black uppercase tracking-widest leading-none">Playback</span>
            </button>
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
                    aria-label="Select profile"
                >
                    <option value="" disabled className="bg-slate-900 text-slate-500 text-sm">Select Profile</option>
                    {profiles.map(p => (
                        <option key={p} value={p} className="bg-slate-900 text-white text-sm">{p}</option>
                    ))}
                </select>
                <button
                    onClick={fetchProfiles}
                    className="p-2 hover:bg-white/5 rounded-xl transition-colors"
                    title="Refresh profiles"
                    aria-label="Refresh profiles"
                >
                    <RotateCcw className="w-3 h-3 text-slate-500" />
                </button>
            </div>
        )}

        {/* Meters Control */}
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
                    onChange={(e) => setMeterCount(parseInt(e.target.value) || 0)}
                    className="bg-transparent w-12 text-center outline-none font-bold text-sm"
                    placeholder="0"
                    min="0"
                    aria-label="Number of meters"
                />
                <button
                    onClick={updateMeters}
                    className="p-1 px-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors text-emerald-400 font-bold text-[10px] uppercase"
                >
                    Sync
                </button>
            </div>
            <div className="h-8 w-px bg-white/10" />
            <div className="flex items-center gap-1">
                <Link href="/map" className="p-2 hover:bg-emerald-500/10 rounded-xl transition-colors text-slate-400 hover:text-emerald-400" title="Map View" aria-label="Map view">
                    <MapIcon className="w-5 h-5" />
                </Link>
                <Link href="/topology" className="p-2 hover:bg-indigo-500/10 rounded-xl transition-colors text-slate-400 hover:text-indigo-400" title="3D Topology View" aria-label="3D topology view">
                    <Box className="w-5 h-5" />
                </Link>
            </div>
            <div className="h-8 w-px bg-white/10" />
            <button
                onClick={() => setIsAddModalOpen(true)}
                className="p-2 hover:bg-emerald-500/20 rounded-xl transition-colors group mr-2"
                title="Add New Meter"
                aria-label="Add new meter"
            >
                <Plus className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
            </button>
        </div>

        {/* Attack Control */}
        <div className="flex items-center gap-6 px-4">
            <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => handleAttack(!attackStatus.active)}
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-xl border transition-all active:scale-95",
                            attackStatus.active
                                ? "bg-rose-500/20 border-rose-500/50 text-rose-400 animate-pulse"
                                : "bg-slate-900/50 border-white/5 text-slate-500 hover:border-rose-500/30 hover:text-rose-400"
                        )}
                        aria-pressed={attackStatus.active}
                    >
                        {attackStatus.active ? <ShieldAlert className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
                        <span className="text-xs font-black uppercase tracking-widest leading-none">
                            {attackStatus.active ? 'Mitigating Attack' : 'Infect Grid'}
                        </span>
                    </button>
                    <div className="flex items-center gap-1 bg-slate-900/50 px-2 py-1 rounded-lg border border-white/5">
                        <label htmlFor="attackMode" className="sr-only">Attack Mode</label>
                        <select
                            id="attackMode"
                            value={attackMode}
                            onChange={(e) => setAttackMode(e.target.value as AttackMode)}
                            className="bg-transparent text-[10px] font-bold text-slate-400 outline-none uppercase"
                        >
                            <option value="bias">BIAS</option>
                            <option value="scale">SCALE</option>
                            <option value="random">RANDOM</option>
                        </select>
                    </div>
                </div>
                <div className="flex items-center gap-4 px-1">
                    <div className="flex items-center gap-2">
                        <label htmlFor="biasKW" className="text-[9px] font-bold text-slate-500 uppercase">Bias</label>
                        <input
                            id="biasKW"
                            type="number"
                            value={biasKW}
                            onChange={(e) => setBiasKW(parseFloat(e.target.value) || 0)}
                            className="bg-transparent w-8 text-[10px] font-black text-rose-400 outline-none"
                            step="0.1"
                        />
                        <span className="text-[9px] font-bold text-slate-600">kW</span>
                    </div>
                    <label className="flex items-center gap-1 cursor-pointer group">
                        <input
                            type="checkbox"
                            checked={stealthy}
                            onChange={(e) => setStealthy(e.target.checked)}
                            className="sr-only"
                        />
                        <div className={cn(
                            "w-3 h-3 rounded border transition-colors",
                            stealthy ? "bg-indigo-500 border-indigo-400" : "bg-slate-800 border-white/10 group-hover:border-indigo-500/50"
                        )} />
                        <span className="text-[9px] font-bold text-slate-500 uppercase group-hover:text-indigo-400">Stealth</span>
                    </label>
                </div>
            </div>
            <div className="h-10 w-px bg-white/10" />
            <div className="flex items-center gap-2">
                <div className={cn("w-2 h-2 rounded-full", isConnected ? "bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse" : "bg-rose-500")} />
                <span className="text-xs font-black uppercase tracking-widest text-slate-400">{isConnected ? 'Live' : 'Offline'}</span>
            </div>
        </div>
    </section>
));

GridControls.displayName = 'GridControls';
