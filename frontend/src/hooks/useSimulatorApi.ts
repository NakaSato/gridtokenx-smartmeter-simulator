"use client";

import { useMemo } from 'react';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { createSimulatorApi, type ApiCall } from '@/lib/api/client';

/**
 * Returns the typed simulator API client wired to the currently-selected
 * network target. The underlying `fetch` wrapper THROWS on non-2xx responses
 * (parsing the backend `detail` field), so callers keep their existing
 * try/catch error handling.
 *
 * This is the component-facing counterpart to the logging client used inside
 * `SimulatorProvider` — both share the same typed method surface from
 * `createSimulatorApi`, so endpoint paths/bodies live in exactly one place.
 */
export function useSimulatorApi() {
    const { getApiUrl } = useNetwork();

    return useMemo(() => {
        const apiCall: ApiCall = async <T,>(path: string, options: RequestInit = {}) => {
            const res = await fetch(getApiUrl(path), {
                cache: 'no-store',
                ...options,
                headers: { 'Content-Type': 'application/json', ...options.headers },
            });

            if (!res.ok) {
                let msg = `HTTP ${res.status}: ${res.statusText}`;
                try {
                    const err = await res.json();
                    if (err?.detail) {
                        msg = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
                    } else if (err?.message) {
                        msg = err.message;
                    }
                } catch {
                    /* non-JSON error body */
                }
                throw new Error(msg);
            }

            const text = await res.text();
            return (text ? JSON.parse(text) : null) as T;
        };

        return createSimulatorApi(apiCall);
    }, [getApiUrl]);
}
