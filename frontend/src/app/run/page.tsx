"use client";

import { useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { Dices, RefreshCw } from "lucide-react";
import { useSimulatorApi } from "@/hooks/useSimulatorApi";
import type { MeterSummary, RunSeriesPoint } from "@/lib/api/types";

// recharts is heavy; keep it out of the initial /run chunk. Client-only — the
// charts need a measured container (ResponsiveContainer), so skip SSR.
const RunCharts = dynamic(() => import("./RunCharts"), {
    ssr: false,
    loading: () => (
        <div className="py-16 text-center text-xs text-[var(--lbl-dim)]">Loading charts…</div>
    ),
});

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

    return (
        <main className="mx-auto max-w-6xl space-y-6 p-6">
            <header className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <div className="hmi-panel-2 p-2 text-[var(--lbl)] border border-[var(--line)] bg-[var(--panel-2)]">
                        <Dices className="h-5 w-5" />
                    </div>
                    <div>
                        <h1 className="text-xl font-semibold text-[var(--txt-val)]">Deterministic Run Plots</h1>
                        <p className="text-xs text-[var(--lbl)]">InfluxDB time-series for a seeded run</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <label htmlFor="run-select" className="hmi-lbl">
                        Run
                    </label>
                    <select
                        id="run-select"
                        value={runId}
                        onChange={(e) => setRunId(e.target.value)}
                        className="hmi-input mono"
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
                        className="hmi-btn"
                    >
                        <RefreshCw className="h-4 w-4" />
                    </button>
                </div>
            </header>

            {error && (
                <div className="border border-[var(--alarm-bd)] bg-[var(--alarm-bg)] p-3 text-xs font-medium text-[var(--alarm)]">
                    {error}
                </div>
            )}

            <RunCharts
                agg={agg}
                meterSeries={meterSeries}
                loading={loading}
                meters={meters}
                meterId={meterId}
                onMeterChange={setMeterId}
            />
        </main>
    );
}
