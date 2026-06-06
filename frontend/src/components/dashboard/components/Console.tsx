"use client";

import { useMemo, useState, useCallback, memo } from 'react';
import {
    Terminal, Copy, Check, Trash2, Info, CheckCircle2,
    AlertTriangle, AlertCircle, Activity,
} from 'lucide-react';
import { cn } from '@/lib/common';
import type { LogEntry, LogType } from '@/lib/types';

interface ConsoleProps {
    logs: LogEntry[];
    onClear: () => void;
}

type FilterKey = 'all' | LogType;

// Per-level presentation: icon + accent colour, reused by the filter pills and
// each log row so a level reads the same everywhere.
const LEVEL_META: Record<LogType, { icon: typeof Info; color: string; bar: string; label: string }> = {
    info: { icon: Info, color: 'text-blue-400', bar: 'border-l-blue-400/70', label: 'Info' },
    success: { icon: CheckCircle2, color: 'text-emerald-400', bar: 'border-l-emerald-400/70', label: 'OK' },
    warning: { icon: AlertTriangle, color: 'text-amber-400', bar: 'border-l-amber-400/70', label: 'Warn' },
    error: { icon: AlertCircle, color: 'text-rose-400', bar: 'border-l-rose-400/70', label: 'Error' },
    reading: { icon: Activity, color: 'text-indigo-400', bar: 'border-l-indigo-400/70', label: 'Reading' },
};

const FILTERS: FilterKey[] = ['all', 'reading', 'info', 'success', 'warning', 'error'];

export const Console = memo(({ logs, onClear }: ConsoleProps) => {
    const [filter, setFilter] = useState<FilterKey>('all');
    const [copied, setCopied] = useState(false);

    // Counts per level for the filter-pill badges (single pass).
    const counts = useMemo(() => {
        const c: Record<string, number> = { all: logs.length };
        for (const log of logs) c[log.type] = (c[log.type] ?? 0) + 1;
        return c;
    }, [logs]);

    const filtered = useMemo(
        () => (filter === 'all' ? logs : logs.filter((l) => l.type === filter)),
        [logs, filter],
    );

    const copyLogs = useCallback(() => {
        const text = filtered
            .map((l) => {
                const body = l.type === 'reading' && l.reading
                    ? `${l.reading.meter_id} +${(l.reading.energy_generated || 0).toFixed(2)}/-${(l.reading.energy_consumed || 0).toFixed(2)}`
                    : l.message;
                return `[${l.timestamp}] ${l.type.toUpperCase()} ${body}`;
            })
            .join('\n');
        navigator.clipboard?.writeText(text).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 1200);
        }).catch(() => { /* clipboard blocked — no-op */ });
    }, [filtered]);

    return (
        <div className="glass rounded-3xl overflow-hidden shadow-2xl h-[600px] flex flex-col border border-indigo-500/20">
            <div className="bg-slate-900/80 px-4 py-3 border-b border-white/5 flex flex-col gap-3">
                <div className="flex justify-between items-center">
                    <span className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-indigo-400">
                        <Terminal className="w-3.5 h-3.5" /> System Logs
                        <span className="flex items-center gap-1 text-slate-500">
                            <span className="relative flex h-1.5 w-1.5">
                                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
                            </span>
                            {logs.length}
                        </span>
                    </span>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={copyLogs}
                            disabled={filtered.length === 0}
                            className="flex items-center gap-1 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors disabled:opacity-30 disabled:hover:text-slate-500"
                            aria-label="Copy logs"
                        >
                            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                            {copied ? 'Copied' : 'Copy'}
                        </button>
                        <button
                            onClick={onClear}
                            disabled={logs.length === 0}
                            className="flex items-center gap-1 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-rose-400 transition-colors disabled:opacity-30 disabled:hover:text-slate-500"
                            aria-label="Clear logs"
                        >
                            <Trash2 className="w-3 h-3" /> Clear
                        </button>
                    </div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                    {FILTERS.map((key) => {
                        const meta = key === 'all' ? null : LEVEL_META[key];
                        const count = counts[key] ?? 0;
                        const active = filter === key;
                        return (
                            <button
                                key={key}
                                onClick={() => setFilter(key)}
                                className={cn(
                                    "px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider border transition-colors",
                                    active
                                        ? "bg-indigo-500/20 border-indigo-400/40 text-indigo-200"
                                        : "border-white/5 text-slate-500 hover:text-slate-300 hover:border-white/10",
                                )}
                            >
                                <span className={cn(active && meta ? meta.color : '')}>
                                    {key === 'all' ? 'All' : meta!.label}
                                </span>
                                <span className="ml-1 text-slate-500">{count}</span>
                            </button>
                        );
                    })}
                </div>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-1.5 font-mono text-[11px]" role="log">
                {filtered.map((log, i) => {
                    const meta = LEVEL_META[log.type];
                    const Icon = meta.icon;
                    return (
                        <div
                            key={`${log.timestamp}-${i}`}
                            className={cn(
                                "flex gap-2.5 items-start pl-2 py-1 border-l-2 rounded-r bg-white/[0.015] hover:bg-white/[0.04] transition-colors",
                                meta.bar,
                            )}
                        >
                            <Icon className={cn("w-3 h-3 mt-0.5 shrink-0", meta.color)} />
                            <span className="text-slate-600 shrink-0">{log.timestamp}</span>
                            <div className="min-w-0 flex-1">
                                {log.type === 'reading' && log.reading ? (
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <span className="text-blue-400 font-bold truncate max-w-[140px]">{log.reading.meter_id}</span>
                                        <span className="text-emerald-400">+{(log.reading.energy_generated || 0).toFixed(2)}</span>
                                        <span className="text-slate-600">/</span>
                                        <span className="text-rose-400">−{(log.reading.energy_consumed || 0).toFixed(2)}</span>
                                        {(() => {
                                            const net = (log.reading.energy_generated || 0) - (log.reading.energy_consumed || 0);
                                            return (
                                                <span className={cn("ml-auto px-1.5 rounded text-[9px] font-bold", net >= 0 ? "bg-emerald-500/15 text-emerald-400" : "bg-rose-500/15 text-rose-400")}>
                                                    {net >= 0 ? '+' : ''}{net.toFixed(2)}
                                                </span>
                                            );
                                        })()}
                                    </div>
                                ) : (
                                    <span className={cn("break-words", meta.color)}>{log.message}</span>
                                )}
                            </div>
                        </div>
                    );
                })}
                {filtered.length === 0 && (
                    <div className="text-slate-600 animate-pulse uppercase tracking-widest text-center py-10">
                        {logs.length === 0 ? 'Listening for signals…' : `No ${filter} entries`}
                    </div>
                )}
            </div>
        </div>
    );
});

Console.displayName = 'Console';
