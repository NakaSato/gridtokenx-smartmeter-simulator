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
                    "hmi-btn px-4 py-2",
                    attackStatus.active && "alarm"
                )}
                aria-pressed={attackStatus.active}
            >
                {attackStatus.active ? <ShieldAlert className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
                <span className="leading-none">
                    {attackStatus.active ? 'Mitigating Attack' : 'Infect Grid'}
                </span>
            </button>
            <div className="flex items-center gap-1 bg-[var(--panel)] px-1 border border-[var(--line)]">
                <label htmlFor="attackMode" className="sr-only">Attack Mode</label>
                <select
                    id="attackMode"
                    value={attackMode}
                    onChange={(e) => setAttackMode(e.target.value as AttackMode)}
                    className="hmi-input border-0 bg-transparent uppercase"
                >
                    <option value="bias">BIAS</option>
                    <option value="scale">SCALE</option>
                    <option value="random">RANDOM</option>
                </select>
            </div>
        </div>
        <div className="flex items-center gap-4 px-1">
            <div className="flex items-center gap-2">
                <label htmlFor="biasKW" className="hmi-lbl">Bias</label>
                <input
                    id="biasKW"
                    type="number"
                    value={biasKW}
                    onChange={(e) => setBiasKW(parseFloat(e.target.value) || 0)}
                    className="hmi-input mono w-14 px-1 py-0.5"
                    step="0.1"
                />
                <span className="hmi-lbl">kW</span>
            </div>
            <label className="flex items-center gap-1 cursor-pointer group">
                <input
                    type="checkbox"
                    checked={stealthy}
                    onChange={(e) => setStealthy(e.target.checked)}
                    className="sr-only"
                />
                <div className={cn(
                    "w-3 h-3 border border-[var(--line-2)]",
                    stealthy ? "bg-[var(--txt)]" : "bg-[var(--bar-bg)]"
                )} />
                <span className="hmi-lbl">Stealth</span>
            </label>
        </div>
    </div>
));

AttackControls.displayName = 'AttackControls';
