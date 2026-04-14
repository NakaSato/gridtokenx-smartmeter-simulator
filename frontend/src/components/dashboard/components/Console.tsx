"use client";

import { useEffect, useRef, memo } from 'react';
import { cn } from '@/lib/common';
import type { LogEntry } from '@/lib/types';

interface ConsoleProps {
    logs: LogEntry[];
    onClear: () => void;
}

export const Console = memo(({ logs, onClear }: ConsoleProps) => {
    const consoleRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom on new logs (optional - currently shows newest first)
    useEffect(() => {
        if (consoleRef.current && logs.length > 0) {
            // Uncomment to auto-scroll: consoleRef.current.scrollTop = 0;
        }
    }, [logs]);

    return (
        <div className="glass rounded-3xl overflow-hidden shadow-2xl h-[600px] flex flex-col border border-indigo-500/20">
            <div className="bg-slate-900/80 p-4 border-b border-white/5 flex justify-between items-center">
                <span className="text-[10px] font-black uppercase tracking-widest text-indigo-400">System Logs</span>
                <button
                    onClick={onClear}
                    className="text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors"
                    aria-label="Clear logs"
                >
                    Clear
                </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-2 font-mono text-[11px]" ref={consoleRef} role="log">
                {logs.map((log, i) => (
                    <div key={`${log.timestamp}-${i}`} className="flex gap-3">
                        <span className="text-slate-600 shrink-0">[{log.timestamp}]</span>
                        <div className="space-y-1">
                            {log.type === 'reading' && log.reading ? (
                                <div className="flex items-center gap-2">
                                    <span className="text-blue-400 font-bold">{log.reading.meter_id}</span>
                                    <span className="text-slate-500">→</span>
                                    <span className="text-emerald-400">+{log.reading.energy_generated.toFixed(2)}</span>
                                    <span className="text-slate-500">/</span>
                                    <span className="text-rose-400">-{log.reading.energy_consumed.toFixed(2)}</span>
                                </div>
                            ) : (
                                <span className={cn(
                                    log.type === 'error' && "text-rose-400",
                                    log.type === 'warning' && "text-amber-400",
                                    log.type === 'success' && "text-emerald-400",
                                    log.type === 'info' && "text-blue-400"
                                )}>
                                    {log.message}
                                </span>
                            )}
                        </div>
                    </div>
                ))}
                {logs.length === 0 && (
                    <div className="text-slate-600 animate-pulse uppercase tracking-widest text-center py-10">
                        Listening for signals...
                    </div>
                )}
            </div>
        </div>
    );
});

Console.displayName = 'Console';
