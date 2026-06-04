import { memo } from 'react';
import { ShieldAlert, Shield } from 'lucide-react';
import { cn } from '@/lib/common';
import type { AttackStatus, AttackMode } from '@/lib/types';

interface AttackControlsProps {
    handleAttack: (active: boolean) => void;
    attackStatus: AttackStatus;
    attackMode: AttackMode;
    setAttackMode: (mode: AttackMode) => void;
    biasKW: number;
    setBiasKW: (bias: number) => void;
    stealthy: boolean;
    setStealthy: (stealthy: boolean) => void;
}

export const AttackControls = memo(({
    handleAttack, attackStatus, attackMode, setAttackMode, biasKW, setBiasKW, stealthy, setStealthy
}: AttackControlsProps) => (
    <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
            <button
                onClick={() => handleAttack(!attackStatus.active)}
                className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-xl transition-all active:scale-95 shadow-inner",
                    attackStatus.active
                        ? "bg-rose-500/20 text-rose-400 animate-pulse shadow-[0_0_15px_rgba(244,63,94,0.2)]"
                        : "bg-slate-900/50 text-slate-500 hover:text-rose-400 hover:bg-slate-800/80"
                )}
                aria-pressed={attackStatus.active}
            >
                {attackStatus.active ? <ShieldAlert className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
                <span className="text-xs font-black uppercase tracking-widest leading-none">
                    {attackStatus.active ? 'Mitigating Attack' : 'Infect Grid'}
                </span>
            </button>
            <div className="flex items-center gap-1 bg-slate-900/50 px-3 py-2 rounded-xl shadow-inner">
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
                    "w-3 h-3 rounded transition-colors shadow-inner",
                    stealthy ? "bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]" : "bg-slate-800 group-hover:bg-slate-700"
                )} />
                <span className="text-[9px] font-bold text-slate-500 uppercase group-hover:text-indigo-400">Stealth</span>
            </label>
        </div>
    </div>
));

AttackControls.displayName = 'AttackControls';
