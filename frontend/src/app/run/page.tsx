"use client";

import { useCallback, useEffect, useState } from "react";
import {
    Area,
    AreaChart,
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { Activity, Dices, RefreshCw } from "lucide-react";
import { useSimulatorApi } from "@/hooks/useSimulatorApi";
import { Card } from "@/components/ui/card";
import type { MeterSummary, RunSeriesPoint } from "@/lib/api/types";

/** ISO timestamp -> HH:mm for the time axis. */
const hhmm = (iso: string) => (iso.includes("T") ? iso.slice(11, 16) : iso);

export default function RunPage() {
    const api = useSimulatorApi();

    const [runs, setRuns] = useState<string[]>([]);
    const [runId, setRunId] = useState<string>("");
    const [agg, setAgg] = useState<RunSeriesPoint[]>([]);
    const [meters, setMeters] = useState<MeterSummary[]>([]);
    const [meterId, setMeterId] = useState<string>("");
    const [meterSeries, setMeterSeries] = useState<RunSeriesPoint[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    // Initial load: current run id, the run list, and the meter roster.
    const bootstrap = useCallback(async () => {
        setError(null);
        try {
            const [current, runList, meterList] = await Promise.all([
                api.getCurrentRun(),
                api.listRuns(),
                api.listMeters({ limit: 1000 }),
            ]);
            const list = runList?.runs ?? [];
            setRuns(list);
            setMeters(meterList?.meters ?? []);
            setRunId((prev) => prev || current?.run_id || list[0] || "");
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }, [api]);

    useEffect(() => {
        bootstrap();
    }, [bootstrap]);

    // Fleet aggregate series for the selected run.
    useEffect(() => {
        if (!runId) return;
        let cancelled = false;
        (async () => {
            setLoading(true);
            setError(null);
            try {
                const res = await api.getRunSeries({ run_id: runId });
                if (!cancelled) setAgg(res?.series ?? []);
            } catch (e) {
                if (!cancelled) setError(e instanceof Error ? e.message : String(e));
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [api, runId]);

    // Per-meter drilldown series.
    useEffect(() => {
        if (!runId || !meterId) {
            setMeterSeries([]);
            return;
        }
        let cancelled = false;
        (async () => {
            try {
                const res = await api.getRunSeries({ run_id: runId, meter_id: meterId });
                if (!cancelled) setMeterSeries(res?.series ?? []);
            } catch (e) {
                if (!cancelled) setError(e instanceof Error ? e.message : String(e));
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [api, runId, meterId]);

    const aggData = agg.map((p) => ({ ...p, t: hhmm(p.time) }));
    const meterData = meterSeries.map((p) => ({ ...p, t: hhmm(p.time) }));

    return (
        <main className="mx-auto max-w-6xl space-y-6 p-6">
            <header className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <div className="rounded-xl bg-violet-500/15 p-2 text-violet-400">
                        <Dices className="h-5 w-5" />
                    </div>
                    <div>
                        <h1 className="text-xl font-black text-white">Deterministic Run Plots</h1>
                        <p className="text-xs text-slate-500">InfluxDB time-series for a seeded run</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <label htmlFor="run-select" className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                        Run
                    </label>
                    <select
                        id="run-select"
                        value={runId}
                        onChange={(e) => setRunId(e.target.value)}
                        className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 font-mono text-xs text-slate-200 outline-none focus:border-violet-500/50"
                    >
                        {runs.length === 0 && <option value="">No runs yet</option>}
                        {runs.map((r) => (
                            <option key={r} value={r}>
                                {r}
                            </option>
                        ))}
                    </select>
                    <button
                        type="button"
                        onClick={bootstrap}
                        aria-label="Refresh runs"
                        className="rounded-lg border border-white/10 p-2 text-slate-400 transition-colors hover:bg-white/5 hover:text-slate-100"
                    >
                        <RefreshCw className="h-4 w-4" />
                    </button>
                </div>
            </header>

            {error && (
                <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs font-bold text-rose-300">
                    {error}
                </div>
            )}

            {/* Fleet aggregate: generation vs consumption */}
            <Card className="gap-3 border-white/10 bg-slate-950/60 p-5">
                <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4 text-emerald-400" />
                    <h2 className="text-[11px] font-black uppercase tracking-widest text-slate-300">
                        Fleet Energy — generated vs consumed (kWh / tick)
                    </h2>
                    {loading && <span className="text-[10px] text-slate-500">loading…</span>}
                </div>
                <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={aggData}>
                            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                            <XAxis dataKey="t" stroke="#475569" fontSize={10} />
                            <YAxis stroke="#475569" fontSize={10} />
                            <Tooltip
                                contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }}
                            />
                            <Legend wrapperStyle={{ fontSize: 11 }} />
                            <Area type="monotone" dataKey="energy_generated" name="Generated" stroke="#10b981" fill="#10b98133" />
                            <Area type="monotone" dataKey="energy_consumed" name="Consumed" stroke="#f43f5e" fill="#f43f5e33" />
                            <Line type="monotone" dataKey="net" name="Net" stroke="#818cf8" dot={false} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </Card>

            {/* Fleet frequency */}
            <Card className="gap-3 border-white/10 bg-slate-950/60 p-5">
                <h2 className="text-[11px] font-black uppercase tracking-widest text-slate-300">System Frequency (Hz)</h2>
                <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={aggData}>
                            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                            <XAxis dataKey="t" stroke="#475569" fontSize={10} />
                            <YAxis stroke="#475569" fontSize={10} domain={["auto", "auto"]} />
                            <Tooltip
                                contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }}
                            />
                            <Line type="monotone" dataKey="frequency" name="Frequency" stroke="#fbbf24" dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </Card>

            {/* Per-meter drilldown */}
            <Card className="gap-3 border-white/10 bg-slate-950/60 p-5">
                <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-[11px] font-black uppercase tracking-widest text-slate-300">Per-meter drilldown</h2>
                    <label htmlFor="meter-select" className="sr-only">
                        Meter
                    </label>
                    <select
                        id="meter-select"
                        value={meterId}
                        onChange={(e) => setMeterId(e.target.value)}
                        className="rounded-lg border border-white/10 bg-slate-900 px-3 py-1.5 font-mono text-xs text-slate-200 outline-none focus:border-violet-500/50"
                    >
                        <option value="">Select a meter…</option>
                        {meters.map((m) => (
                            <option key={m.meter_id} value={m.meter_id}>
                                {m.meter_id.slice(0, 8)} · {m.meter_type ?? "?"}
                            </option>
                        ))}
                    </select>
                </div>
                {meterId ? (
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={meterData}>
                                <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                                <XAxis dataKey="t" stroke="#475569" fontSize={10} />
                                <YAxis yAxisId="kwh" stroke="#475569" fontSize={10} />
                                <YAxis yAxisId="v" orientation="right" stroke="#475569" fontSize={10} domain={["auto", "auto"]} />
                                <Tooltip
                                    contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }}
                                />
                                <Legend wrapperStyle={{ fontSize: 11 }} />
                                <Area yAxisId="kwh" type="monotone" dataKey="energy_generated" name="Generated" stroke="#10b981" fill="#10b98133" />
                                <Area yAxisId="kwh" type="monotone" dataKey="energy_consumed" name="Consumed" stroke="#f43f5e" fill="#f43f5e33" />
                                <Line yAxisId="v" type="monotone" dataKey="voltage" name="Voltage" stroke="#38bdf8" dot={false} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <p className="py-8 text-center text-xs text-slate-600">Pick a meter to plot its gen/con/voltage.</p>
                )}
            </Card>
        </main>
    );
}
