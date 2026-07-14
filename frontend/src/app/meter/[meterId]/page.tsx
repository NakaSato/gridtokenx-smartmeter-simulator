"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Activity } from 'lucide-react';
import { useSimulatorApi } from '@/hooks/useSimulatorApi';
import type { MeterSummary, MeterReading, MeterBill, RunSeriesPoint, CarbonOffset } from '@/lib/api/types';

const HISTORY_CAP = 240; // ~20 min of live polling at 5s, or a full persisted run.

type ChartPoint = { time: string; generation: number; consumption: number };

const fmt = (n: number, d = 2) =>
    n.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });

// Build the HMI line chart as SVG paths from real gen/cons series.
function EnergyChart({ data }: { data: ChartPoint[] }) {
    const W = 960, H = 320, pad = { l: 40, r: 12, t: 14, b: 26 };
    const N = data.length;
    if (N < 2) {
        return <div className="chart-empty">No readings yet — start the simulation</div>;
    }

    const gen = data.map((p) => Math.max(0, p.generation));
    const cons = data.map((p) => Math.max(0, p.consumption));
    const maxV = Math.max(...gen, ...cons, 0.001);
    const ymax = maxV * 1.1;

    const X = (i: number) => pad.l + (i / (N - 1)) * (W - pad.l - pad.r);
    const Y = (v: number) => pad.t + (1 - v / ymax) * (H - pad.t - pad.b);
    const path = (arr: number[]) =>
        arr.map((v, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)} ${Y(v).toFixed(1)}`).join(' ');

    const yticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * ymax);
    const labelCount = Math.min(8, N);
    const xticks = Array.from({ length: labelCount }, (_, k) => {
        const i = Math.round((k / (labelCount - 1)) * (N - 1));
        return { i, label: data[i].time };
    });

    return (
        <svg
            className="chart"
            viewBox={`0 0 ${W} ${H}`}
            preserveAspectRatio="none"
            role="img"
            aria-label="Generation and consumption over time"
        >
            {yticks.map((yv, k) => {
                const y = Y(yv);
                return (
                    <g key={`y${k}`}>
                        <line className="gl" x1={pad.l} y1={y} x2={W - pad.r} y2={y} />
                        <text className="tk" x={pad.l - 6} y={y + 3} textAnchor="end">
                            {yv.toFixed(2).replace(/\.00$/, '')}
                        </text>
                    </g>
                );
            })}
            {xticks.map(({ i, label }, k) => {
                const anc = k === 0 ? 'start' : k === xticks.length - 1 ? 'end' : 'middle';
                return (
                    <text key={`x${k}`} className="tk" x={X(i)} y={H - 8} textAnchor={anc}>
                        {label}
                    </text>
                );
            })}
            <line className="axis" x1={pad.l} y1={Y(0)} x2={W - pad.r} y2={Y(0)} />
            <path className="ln-cons" d={path(cons)} />
            <path className="ln-gen" d={path(gen)} />
        </svg>
    );
}

const MeterDetails = () => {
    const { meterId } = useParams<{ meterId: string }>();
    const router = useRouter();
    const api = useSimulatorApi();

    const [metadata, setMetadata] = useState<MeterSummary | null>(null);
    const [readings, setReadings] = useState<MeterReading[]>([]);
    const [series, setSeries] = useState<RunSeriesPoint[]>([]);
    const [bill, setBill] = useState<MeterBill | null>(null);
    const [carbon, setCarbon] = useState<CarbonOffset | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    // Copy the canonical meter_id (dashes intact) even though the UI shows it
    // dash-stripped, so pasted IDs stay usable against the API/other services.
    const handleCopyId = useCallback(async (id: string) => {
        try {
            await navigator.clipboard.writeText(id);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    }, []);

    // Live history buffer: the readings endpoint only returns the latest tick,
    // so when no deterministic run is persisted we accumulate ticks here across
    // polls (deduped by timestamp) to build a rolling per-meter time-series.
    const liveBuffer = useRef<ChartPoint[]>([]);
    const lastStamp = useRef<string | null>(null);

    // The App Router reuses this component across /meter/[id] param changes, so
    // the buffer refs survive a meter→meter navigation. Clear them when the
    // meter changes (during render, not in an effect) so the Live chart never
    // mixes the previous meter's ticks into the new one's series.
    const [prevMeterId, setPrevMeterId] = useState(meterId);
    if (meterId !== prevMeterId) {
        setPrevMeterId(meterId);
        liveBuffer.current = [];
        lastStamp.current = null;
    }

    const fetchData = useCallback(async () => {
        if (!meterId) return;
        try {
            const [meta, hist, runSeries, meterBill, meterCarbon] = await Promise.all([
                api.getMeter(meterId),
                api.getMeterReadings(meterId, 50),
                // Real persisted history for this meter (Influx deterministic run).
                api.getRunSeries({ meter_id: meterId }).catch(() => null),
                api.getMeterBill(meterId).catch(() => null),
                api.getMeterCarbon(meterId).catch(() => null),
            ]);
            setMetadata(meta);
            const latestReadings = hist?.readings ?? [];
            setReadings(latestReadings);
            setSeries(runSeries?.series ?? []);
            setBill(meterBill);
            setCarbon(meterCarbon);

            // Accumulate the newest tick into the live buffer (fallback history).
            const newest = latestReadings[0];
            if (newest && newest.timestamp !== lastStamp.current) {
                lastStamp.current = newest.timestamp;
                liveBuffer.current = [
                    ...liveBuffer.current,
                    {
                        time: new Date(newest.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                        generation: newest.energy_generated ?? 0,
                        consumption: newest.energy_consumed ?? 0,
                    },
                ].slice(-HISTORY_CAP);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    }, [meterId, api]);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [fetchData]);

    if (loading && !metadata) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    if (error || !metadata) {
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
                <div className="w-16 h-16 bg-rose-500/20 rounded-full flex items-center justify-center mb-4">
                    <Activity className="w-8 h-8 text-rose-500" />
                </div>
                <h2 className="text-2xl font-black text-white mb-2 uppercase">Meter Not Found</h2>
                <p className="text-slate-400 mb-6">{error || `Could not find data for ${meterId}`}</p>
                <Link href="/map" className="px-6 py-3 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition-colors">
                    Return to Map
                </Link>
            </div>
        );
    }

    // Prefer the persisted deterministic-run series (full history); otherwise
    // fall back to the live buffer accumulated across polls.
    const chartData: ChartPoint[] = series.length > 0
        ? series.map((p) => ({
            time: new Date(p.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            generation: p.energy_generated ?? 0,
            consumption: p.energy_consumed ?? 0,
        }))
        : liveBuffer.current;
    const historySource = series.length > 0 ? 'Persisted run' : 'Live';

    const latest = readings[0];
    const totalGen = readings.reduce((s, r) => s + (r.energy_generated ?? 0), 0);
    const totalCons = readings.reduce((s, r) => s + (r.energy_consumed ?? 0), 0);
    const net = totalGen - totalCons;

    // KPI scalars.
    const latestGen = latest?.energy_generated ?? 0;
    const latestCons = latest?.energy_consumed ?? 0;
    const voltage = latest?.voltage ?? metadata.voltage ?? 0;
    const nomV = metadata.rated_voltage_v ?? 230;
    const pf = latest?.power_factor ?? 0;
    const freq = latest?.frequency ?? 0;

    // Voltage band: ±15% full scale, ±10% in-band window (matches HMI layout).
    const vmin = nomV * 0.85, vmax = nomV * 1.15;
    const vFill = Math.max(0, Math.min(100, ((voltage - vmin) / (vmax - vmin)) * 100));
    const vDev = Math.abs(voltage - nomV) / nomV;
    const vState = vDev > 0.1 ? 'alarm' : vDev > 0.06 ? 'warn' : 'ok';
    const vStateLabel = vState === 'ok' ? 'In band' : vState === 'warn' ? 'Near limit' : 'Out of band';

    // A small bar fill for the gen/cons KPIs, scaled against the larger of the two.
    const kpiScale = Math.max(latestGen, latestCons, 0.001);

    // Net (window): negative = importing (warn), positive = exporting (ok).
    const isImport = net < 0;
    const netMag = Math.min(50, (Math.abs(net) / Math.max(Math.abs(net), 1)) * 50);

    return (
        <>
            {/* Header */}
            <div className="hd">
                    <Link href="/map" className="back" title="Back to fleet" aria-label="Back" onClick={(e) => { if (window.history.length > 1) { e.preventDefault(); router.back(); } }}>‹</Link>
                    <div className="titlewrap">
                        <div className="title">{metadata.location_name ?? metadata.meter_id}</div>
                        <div className="meta">
                            <span
                                className="uuid"
                                onClick={() => handleCopyId(metadata.meter_id)}
                                title="Click to copy ID"
                                style={{ cursor: 'pointer', color: copied ? 'var(--ok)' : undefined }}
                            >
                                {metadata.meter_id.replace(/-/g, '')}
                            </span>
                            <span>BUS {metadata.bus_name ?? '—'} · PHASE {metadata.phase ?? '—'}</span>
                        </div>
                    </div>
                    <div className="badges">
                        {metadata.has_solar && (
                            <span className="bdg pv">{metadata.solar_capacity ?? 0} kW PV</span>
                        )}
                        <span className="bdg type">{metadata.meter_type}</span>
                        <span className="bdg active">{metadata.status ?? 'Active'}</span>
                    </div>
                </div>

                {/* KPI cards */}
                <div className="kpis">
                    <div className="kpi">
                        <div className="top"><span className="lbl">Latest generation</span><span className="st ok">Live</span></div>
                        <div className="num"><span className="v mono">{fmt(latestGen, 3)}</span><span className="u">kWh</span></div>
                        <div className="bar"><div className="fill" style={{ width: `${(latestGen / kpiScale) * 100}%` }} /></div>
                        <div className="sub">Solar · 15-min interval</div>
                    </div>
                    <div className="kpi">
                        <div className="top"><span className="lbl">Latest consumption</span><span className="st ok">Live</span></div>
                        <div className="num"><span className="v mono">{fmt(latestCons, 3)}</span><span className="u">kWh</span></div>
                        <div className="bar"><div className="fill" style={{ width: `${(latestCons / kpiScale) * 100}%` }} /></div>
                        <div className="sub">Load · 15-min interval</div>
                    </div>
                    <div className="kpi">
                        <div className="top"><span className="lbl">Voltage</span><span className={`st ${vState}`}>{vStateLabel}</span></div>
                        <div className="num"><span className={`v mono${vState === 'ok' ? '' : ` ${vState}`}`}>{fmt(voltage, 1)}</span><span className="u">V</span></div>
                        <div className="bar">
                            <div className="band" style={{ left: '16.7%', width: '66.6%' }} />
                            <div className={`fill${vState === 'ok' ? '' : ` ${vState}`}`} style={{ width: `${vFill}%` }} />
                        </div>
                        <div className="sub">PF {fmt(pf, 2)} · {fmt(freq, 1)} Hz · nom {nomV} V ±10%</div>
                    </div>
                    <div className="kpi">
                        <div className="top"><span className="lbl">Net (window)</span><span className={`st ${isImport ? 'warn' : 'ok'}`}>{isImport ? 'Import' : 'Export'}</span></div>
                        <div className="num"><span className={`v mono${isImport ? ' warn' : ''}`}>{net >= 0 ? '+' : '−'}{fmt(Math.abs(net), 3)}</span><span className="u">kWh</span></div>
                        <div className="bar bi">
                            <div className="zero" />
                            <div className={`fill${isImport ? ' warn' : ''}`} style={isImport ? { right: '50%', width: `${netMag}%` } : { left: '50%', width: `${netMag}%` }} />
                        </div>
                        <div className="sub">{readings.length} reading{readings.length === 1 ? '' : 's'} · accumulated</div>
                    </div>
                </div>

                {/* Energy history */}
                <div className="panel">
                    <div className="panel-hd">
                        <span className="t">Energy History</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                            <span className="meta">{historySource} · {chartData.length} pts</span>
                            <span className="legend">
                                <span><span className="sw gen" />Gen</span>
                                <span><span className="sw cons" />Cons</span>
                            </span>
                        </div>
                    </div>
                    <div className="panel-bd">
                        <div className="chart-wrap"><EnergyChart data={chartData} /></div>
                    </div>
                </div>

                {/* Billing */}
                {bill && (
                    <div className="panel">
                        <div className="panel-hd">
                            <span className="t">Energy Trading &amp; Billing</span>
                            <span className="meta">{bill.tariff} · sell @ {fmt(bill.export_rate, 2)} {bill.currency}/kWh</span>
                        </div>
                        <div className="panel-bd">
                            <div className="bill">
                                <div className="bcard">
                                    <div className="lbl">Surplus sold</div>
                                    <div className="num"><span className="v mono">{fmt(bill.export_kwh, 2)}</span><span className="u">kWh</span></div>
                                    <div className="sub"><b>@&nbsp;{fmt(bill.export_rate, 2)}&nbsp;{bill.currency}</b> buy-back</div>
                                </div>
                                <div className="bcard">
                                    <div className="lbl">Export credit</div>
                                    <div className="num"><span className="v mono ok">{fmt(bill.export_credit, 2)}</span><span className="u">{bill.currency}</span></div>
                                    <div className="sub">Sold to grid · revenue</div>
                                </div>
                                <div className="bcard">
                                    <div className="lbl">Import bill</div>
                                    <div className="num"><span className="v mono">{fmt(bill.total, 2)}</span><span className="u">{bill.currency}</span></div>
                                    <div className="sub"><b>{fmt(bill.kwh_total, 1)} kWh</b> · VAT incl.</div>
                                </div>
                                <div className="bcard">
                                    <div className="lbl">Net total</div>
                                    <div className="num"><span className={`v mono ${bill.net_total >= 0 ? 'alarm' : 'ok'}`}>{fmt(Math.abs(bill.net_total), 2)}</span><span className="u">{bill.currency}</span></div>
                                    <div className="sub">{bill.net_total >= 0 ? 'Owed' : 'Credit'} · import − export</div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Carbon */}
                {carbon && (
                    <div className="panel">
                        <div className="panel-hd">
                            <span className="t">Carbon Footprint</span>
                            <span className="meta">grid {fmt(carbon.grid_intensity_kgco2_per_kwh, 3)} · PV {fmt(carbon.solar_intensity_kgco2_per_kwh, 3)} kg/kWh</span>
                        </div>
                        <div className="panel-bd">
                            <div className="bill">
                                <div className="bcard">
                                    <div className="lbl">Grid emissions</div>
                                    <div className="num"><span className="v mono alarm">{fmt(carbon.grid_emissions_kg, 2)}</span><span className="u">kg</span></div>
                                    <div className="sub"><b>{fmt(carbon.import_kwh, 1)} kWh</b> imported</div>
                                </div>
                                <div className="bcard">
                                    <div className="lbl">Offset (net of PV)</div>
                                    <div className="num"><span className="v mono ok">{fmt(carbon.offset_kg, 2)}</span><span className="u">kg</span></div>
                                    <div className="sub"><b>{fmt(carbon.export_kwh, 1)} kWh</b> exported</div>
                                </div>
                                <div className="bcard">
                                    <div className="lbl">Net emissions</div>
                                    <div className="num"><span className={`v mono ${carbon.net_emissions_kg <= 0 ? 'ok' : 'alarm'}`}>{carbon.net_emissions_kg < 0 ? '−' : ''}{fmt(Math.abs(carbon.net_emissions_kg), 2)}</span><span className="u">kg</span></div>
                                    <div className="sub">{carbon.net_emissions_kg <= 0 ? 'Carbon-negative' : 'Net emitter'} · grid − offset</div>
                                </div>
                                <div className="bcard">
                                    <div className="lbl">Trees equivalent</div>
                                    <div className="num"><span className="v mono ok">{fmt(carbon.trees_equivalent, 2)}</span><span className="u">trees</span></div>
                                    <div className="sub">annual CO₂ sequestration</div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
        </>
    );
};

export default MeterDetails;
