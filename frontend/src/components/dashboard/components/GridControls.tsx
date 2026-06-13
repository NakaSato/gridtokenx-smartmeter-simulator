"use client";

import { memo, useState } from 'react';
import { Play, Pause, SkipForward, Square, RotateCcw } from 'lucide-react';
import type { SimulatorStatus, AttackStatus, AttackMode } from '@/lib/types';
import type { SimTimeRange } from '@/lib/api/types';
import { useSimulator } from '@/components/providers/SimulatorProvider';
import { useHmiTheme } from '@/components/providers/HmiThemeProvider';
import './GridControls.hmi.css';

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
    // Process values (MW) for the analog deviation cards.
    totalGenMW?: number;
    totalConsMW?: number;
    totalSurpMW?: number;
    stabilityScore?: number | null;
}

/** datetime-local yields `YYYY-MM-DDTHH:mm`; tag it UTC so replay is locale-stable. */
function localToUtcIso(local: string): string {
    const withSecs = local.length === 16 ? `${local}:00` : local;
    return `${withSecs}+00:00`;
}

function fmtClock(iso?: string): string {
    if (!iso) return '—';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    const date = d.toLocaleString('en-GB', { timeZone: 'UTC', day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
    const time = d.toLocaleString('en-GB', { timeZone: 'UTC', hour: '2-digit', minute: '2-digit', second: '2-digit' });
    return `${date} · ${time} UTC`;
}

function fmtTime(iso?: string): string {
    if (!iso) return '--:--:--';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString('en-GB', { timeZone: 'UTC', hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function fmtWindow(iso?: string): string {
    if (!iso) return '—';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString('en-GB', { timeZone: 'UTC', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) + ' UTC';
}

const clampPct = (n: number) => Math.max(0, Math.min(100, n));

/** Seconds → "Nd HH:MM:SS" (drops day part when < 1 day). */
function fmtDur(secs?: number): string {
    if (secs == null || Number.isNaN(secs)) return '—';
    const s = Math.floor(secs);
    const d = Math.floor(s / 86400);
    const h = Math.floor((s % 86400) / 3600);
    const m = Math.floor((s % 3600) / 60);
    const ss = s % 60;
    const pad = (n: number) => String(n).padStart(2, '0');
    const hms = `${pad(h)}:${pad(m)}:${pad(ss)}`;
    return d > 0 ? `${d}d ${hms}` : hms;
}

/** Run-window options: a preset length, an explicit end, or open-ended. */
type WindowMode = SimTimeRange | 'custom' | 'open';

const WINDOW_OPTIONS: { value: WindowMode; label: string }[] = [
    { value: 'open', label: 'Open-ended' },
    { value: 'hour', label: '1 hour' },
    { value: 'day', label: '1 day' },
    { value: 'week', label: '1 week' },
    { value: 'month', label: '1 month' },
    { value: 'year', label: '1 year' },
    { value: 'custom', label: 'Custom end' },
];

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
    totalGenMW = 0,
    totalConsMW = 0,
    totalSurpMW = 0,
    stabilityScore = null,
}: GridControlsProps) => {
    const { startDeterministic } = useSimulator();
    const { theme } = useHmiTheme();

    // Deterministic run config (mirrors the start-deterministic contract).
    const [seed, setSeed] = useState(42);
    const [startTime, setStartTime] = useState('2026-06-10T08:00');
    const [windowMode, setWindowMode] = useState<WindowMode>('day');
    const [endTime, setEndTime] = useState('2026-06-11T08:00');
    const [intervalSecs, setIntervalSecs] = useState(900);
    const [numMeters, setNumMeters] = useState('');
    const [autostart, setAutostart] = useState(true);
    const [busy, setBusy] = useState(false);

    // Send exactly one of: a time_range preset, an explicit end_time, or
    // nothing (open-ended) — never both.
    const windowPayload = () => {
        if (windowMode === 'open') return {};
        if (windowMode === 'custom') return endTime ? { end_time: localToUtcIso(endTime) } : {};
        return { time_range: windowMode };
    };

    const launchDeterministic = async () => {
        setBusy(true);
        try {
            await startDeterministic({
                seed,
                start_time: startTime ? localToUtcIso(startTime) : undefined,
                ...windowPayload(),
                interval: intervalSecs,
                ...(numMeters ? { num_meters: parseInt(numMeters, 10) } : {}),
                autostart,
            });
        } finally {
            setBusy(false);
        }
    };

    // Run state derivation.
    const runLabel = status.running ? (status.paused ? 'Paused' : 'Running') : 'Idle';
    const runClass = status.running ? (status.paused ? 'paused' : '') : 'idle';
    const runId = status.run_id ?? `seed${status.seed ?? seed}-i${status.interval_seconds ?? intervalSecs}-m${status.num_meters}`;

    // Net flow: negative = import (advisory).
    const isImport = totalSurpMW < 0;

    // Analog bar geometry (full-scale 0.5 MW gen/cons, ±0.25 MW net).
    const genFill = clampPct((totalGenMW / 0.5) * 100);
    const consFill = clampPct((totalConsMW / 0.5) * 100);
    const netFill = clampPct((Math.abs(totalSurpMW) / 0.25) * 50);
    const hasStab = stabilityScore != null;
    const stabFill = hasStab ? clampPct(stabilityScore) : 0;
    const stabState = !hasStab ? 'nodata' : stabilityScore >= 95 ? 'ok' : stabilityScore >= 90 ? 'warn' : 'alarm';

    return (
        <section className="hmi" data-theme={theme} aria-label="Grid operations console">

            {/* Status bar */}
            <div className="hmi-bar">
                <span className="brand">GRIDTOKENX</span>
                <span className="sub">Real-Time Grid</span>
                <span className="spacer" />
                <span className="stat">
                    <span className={`dot${isConnected ? '' : ' alarm'}`} />
                    {isConnected ? 'Telemetry Live' : 'Telemetry Offline'}
                </span>
                {isImport && (
                    <span className="stat"><span className="dot warn" />1 Advisory</span>
                )}
                <span className="clock mono">{fmtClock(status.sim_time)}</span>
            </div>

            <div className="hmi-grid">

                {/* LEFT: simulation & fleet */}
                <div className="panel">
                    <div className="panel-hd">
                        <span className="t">Simulation &amp; Fleet</span>
                        <span className="meta mono">{runId}</span>
                    </div>
                    <div className="panel-bd">

                        {/* Tier 1 — live run state */}
                        <div className="run-state">
                            <div className="rs-main">
                                <span className={`rs-badge ${runClass}`}>
                                    <span className="rs-pulse" />{runLabel}
                                </span>
                                <span className="rs-clock mono">
                                    {fmtTime(status.sim_time)}<span className="rs-clock-d">UTC · sim</span>
                                </span>
                            </div>
                            <div className="rs-prog">
                                <div className="rs-prog-fill" style={{ width: status.running ? '100%' : '0%' }} />
                                <span className="rs-prog-tick mono">
                                    {status.deterministic ? `seed ${status.seed ?? '—'}` : status.mode} · {status.interval_seconds ?? intervalSecs}s
                                </span>
                            </div>
                        </div>

                        {/* Tier 2 — transport */}
                        <div className="sec">
                            <div className="sec-lbl">Transport</div>
                            <div className="transport" role="group" aria-label="Simulation transport">
                                <div className="t-group">
                                    {status.paused ? (
                                        <button type="button" className="btn icon run" title="Resume" aria-label="Resume" onClick={() => handleControl('resume')}><Play className="w-4 h-4" /></button>
                                    ) : (
                                        <button type="button" className="btn icon run" title="Pause" aria-label="Pause" disabled={!status.running} onClick={() => handleControl('pause')}><Pause className="w-4 h-4" /></button>
                                    )}
                                    <button type="button" className="btn icon" title="Step forward" aria-label="Step forward" onClick={() => handleControl('step')}><SkipForward className="w-4 h-4" /></button>
                                </div>
                                <div className="t-group">
                                    <button type="button" className="btn icon danger" title="Stop" aria-label="Stop" disabled={!status.running} onClick={() => handleControl('stop')}><Square className="w-4 h-4" /></button>
                                    <button type="button" className="btn icon" title="Restart" aria-label="Restart" onClick={() => handleControl('restart')}><RotateCcw className="w-4 h-4" /></button>
                                </div>
                                <span className="t-spacer" />
                                <button type="button" className="btn primary lg" disabled={status.running} onClick={() => handleControl('start')}>Launch</button>
                            </div>
                        </div>

                        {/* Tier 3 — deterministic run window */}
                        <div className="sec">
                            <div className="sec-lbl">Deterministic run</div>
                            <div className="win">
                                <div className="win-field">
                                    <label className="cfg-k" htmlFor="winStart">Start (UTC)</label>
                                    <input id="winStart" className="dt" type="datetime-local" step={60}
                                        value={startTime} onChange={(e) => setStartTime(e.target.value)} />
                                </div>
                                <div className="win-field">
                                    <label className="cfg-k" htmlFor="winSeed">Seed</label>
                                    <input id="winSeed" className="dt" type="number" style={{ width: 72 }}
                                        value={seed} onChange={(e) => setSeed(parseInt(e.target.value, 10) || 0)} />
                                </div>
                                <div className="win-field">
                                    <label className="cfg-k" htmlFor="winMeters">Meters</label>
                                    <input id="winMeters" className="dt" type="number" placeholder="auto" min={1} style={{ width: 72 }}
                                        value={numMeters} onChange={(e) => setNumMeters(e.target.value)} />
                                </div>
                                <div className="win-field">
                                    <label className="cfg-k" htmlFor="winWindow">Window</label>
                                    <select id="winWindow" className="dt" value={windowMode}
                                        onChange={(e) => setWindowMode(e.target.value as WindowMode)}>
                                        {WINDOW_OPTIONS.map((o) => (
                                            <option key={o.value} value={o.value}>{o.label}</option>
                                        ))}
                                    </select>
                                </div>
                                {windowMode === 'custom' && (
                                    <div className="win-field">
                                        <label className="cfg-k" htmlFor="winEnd">End (UTC)</label>
                                        <input id="winEnd" className="dt" type="datetime-local" step={60}
                                            value={endTime} onChange={(e) => setEndTime(e.target.value)} />
                                    </div>
                                )}
                                <div className="win-presets" role="group" aria-label="Interval presets">
                                    {[300, 900, 1800].map((s) => (
                                        <button key={s} type="button"
                                            className={`chip${intervalSecs === s ? ' active' : ''}`}
                                            onClick={() => setIntervalSecs(s)}>
                                            {s}s
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="win-derived">
                                <span className="wd-item"><span className="wd-k">Interval</span><span className="wd-v mono">{intervalSecs} s/tick</span></span>
                                <label className="wd-item" style={{ cursor: 'pointer' }}>
                                    <span className="wd-k">Autostart</span>
                                    <span className="wd-v" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <input type="checkbox" checked={autostart} onChange={(e) => setAutostart(e.target.checked)} />
                                        {autostart ? 'on' : 'off'}
                                    </span>
                                </label>
                                <button type="button" className="btn primary" style={{ marginLeft: 'auto' }} disabled={busy} onClick={launchDeterministic}>
                                    {busy ? 'Launching…' : 'Launch run'}
                                </button>
                            </div>
                        </div>

                        {/* Tier 3b — live configuration */}
                        <div className="sec">
                            <div className="sec-lbl">Configuration</div>
                            <div className="cfg">
                                <div className="cfg-cell wide">
                                    <span className="cfg-k">Mode</span>
                                    <span className={`cfg-v${status.deterministic ? ' ok' : ''}`}>
                                        {status.deterministic ? `Deterministic · seed ${status.seed ?? '—'}` : (status.mode || 'standalone')}
                                    </span>
                                </div>
                                <div className="cfg-cell wide">
                                    <span className="cfg-k">Interval</span>
                                    <span className="cfg-v mono">{status.interval_seconds ?? intervalSecs} s</span>
                                </div>
                                {status.end_time && (
                                    <div className="cfg-cell wide">
                                        <span className="cfg-k">Window end</span>
                                        <span className="cfg-v mono">{fmtTime(status.end_time)} UTC</span>
                                    </div>
                                )}
                                <div className="cfg-cell wide">
                                    <span className="cfg-k">Weather</span>
                                    <span className="cfg-v mono">{status.weather_mode || 'auto'}</span>
                                </div>
                                <div className="cfg-cell wide">
                                    <span className="cfg-k">Meters</span>
                                    <span className="cfg-v mono">{status.num_meters} active</span>
                                </div>
                            </div>
                        </div>

                        {/* Tier 3c — fleet sizing */}
                        <div className="sec">
                            <div className="sec-lbl">Fleet config</div>
                            <div className="win">
                                <div className="win-field">
                                    <label className="cfg-k" htmlFor="fleetCount">Fleet size</label>
                                    <input id="fleetCount" className="dt" type="number" min={1} max={10000} style={{ width: 84 }}
                                        value={meterCount} onChange={(e) => setMeterCount(parseInt(e.target.value, 10) || 20)} />
                                </div>
                                <div className="win-field">
                                    <label className="cfg-k" htmlFor="genMin">Gen min</label>
                                    <input id="genMin" className="dt" type="number" style={{ width: 64 }}
                                        value={genMin} onChange={(e) => setGenMin(parseFloat(e.target.value) || 0)} />
                                </div>
                                <div className="win-field">
                                    <label className="cfg-k" htmlFor="genMax">Gen max</label>
                                    <input id="genMax" className="dt" type="number" style={{ width: 64 }}
                                        value={genMax} onChange={(e) => setGenMax(parseFloat(e.target.value) || 0)} />
                                </div>
                                <button type="button" className="btn" style={{ alignSelf: 'flex-end' }} onClick={updateMeters}>Apply fleet</button>
                            </div>
                        </div>

                        {/* Tier 4 — reference metadata */}
                        <div className="ref">
                            <div className="ref-row"><span className="ref-k">Run ID</span><span className="ref-v mono">{runId}</span></div>
                            <div className="ref-row"><span className="ref-k">Start</span><span className="ref-v mono">{fmtWindow(status.start_time)}</span></div>
                            <div className="ref-row"><span className="ref-k">Sim clock</span><span className="ref-v mono">{fmtWindow(status.sim_time)}</span></div>
                            <div className="ref-row"><span className="ref-k">Ticks</span><span className="ref-v mono">{status.tick_count ?? '—'}</span></div>
                            <div className="ref-row"><span className="ref-k">Sim elapsed</span><span className="ref-v mono">{fmtDur(status.sim_elapsed_seconds)}</span></div>
                            <div className="ref-row"><span className="ref-k">Runtime</span><span className="ref-v mono">{fmtDur(status.runtime_seconds)}</span></div>
                            <div className="ref-row"><span className="ref-k">Fleet online</span><span className="ref-v mono">{status.num_meters} / {status.num_meters} meters</span></div>
                        </div>

                    </div>
                </div>

                {/* RIGHT: grid integrity / fault injection */}
                <div className="panel">
                    <div className="panel-hd">
                        <span className="t">Grid Integrity</span>
                        <span className="meta">Fault Injection</span>
                    </div>
                    <div className="panel-bd">

                        <div className="fi-warn">⚠ Fault injection alters telemetry — sandbox runs only</div>

                        <div className="integ-list">
                            <div className="integ-row">
                                <span className="n">Inject fault</span>
                                <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <span className={`tag${attackStatus.active ? ' armed' : ''}`}>Type · {String(attackMode).toUpperCase()}</span>
                                    <select className="sel-field" aria-label="Fault type"
                                        value={attackMode} onChange={(e) => setAttackMode(e.target.value as AttackMode)}>
                                        <option value="bias">BIAS</option>
                                        <option value="scale">SCALE</option>
                                        <option value="random">RANDOM</option>
                                    </select>
                                    <button
                                        type="button"
                                        className={`btn ${attackStatus.active ? 'active' : 'danger'}`}
                                        onClick={() => handleAttack(!attackStatus.active)}
                                        aria-pressed={attackStatus.active}>
                                        {attackStatus.active ? 'Mitigate' : 'Arm'}
                                    </button>
                                </span>
                            </div>
                            <div className="integ-row">
                                <span className="n">Bias magnitude</span>
                                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <input className="num-field mono" type="number" step={0.1} aria-label="Bias magnitude (kW)"
                                        value={biasKW} onChange={(e) => setBiasKW(parseFloat(e.target.value) || 0)} />
                                    <span className="vv">kW</span>
                                </span>
                            </div>
                            <div className="integ-row">
                                <span className="n">Stealth mode</span>
                                <button type="button" className={`tag${stealthy ? ' armed' : ''}`} style={{ cursor: 'pointer', background: 'none' }}
                                    onClick={() => setStealthy(!stealthy)} aria-pressed={stealthy}>
                                    {stealthy ? 'On' : 'Off'}
                                </button>
                            </div>
                            <div className="integ-row">
                                <span className="n">Replay-protection</span>
                                <span className={`tag${isConnected ? ' ok' : ''}`}>{isConnected ? 'Verified' : 'Unknown'}</span>
                            </div>
                            <div className="integ-row">
                                <span className="n">Oracle signatures (Ed25519)</span>
                                <span className="vv">{status.num_meters} / {status.num_meters} valid</span>
                            </div>
                            <div className="integ-row">
                                <span className="n">Last attestation</span>
                                <span className="vv">{fmtTime(status.sim_time)} UTC</span>
                            </div>
                        </div>

                    </div>
                </div>
            </div>

            {/* Process values */}
            <div className="pv-row">
                <div className="pv">
                    <div className="pv-lbl"><span>Grid Generation</span><span className="pv-state">NORM</span></div>
                    <div className="pv-num"><span className="v mono">{totalGenMW.toFixed(3)}</span><span className="u">MW</span></div>
                    <div className="bar">
                        <div className="band" style={{ left: '20%', width: '60%' }} />
                        <div className="fill" style={{ width: `${genFill}%` }} />
                        <div className="sp" style={{ left: '50%' }} />
                    </div>
                    <div className="bar-scale"><span>0</span><span>SP 0.25</span><span>0.50</span></div>
                </div>

                <div className="pv">
                    <div className="pv-lbl"><span>Grid Consumption</span><span className="pv-state">NORM</span></div>
                    <div className="pv-num"><span className="v mono">{totalConsMW.toFixed(3)}</span><span className="u">MW</span></div>
                    <div className="bar">
                        <div className="band" style={{ left: '20%', width: '60%' }} />
                        <div className="fill" style={{ width: `${consFill}%` }} />
                        <div className="sp" style={{ left: '50%' }} />
                    </div>
                    <div className="bar-scale"><span>0</span><span>SP 0.25</span><span>0.50</span></div>
                </div>

                <div className="pv">
                    <div className="pv-lbl"><span>Net Flow</span><span className={`pv-state ${isImport ? 'warn' : 'ok'}`}>{isImport ? 'IMPORT' : 'EXPORT'}</span></div>
                    <div className="pv-num"><span className={`v mono${isImport ? ' warn' : ''}`}>{totalSurpMW >= 0 ? '+' : '−'}{Math.abs(totalSurpMW).toFixed(3)}</span><span className="u">MW</span></div>
                    <div className="bar bi">
                        <div className="zero" />
                        {isImport
                            ? <div className="fill warn" style={{ right: '50%', width: `${netFill}%` }} />
                            : <div className="fill" style={{ left: '50%', width: `${netFill}%` }} />}
                    </div>
                    <div className="bar-scale"><span>−0.25 import</span><span>0</span><span>+0.25 export</span></div>
                </div>

                <div className="pv">
                    <div className="pv-lbl"><span>Stability Score</span><span className={`pv-state ${stabState}`}>{!hasStab ? 'NO DATA' : stabState === 'ok' ? 'STABLE' : stabState === 'warn' ? 'WATCH' : 'ALARM'}</span></div>
                    <div className="pv-num"><span className={`v mono${hasStab && stabState === 'ok' ? '' : ` ${stabState}`}`}>{hasStab ? stabilityScore.toFixed(1) : '—'}</span><span className="u">%</span></div>
                    <div className="bar">
                        <div className="band" style={{ left: '95%', width: '5%' }} />
                        {hasStab && <div className={`fill${stabState === 'ok' ? '' : ` ${stabState}`}`} style={{ width: `${stabFill}%` }} />}
                        <div className="sp" style={{ left: '95%' }} />
                    </div>
                    <div className="bar-scale"><span>90</span><span>Lo-lim 95</span><span>100</span></div>
                </div>
            </div>
        </section>
    );
});

GridControls.displayName = 'GridControls';
