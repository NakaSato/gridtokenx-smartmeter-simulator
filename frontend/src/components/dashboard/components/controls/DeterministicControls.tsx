"use client";

import { memo, useState } from 'react';
import { Dices } from 'lucide-react';
import { useSimulator } from '@/components/providers/SimulatorProvider';
import { DateTimePicker } from '@/components/ui/datetime-picker';

/**
 * Configure + launch a deterministic run via
 * POST /api/v1/simulation/actions/start-deterministic.
 *
 * Same seed + start_time (+ interval/meters/topology) => byte-identical replay.
 * Empty num_meters keeps the current fleet size. Self-contained: pulls
 * startDeterministic from the simulator context rather than prop-drilling.
 */
/**
 * The `datetime-local` picker yields `YYYY-MM-DDTHH:mm` (or `:ss` with step=1).
 * Treat the entered wall-clock as UTC and tag it `+00:00` so the run is
 * timezone-stable regardless of the operator's browser locale — same picked
 * value => same ISO => same deterministic replay.
 */
function localToUtcIso(local: string): string {
    const withSecs = local.length === 16 ? `${local}:00` : local;
    return `${withSecs}+00:00`;
}

export const DeterministicControls = memo(() => {
    const { startDeterministic } = useSimulator();
    const [seed, setSeed] = useState(42);
    const [startTime, setStartTime] = useState('2026-06-10T08:00:00');
    const [interval, setIntervalSecs] = useState(900);
    const [numMeters, setNumMeters] = useState('');
    const [autostart, setAutostart] = useState(true);
    const [busy, setBusy] = useState(false);

    const launch = async () => {
        setBusy(true);
        try {
            await startDeterministic({
                seed,
                start_time: startTime ? localToUtcIso(startTime) : undefined,
                interval,
                ...(numMeters ? { num_meters: parseInt(numMeters, 10) } : {}),
                autostart,
            });
        } finally {
            setBusy(false);
        }
    };

    const inputCls =
        'bg-transparent text-[10px] font-black text-slate-300 outline-none text-center border border-white/10 rounded px-1 py-0.5 focus:border-violet-400/50';

    return (
        <div className="flex flex-wrap items-center gap-2 bg-slate-900/50 px-4 py-2 rounded-xl ml-2 shadow-inner">
            <Dices className="w-3 h-3 text-violet-400" />
            <span className="text-[9px] uppercase font-black text-slate-500 tracking-widest">Deterministic</span>
            <input
                type="number"
                aria-label="RNG seed"
                title="RNG seed"
                value={seed}
                onChange={(e) => setSeed(parseInt(e.target.value, 10) || 0)}
                className={`${inputCls} w-12`}
            />
            <DateTimePicker
                value={startTime}
                onChange={setStartTime}
                aria-label="Sim-clock start (UTC)"
                className="h-7 border-white/10 bg-transparent text-slate-300 hover:bg-white/5 hover:text-slate-100"
            />
            <input
                type="number"
                aria-label="Tick interval (seconds)"
                title="Tick interval (seconds)"
                value={interval}
                onChange={(e) => setIntervalSecs(parseInt(e.target.value, 10) || 1)}
                className={`${inputCls} w-12`}
                min="1"
            />
            <input
                type="number"
                aria-label="Fleet size (blank = keep current)"
                title="Fleet size (blank = keep current)"
                value={numMeters}
                onChange={(e) => setNumMeters(e.target.value)}
                className={`${inputCls} w-12`}
                placeholder="auto"
                min="1"
            />
            <label className="flex items-center gap-1 text-[9px] font-black text-slate-400 uppercase tracking-widest">
                <input
                    type="checkbox"
                    checked={autostart}
                    onChange={(e) => setAutostart(e.target.checked)}
                    className="accent-violet-500"
                />
                Run
            </label>
            <button
                type="button"
                onClick={launch}
                disabled={busy}
                className="px-2 py-1 rounded bg-violet-500/20 text-violet-300 text-[9px] font-black uppercase tracking-widest hover:bg-violet-500/30 transition-colors disabled:opacity-40"
                title="Configure + (re)start a deterministic run"
            >
                {busy ? '…' : 'Launch'}
            </button>
        </div>
    );
});

DeterministicControls.displayName = 'DeterministicControls';
