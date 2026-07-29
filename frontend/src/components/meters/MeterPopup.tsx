"use client";

import { ArrowRight, Cpu } from 'lucide-react';
import { useState } from 'react';
import Link from 'next/link';
import { cn, copyToClipboard } from '@/lib/common';

export interface MeterData {
    meter_id: string;
    meter_type?: string;
    latitude: number;
    longitude: number;
    generation?: number;
    consumption?: number;
    voltage?: number;
    is_compromised?: boolean;
    nodal_price?: number;
    location_name?: string;
    phase?: string;
    is_shed?: boolean;
}

interface MeterPopupProps {
    meter: MeterData;
}

export function MeterPopup({ meter }: MeterPopupProps) {
    const [copied, setCopied] = useState(false);
    const handleCopy = async (e: React.MouseEvent) => {
        e.stopPropagation();
        if (!(await copyToClipboard(meter.meter_id))) {
            console.error('Failed to copy meter id');
            return;
        }
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="w-[280px] hmi-panel p-3 space-y-3">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="p-2 border border-[var(--line-2)] bg-[var(--panel-2)]">
                    <Cpu className="w-4 h-4 text-[var(--txt-val)]" />
                </div>
                <div className="flex-1 min-w-0">
                    <h3
                        onClick={handleCopy}
                        className={cn(
                            "font-semibold text-sm uppercase tracking-wide truncate leading-tight cursor-pointer",
                            copied ? "text-[var(--ok)]" : "text-[var(--txt-val)]"
                        )}
                        title="Click to copy ID"
                    >
                        {meter.location_name || 'Smart Meter'}
                    </h3>
                    <div className="flex items-center gap-2 mt-0.5">
                        <span className="hmi-lbl">
                            {meter.meter_type?.replace(/_/g, ' ') || 'SMART METER'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-2">
                <div className="bg-[var(--panel-2)] border border-[var(--line)] p-2.5 space-y-1">
                    <span className="hmi-lbl">Generation</span>
                    <p className="text-sm font-medium text-[var(--txt-val)] mono">
                        {(meter.generation || 0).toFixed(2)} <span className="hmi-unit">kWh</span>
                    </p>
                </div>
                <div className="bg-[var(--panel-2)] border border-[var(--line)] p-2.5 space-y-1">
                    <span className="hmi-lbl">Consumption</span>
                    <p className="text-sm font-medium text-[var(--txt-val)] mono">
                        {(meter.consumption || 0).toFixed(2)} <span className="hmi-unit">kWh</span>
                    </p>
                </div>
            </div>

            {/* Constraints & Environment */}
            <div className="grid grid-cols-2 gap-2">
                <div className="bg-[var(--panel-2)] border border-[var(--line)] p-2 flex flex-col items-center">
                    <span className="hmi-lbl">Limits (Min/Max)</span>
                    <span className="text-[10px] font-medium text-[var(--txt)] mono">0.1 / 500</span>
                </div>
                <div className="bg-[var(--panel-2)] border border-[var(--line)] p-2 flex flex-col items-center">
                    <span className="hmi-lbl">Ambient Temp</span>
                    <span className="text-[10px] font-medium text-[var(--txt)] mono">31.4°C</span>
                </div>
            </div>

            {/* Electrical Integrity */}
            {meter.is_shed ? (
                <div className="border border-[var(--alarm-bd)] bg-[var(--alarm-bg)] p-3 flex items-center justify-between">
                    <span className="hmi-lbl" style={{ color: 'var(--alarm)' }}>Status</span>
                    <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-semibold text-[var(--alarm)] uppercase tracking-widest">SHEDDED</span>
                        <span className="hmi-dot alarm" />
                    </div>
                </div>
            ) : (
                <div className="border border-[var(--line)] bg-[var(--panel-2)] p-3 flex items-center justify-between">
                    <span className="hmi-lbl">Grid Sync</span>
                    <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-medium text-[var(--txt-val)] mono">{meter.voltage}V</span>
                        <span className="hmi-dot" />
                    </div>
                </div>
            )}

            {/* Footer */}
            <Link
                href={`/meter/${meter.meter_id}`}
                className="hmi-btn primary w-full"
            >
                <span>Full Telemetry</span>
                <ArrowRight className="w-3.5 h-3.5" />
            </Link>
        </div>
    );
}
