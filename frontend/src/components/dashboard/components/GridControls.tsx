import { memo } from 'react';
import { cn } from '@/lib/common';
import type { SimulatorStatus, AttackStatus, AttackMode } from '@/lib/types';
import { SimulationControls } from './controls/SimulationControls';
import { FleetControls } from './controls/FleetControls';
import { AttackControls } from './controls/AttackControls';
import { Shield, Settings2 } from 'lucide-react';

interface GridControlsProps {
    status: SimulatorStatus;
    handleControl: (action: string) => void;
    meterCount: number;
    setMeterCount: (count: number) => void;
    updateMeters: () => void;
    genMin: number;
    setGenMin: (val: number) => void;
    genMax: number;
    setGenMax: (val: number) => void;
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
    isLoading?: boolean;
}

export const GridControls = memo(({
    status,
    handleControl,
    meterCount,
    setMeterCount,
    updateMeters,
    genMin,
    setGenMin,
    genMax,
    setGenMax,
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
    isLoading
}: GridControlsProps) => {
    return (
        <section className="relative group w-full" aria-label="Simulator controls">
            {/* Ambient Background Glow */}
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500/20 via-purple-500/20 to-emerald-500/20 rounded-[2.5rem] blur-xl opacity-50 group-hover:opacity-75 transition duration-1000"></div>
            
            <div className="relative glass rounded-[2rem] p-6 lg:p-8 grid grid-cols-1 lg:grid-cols-2 gap-6 shadow-2xl backdrop-blur-xl bg-slate-950/60 overflow-hidden">
                {/* Background decorative elements */}
                <div className="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 rounded-full bg-emerald-500/20 blur-[80px] mix-blend-screen pointer-events-none animate-pulse"></div>
                <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-64 h-64 rounded-full bg-indigo-500/20 blur-[80px] mix-blend-screen pointer-events-none animate-pulse" style={{ animationDelay: '1s' }}></div>

                {/* Simulation & Fleet Section */}
                <div className="flex flex-col gap-4 relative z-10 bg-white/5 rounded-2xl p-5 transition-colors shadow-inner">
                    <div className="flex items-center gap-3 mb-1">
                        <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.2)]">
                            <Settings2 className="w-4 h-4" />
                        </div>
                        <h3 className="text-[11px] uppercase font-black text-slate-300 tracking-widest">Simulation & Fleet</h3>
                    </div>
                    <div className="flex flex-col gap-4">
                        <SimulationControls
                            status={status}
                            handleControl={handleControl}
                        />
                        <div className="w-full h-px bg-white/5"></div>
                        <FleetControls 
                            meterCount={meterCount} 
                            setMeterCount={setMeterCount} 
                            updateMeters={updateMeters} 
                            genMin={genMin} 
                            setGenMin={setGenMin} 
                            genMax={genMax} 
                            setGenMax={setGenMax} 
                        />
                    </div>
                </div>

                {/* Grid Integrity Section */}
                <div className="flex flex-col gap-4 relative z-10 bg-white/5 rounded-2xl p-5 transition-colors shadow-inner">
                    <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-3">
                            <div className={cn(
                                "p-2 rounded-xl shadow-[0_0_15px_rgba(0,0,0,0.2)] transition-colors duration-500",
                                isConnected ? "bg-emerald-500/20 text-emerald-400 shadow-emerald-500/20" : "bg-rose-500/20 text-rose-400 shadow-rose-500/20"
                            )}>
                                <Shield className="w-4 h-4" />
                            </div>
                            <h3 className="text-[11px] uppercase font-black text-slate-300 tracking-widest">Grid Integrity</h3>
                        </div>
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/40 shadow-inner">
                            <div className={cn("w-2 h-2 rounded-full", isConnected ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)] animate-pulse" : "bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.8)]")} />
                            <span className={cn("text-[9px] font-black uppercase tracking-widest leading-none mt-0.5", isConnected ? "text-emerald-400" : "text-rose-400")}>{isConnected ? 'Live' : 'Offline'}</span>
                        </div>
                    </div>
                    <AttackControls
                        handleAttack={handleAttack}
                        attackStatus={attackStatus}
                        attackMode={attackMode}
                        setAttackMode={setAttackMode}
                        biasKW={biasKW}
                        setBiasKW={setBiasKW}
                        stealthy={stealthy}
                        setStealthy={setStealthy}
                    />
                </div>
            </div>
        </section>
    );
});

GridControls.displayName = 'GridControls';
