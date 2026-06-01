import { memo } from 'react';
import { 
    Play, Pause, Square, RotateCcw, Zap, History, Database, Settings, 
    Map as MapIcon, Box, Plus, ShieldAlert, Shield, Sun, Cloud, CloudLightning, Moon, Activity 
} from 'lucide-react';
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
    genMin: number;
    setGenMin: (val: number) => void;
    genMax: number;
    setGenMax: (val: number) => void;
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
    onUpdateWeather?: (mode: string) => Promise<void>;
    onUpdateStress?: (multiplier: number) => Promise<void>;
    onUpdateScenario?: (scenario: string) => Promise<void>;
    isLoading?: boolean;
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
    genMin,
    setGenMin,
    genMax,
    setGenMax,
    setIsAddModalOpen,
    handleAttack,
    attackStatus,
    attackMode,
    setAttackMode,
    biasKW,
    setBiasKW,
    stealthy,
    setStealthy,
    isConnected,
    onUpdateWeather,
    onUpdateStress,
    onUpdateScenario,
    isLoading
}: GridControlsProps) => {
    const weatherOptions = [
        { mode: 'Sunny', icon: Sun, color: 'text-amber-400' },
        { mode: 'Cloudy', icon: Cloud, color: 'text-slate-400' },
        { mode: 'Stormy', icon: CloudLightning, color: 'text-indigo-400' },
        { mode: 'Eclipse', icon: Moon, color: 'text-purple-400' },
    ];

    return (
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
            <div className="flex items-center gap-1 bg-slate-900/50 px-3 py-2 rounded-xl border border-white/5 ml-2">
                <Box className="w-3 h-3 text-slate-500" />
                <select
                    id="scenarioSelect"
                    defaultValue=""
                    onChange={(e) => onUpdateScenario?.(e.target.value)}
                    className="bg-transparent text-[10px] font-black text-slate-400 outline-none uppercase cursor-pointer"
                >
                    <option value="" disabled>Scenario</option>
                    <option value="ieee123">IEEE 123-Node</option>
                    <option value="ieee8500">IEEE 8500-Node</option>
                </select>
            </div>

            <div className="flex items-center gap-1 bg-slate-900/50 px-3 py-1.5 rounded-xl border border-white/5 ml-2">
                <Activity className="w-3 h-3 text-slate-500" />
                <input
                    type="number"
                    value={meterCount}
                    onChange={(e) => setMeterCount(parseInt(e.target.value) || 20)}
                    className="bg-transparent w-10 text-[10px] font-black text-slate-400 outline-none text-center"
                    min="1"
                    max="10000"
                />
                <input
                    type="number"
                    value={genMin}
                    onChange={(e) => setGenMin(parseFloat(e.target.value) || 0)}
                    className="bg-transparent w-8 text-[10px] font-black text-amber-400 outline-none text-center"
                    placeholder="Min"
                />
                <input
                    type="number"
                    value={genMax}
                    onChange={(e) => setGenMax(parseFloat(e.target.value) || 0)}
                    className="bg-transparent w-8 text-[10px] font-black text-amber-400 outline-none text-center"
                    placeholder="Max"
                />
                <button
                    onClick={updateMeters}
                    className="p-1 hover:bg-white/10 rounded transition-colors"
                    title="Update Fleet Config"
                >
                    <Plus className="w-3 h-3 text-emerald-400" />
                </button>
            </div>
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

        {/* Weather & Stress Controls */}
        <div className="flex flex-wrap items-center gap-6 bg-slate-900/50 p-2 px-4 rounded-2xl border border-white/5">
            <div className="flex items-center gap-2">
                {weatherOptions.map((opt) => (
                    <button
                        key={opt.mode}
                        onClick={() => onUpdateWeather?.(opt.mode)}
                        disabled={isLoading}
                        className={cn(
                            "p-2 rounded-xl border transition-all active:scale-95 group relative",
                            status.weather_mode === opt.mode 
                                ? "bg-white/10 border-white/20 shadow-lg" 
                                : "bg-black/20 border-white/5 hover:border-white/10 grayscale-[0.5] hover:grayscale-0"
                        )}
                        title={opt.mode}
                    >
                        <opt.icon className={cn("w-4 h-4", opt.color)} />
                    </button>
                ))}
            </div>

            <div className="h-8 w-px bg-white/10 hidden sm:block" />

            <div className="flex items-center gap-4 min-w-[160px]">
                <div className="flex flex-col">
                    <span className="text-[8px] font-black uppercase tracking-widest text-slate-500 leading-none mb-1">Stress</span>
                    <span className={cn(
                        "text-[10px] font-black tracking-tighter",
                        status.grid_stress > 1.2 ? "text-rose-400" : status.grid_stress < 0.8 ? "text-emerald-400" : "text-amber-400"
                    )}>
                        {status.grid_stress.toFixed(1)}x
                    </span>
                </div>
                <div className="flex-1 flex flex-col justify-center">
                    <input
                        type="range"
                        min="0.5"
                        max="2.0"
                        step="0.1"
                        value={status.grid_stress}
                        onChange={(e) => onUpdateStress?.(parseFloat(e.target.value))}
                        disabled={isLoading}
                        className="w-full h-1 bg-black/40 rounded-full appearance-none cursor-pointer accent-indigo-500 hover:accent-indigo-400 transition-all"
                    />
                </div>
                {isLoading && (
                    <Activity className="w-3 h-3 text-indigo-400 animate-spin" />
                )}
            </div>
        </div>
    </section>
    );
});

GridControls.displayName = 'GridControls';
