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

// HMI dark-theme hex (recharts inline props can't read CSS vars).
const GRID = "#2c3034";
const AXIS = "#3a3f44";
const TEXT = "#cfd3d7";
const GEN = "#d8932e";
const CONS = "#6f9bc4";
const INFO = "#5f93c0";

const TOOLTIP_STYLE = {
    background: "#25292d",
    border: "1px solid #3a3f44",
    borderRadius: 0,
    fontSize: 12,
    color: TEXT,
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
            <Card className="gap-3 border border-[var(--line)] bg-[var(--panel)] rounded-none p-5">
                <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4 text-[var(--lbl)]" />
                    <h2 className="hmi-lbl">
                        Fleet Energy — generated vs consumed (kWh / tick)
                    </h2>
                    {loading && <span className="text-[10px] text-[var(--lbl-dim)]">loading…</span>}
                </div>
                <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={aggData}>
                            <CartesianGrid stroke={GRID} strokeDasharray="3 3" />
                            <XAxis dataKey="t" stroke={AXIS} fontSize={10} />
                            <YAxis stroke={AXIS} fontSize={10} />
                            <Tooltip contentStyle={TOOLTIP_STYLE} />
                            <Legend wrapperStyle={{ fontSize: 11, color: TEXT }} />
                            <Area type="monotone" dataKey="energy_generated" name="Generated" stroke={GEN} fill={`${GEN}33`} />
                            <Area type="monotone" dataKey="energy_consumed" name="Consumed" stroke={CONS} fill={`${CONS}33`} />
                            <Line type="monotone" dataKey="net" name="Net" stroke={INFO} dot={false} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </Card>

            {/* Fleet frequency */}
            <Card className="gap-3 border border-[var(--line)] bg-[var(--panel)] rounded-none p-5">
                <h2 className="hmi-lbl">System Frequency (Hz)</h2>
                <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={aggData}>
                            <CartesianGrid stroke={GRID} strokeDasharray="3 3" />
                            <XAxis dataKey="t" stroke={AXIS} fontSize={10} />
                            <YAxis stroke={AXIS} fontSize={10} domain={["auto", "auto"]} />
                            <Tooltip contentStyle={TOOLTIP_STYLE} />
                            <Line type="monotone" dataKey="frequency" name="Frequency" stroke={GEN} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </Card>

            {/* Per-meter drilldown */}
            <Card className="gap-3 border border-[var(--line)] bg-[var(--panel)] rounded-none p-5">
                <div className="flex flex-wrap items-center gap-3">
                    <h2 className="hmi-lbl">Per-meter drilldown</h2>
                    <label htmlFor="meter-select" className="sr-only">
                        Meter
                    </label>
                    <select
                        id="meter-select"
                        value={meterId}
                        onChange={(e) => onMeterChange(e.target.value)}
                        className="hmi-input mono"
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
                                <CartesianGrid stroke={GRID} strokeDasharray="3 3" />
                                <XAxis dataKey="t" stroke={AXIS} fontSize={10} />
                                <YAxis yAxisId="kwh" stroke={AXIS} fontSize={10} />
                                <YAxis yAxisId="v" orientation="right" stroke={AXIS} fontSize={10} domain={["auto", "auto"]} />
                                <Tooltip contentStyle={TOOLTIP_STYLE} />
                                <Legend wrapperStyle={{ fontSize: 11, color: TEXT }} />
                                <Area yAxisId="kwh" type="monotone" dataKey="energy_generated" name="Generated" stroke={GEN} fill={`${GEN}33`} />
                                <Area yAxisId="kwh" type="monotone" dataKey="energy_consumed" name="Consumed" stroke={CONS} fill={`${CONS}33`} />
                                <Line yAxisId="v" type="monotone" dataKey="voltage" name="Voltage" stroke={INFO} dot={false} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <p className="py-8 text-center text-xs text-[var(--lbl-dim)]">Pick a meter to plot its gen/con/voltage.</p>
                )}
            </Card>
        </>
    );
}
