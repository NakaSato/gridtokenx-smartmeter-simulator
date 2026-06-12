"use client";

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
import { Activity } from "lucide-react";
import { Card } from "@/components/ui/card";
import type { MeterSummary, RunSeriesPoint } from "@/lib/api/types";

/** ISO timestamp -> HH:mm for the time axis. */
const hhmm = (iso: string) => (iso.includes("T") ? iso.slice(11, 16) : iso);

const TOOLTIP_STYLE = {
    background: "#0f172a",
    border: "1px solid #334155",
    borderRadius: 8,
    fontSize: 12,
} as const;

interface RunChartsProps {
    agg: RunSeriesPoint[];
    meterSeries: RunSeriesPoint[];
    loading: boolean;
    meters: MeterSummary[];
    meterId: string;
    onMeterChange: (meterId: string) => void;
}

/**
 * Recharts-backed plots for a deterministic run. Split out of the page and
 * loaded via `next/dynamic` so the heavy recharts bundle stays out of the
 * initial `/run` chunk.
 */
export default function RunCharts({
    agg,
    meterSeries,
    loading,
    meters,
    meterId,
    onMeterChange,
}: RunChartsProps) {
    const aggData = agg.map((p) => ({ ...p, t: hhmm(p.time) }));
    const meterData = meterSeries.map((p) => ({ ...p, t: hhmm(p.time) }));

    return (
        <>
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
                            <Tooltip contentStyle={TOOLTIP_STYLE} />
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
                            <Tooltip contentStyle={TOOLTIP_STYLE} />
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
                        onChange={(e) => onMeterChange(e.target.value)}
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
                                <Tooltip contentStyle={TOOLTIP_STYLE} />
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
        </>
    );
}
