"use client";

import { useCallback, useEffect, useState } from 'react';
import { KeyRound, RefreshCw, Shield, ShieldCheck } from 'lucide-react';
import { useSimulatorApi } from '@/hooks/useSimulatorApi';
import type { SecurityStatusResponse } from '@/lib/api/types';

const POLL_MS = 15000;

// Egress security posture from GET /security/status: which hardening layers are
// active (TLS / mTLS / payload encryption / key rotation) plus live key state,
// with a fleet key-rotation control. Polled on the slow cadence — posture and
// key versions move rarely, not per tick.
export const SecurityPanel = () => {
    const api = useSimulatorApi();
    const [status, setStatus] = useState<SecurityStatusResponse | null>(null);
    const [rotating, setRotating] = useState(false);

    const load = useCallback(async () => {
        const data = await api.getSecurityStatus().catch(() => null);
        setStatus(data);
    }, [api]);

    useEffect(() => {
        let cancelled = false;
        const run = async () => {
            const data = await api.getSecurityStatus().catch(() => null);
            if (!cancelled) setStatus(data);
        };
        run();
        const interval = setInterval(run, POLL_MS);
        return () => {
            cancelled = true;
            clearInterval(interval);
        };
    }, [api]);

    const rotate = useCallback(async () => {
        setRotating(true);
        await api.rotateKeys().catch(() => null);
        await load();
        setRotating(false);
    }, [api, load]);

    if (!status) return null;

    const { secure, layers, metering_egress: m, keys } = status;

    return (
        <section aria-label="Telemetry security posture" className="space-y-3">
            <div className="flex items-center justify-between">
                <h2 className="hmi-title text-[13px] flex items-center gap-3">
                    {secure ? (
                        <ShieldCheck className="w-5 h-5 text-[var(--ok)]" />
                    ) : (
                        <Shield className="w-5 h-5 text-[var(--alarm)]" />
                    )}
                    TELEMETRY SECURITY
                </h2>
                <span className={`hmi-bdg ${secure ? 'text-[var(--ok)]' : 'text-[var(--alarm)]'}`}>
                    {secure ? 'SECURE' : 'NOT SECURE'}
                </span>
            </div>

            <div className="hmi-panel p-3.5 space-y-3">
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                    {layers.map((layer) => (
                        <div key={layer.name} className="flex items-center gap-2">
                            <span
                                className="hmi-dot"
                                style={{ background: layer.on ? 'var(--ok)' : 'var(--lbl)' }}
                            />
                            <span className={`hmi-lbl ${layer.on ? '' : 'opacity-50'}`}>{layer.name}</span>
                        </div>
                    ))}
                </div>

                <div className="flex items-center justify-between border-t border-white/5 pt-2.5">
                    <div className="flex items-center gap-2">
                        <KeyRound className="w-3.5 h-3.5 text-[var(--lbl)]" />
                        <span className="hmi-meta mono">
                            {keys.rotation_active
                                ? `${keys.meter_count} meters keyed · auto-rotate ${m.rotation_interval_s ? `${m.rotation_interval_s}s` : 'off'} · keep ${m.key_grace_versions}`
                                : 'key rotation off'}
                        </span>
                    </div>
                    <button
                        type="button"
                        className="hmi-btn flex items-center gap-1.5 text-[11px]"
                        onClick={rotate}
                        disabled={rotating || !keys.rotation_active}
                    >
                        <RefreshCw className={`w-3 h-3 ${rotating ? 'animate-spin' : ''}`} /> ROTATE KEYS
                    </button>
                </div>

                <div className="hmi-meta mono opacity-70">→ {m.endpoint}</div>
            </div>
        </section>
    );
};
