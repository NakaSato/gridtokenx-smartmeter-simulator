"use client";

import { useState, useEffect } from 'react';
import { Factory, Leaf, Scale, Trees } from 'lucide-react';
import { useSimulatorApi } from '@/hooks/useSimulatorApi';
import type { CarbonSummary } from '@/lib/api/types';

const POLL_MS = 15000;

const fmt = (n: number, d = 1) =>
    n.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });

// Fleet-wide CO2 accounting from GET /carbon/summary. Polled independently of
// the live telemetry stream — the aggregate moves on the 15-min settlement
// cadence, not every tick.
export const FleetCarbon = () => {
    const api = useSimulatorApi();
    const [summary, setSummary] = useState<CarbonSummary | null>(null);

    useEffect(() => {
        let cancelled = false;
        const load = async () => {
            const data = await api.getCarbonSummary().catch(() => null);
            if (!cancelled) setSummary(data);
        };
        load();
        const interval = setInterval(load, POLL_MS);
        return () => { cancelled = true; clearInterval(interval); };
    }, [api]);

    if (!summary) return null;

    const carbonNegative = summary.net_emissions_kg <= 0;

    return (
        <section aria-label="Fleet carbon footprint" className="space-y-3">
            <div className="flex items-center justify-between">
                <h2 className="hmi-title text-[13px] flex items-center gap-3">
                    <Leaf className="w-5 h-5 text-[var(--lbl)]" /> FLEET CARBON
                </h2>
                <span className="hmi-meta mono">
                    {summary.meter_count} meters · grid {fmt(summary.grid_intensity_kgco2_per_kwh, 3)} kg/kWh
                </span>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <StatBox
                    icon={Factory}
                    label="Grid emissions"
                    value={fmt(summary.grid_emissions_kg, 1)}
                    unit="kg CO₂e"
                    sub={`${fmt(summary.import_kwh, 0)} kWh imported`}
                />
                <StatBox
                    icon={Leaf}
                    label="Offset (net of PV)"
                    value={fmt(summary.offset_kg, 1)}
                    unit="kg CO₂e"
                    sub={`${fmt(summary.export_kwh, 0)} kWh exported`}
                />
                <StatBox
                    icon={Scale}
                    label="Net emissions"
                    value={`${summary.net_emissions_kg < 0 ? '−' : ''}${fmt(Math.abs(summary.net_emissions_kg), 1)}`}
                    unit="kg CO₂e"
                    sub={carbonNegative ? 'Carbon-negative' : 'Net emitter'}
                    tone={carbonNegative ? 'ok' : 'alarm'}
                />
                <StatBox
                    icon={Trees}
                    label="Trees equivalent"
                    value={fmt(summary.trees_equivalent, 2)}
                    unit="trees/yr"
                    sub="annual CO₂ sequestration"
                    tone="ok"
                />
            </div>
        </section>
    );
};

interface StatBoxProps {
    icon: React.ElementType;
    label: string;
    value: string;
    unit: string;
    sub: string;
    tone?: 'ok' | 'alarm';
}

const StatBox = ({ icon: Icon, label, value, unit, sub, tone }: StatBoxProps) => (
    <div className="hmi-panel p-3.5">
        <div className="flex items-center gap-2 mb-2">
            <Icon className="w-3.5 h-3.5 text-[var(--lbl)]" />
            <span className="hmi-lbl">{label}</span>
        </div>
        <div className={`text-lg mono ${tone === 'ok' ? 'text-[var(--ok)]' : tone === 'alarm' ? 'text-[var(--alarm)]' : 'text-[var(--txt-val)]'}`}>
            {value}<span className="text-[9px] ml-1 text-[var(--lbl)]">{unit}</span>
        </div>
        <div className="hmi-meta mt-1">{sub}</div>
    </div>
);
