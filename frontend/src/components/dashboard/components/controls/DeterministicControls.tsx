"use client";

import { memo, useState } from 'react';
import { Dices } from 'lucide-react';
import { useSimulator } from '@/components/providers/SimulatorProvider';
import { DateTimePicker } from '@/components/ui/datetime-picker';
import { cn } from '@/lib/common';
import type { SimTimeRange } from '@/lib/api/types';

/** Run-window options: a preset length, an explicit end, or open-ended. */
type WindowMode = SimTimeRange | 'custom' | 'open';

const WINDOW_OPTIONS: { value: WindowMode; label: string }[] = [
    { value: 'open', label: 'Open-ended' },
    { value: 'hour', label: '1 hour' },
    { value: 'day', label: '1 day' },
    { value: 'week', label: '1 week' },
    { value: 'month', label: '1 month' },
    { value: 'year', label: '1 year' },
    { value: 'custom', label: 'Custom end…' },
];

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

/** Render an ISO sim-clock instant as a compact UTC label. */
function fmtSimTime(iso?: string): string {
    if (!iso) return '—';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString('en-GB', { timeZone: 'UTC', year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }) + ' UTC';
}

export const DeterministicControls = memo(() => {
    const { startDeterministic, status } = useSimulator();
    const [seed, setSeed] = useState(42);
    const [startTime, setStartTime] = useState('2026-06-10T08:00:00');
    const [windowMode, setWindowMode] = useState<WindowMode>('day');
    const [endTime, setEndTime] = useState('2026-06-11T08:00:00');
    const [interval, setIntervalSecs] = useState(900);
    const [numMeters, setNumMeters] = useState('');
    const [autostart, setAutostart] = useState(true);
    const [busy, setBusy] = useState(false);

    // The window is sent as exactly one of: a time_range preset, an explicit
    // end_time, or nothing (open-ended) — never both.
    const windowPayload = () => {
        if (windowMode === 'open') return {};
        if (windowMode === 'custom') return endTime ? { end_time: localToUtcIso(endTime) } : {};
        return { time_range: windowMode };
    };

    const launch = async () => {
        setBusy(true);
        try {
            await startDeterministic({
                seed,
                start_time: startTime ? localToUtcIso(startTime) : undefined,
                ...windowPayload(),
                interval,
                ...(numMeters ? { num_meters: parseInt(numMeters, 10) } : {}),
                autostart,
            });
        } finally {
            setBusy(false);
        }
    };

    const inputCls =
        'hmi-input mono px-1 py-0.5 text-center';

    return (
        <div className="flex flex-col gap-1.5 ml-2">
        <div className="flex flex-wrap items-center gap-2 bg-[var(--panel)] px-4 py-2 border border-[var(--line)]">
            <Dices className="w-3 h-3 text-[var(--lbl)]" />
            <span
                className={cn(
                    'hmi-chip flex items-center gap-1.5',
                    status.deterministic && 'ok',
                )}
                title={status.deterministic
                    ? `Deterministic run active (seed ${status.seed ?? '—'})`
                    : 'Not a deterministic run — launch one for byte-identical replay'}
            >
                <span
                    className={cn(
                        'hmi-dot',
                        status.deterministic ? (status.running ? '' : 'warn') : 'off',
                    )}
                />
                Deterministic{status.deterministic ? ' ON' : ' OFF'}
                {status.deterministic && status.seed != null && (
                    <span className="normal-case">· seed {status.seed}</span>
                )}
            </span>
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
                className="h-7 border-[var(--line-2)] bg-[var(--bar-bg)] text-[var(--txt)] hover:bg-[var(--hover)] hover:text-[var(--txt-val)]"
            />
            <select
                aria-label="Run window"
                title="Run window — preset length, explicit end, or open-ended"
                value={windowMode}
                onChange={(e) => setWindowMode(e.target.value as WindowMode)}
                className={`${inputCls} w-28`}
            >
                {WINDOW_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                ))}
            </select>
            {windowMode === 'custom' && (
                <DateTimePicker
                    value={endTime}
                    onChange={setEndTime}
                    aria-label="Sim-clock end (UTC)"
                    className="h-7 border-[var(--line-2)] bg-[var(--bar-bg)] text-[var(--txt)] hover:bg-[var(--hover)] hover:text-[var(--txt-val)]"
                />
            )}
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
            <label className="flex items-center gap-1 hmi-lbl">
                <input
                    type="checkbox"
                    checked={autostart}
                    onChange={(e) => setAutostart(e.target.checked)}
                    className="accent-[var(--lbl)]"
                />
                Run
            </label>
            <button
                type="button"
                onClick={launch}
                disabled={busy}
                className="hmi-btn primary px-2 py-1"
                title="Configure + (re)start a deterministic run"
            >
                {busy ? '…' : 'Launch'}
            </button>
        </div>

        {/* Active deterministic run: pinned sim-clock start + Influx run_id. */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 hmi-lbl">
            <span className="flex items-center gap-1.5">
                <span>Start</span>
                <span className="mono text-[var(--txt-val)]">{fmtSimTime(status.start_time)}</span>
            </span>
            <span className="flex items-center gap-1.5">
                <span>Now</span>
                <span className="mono text-[var(--txt-val)]">{fmtSimTime(status.sim_time)}</span>
            </span>
            {status.end_time && (
                <span className="flex items-center gap-1.5">
                    <span>End</span>
                    <span className="mono text-[var(--txt-val)]">{fmtSimTime(status.end_time)}</span>
                </span>
            )}
            {status.run_id && (
                <span className="flex items-center gap-1.5">
                    <span>Run</span>
                    <span className="mono text-[var(--txt)] normal-case">{status.run_id}</span>
                </span>
            )}
        </div>
        </div>
    );
});

DeterministicControls.displayName = 'DeterministicControls';
