"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNetwork } from './NetworkProvider';
import { useApi } from '@/hooks/useApi';
import { useLogs } from '@/hooks/useLogs';
import { createSimulatorApi } from '@/lib/api/client';
import type { Reading, GridHealth, SimulatorStatus, AttackStatus, AttackMode, LogEntry, LogType } from '@/lib/types';
import type { MeterSummary, StartDeterministicPayload } from '@/lib/api/types';

interface SimulatorContextType {
    status: SimulatorStatus;
    readings: Reading[];
    analytics: GridHealth | null;
    attackStatus: AttackStatus;
    isConnected: boolean;
    logs: LogEntry[];
    isLoading: boolean;

    // Actions
    handleControl: (action: string) => Promise<void>;
    startDeterministic: (payload: StartDeterministicPayload) => Promise<void>;
    updateEnvironment: (updates: { weather?: string; grid_stress?: number }) => Promise<void>;
    updateMeterCount: (count: number, ratios?: Record<string, number>) => Promise<void>;
    deleteMeter: (meter_id: string) => Promise<void>;
    updateMeterReading: (meter_id: string, data: Record<string, number>) => Promise<void>;
    overrideMeterReading: (meter_id: string, data: { value: number, field: string, duration_ticks?: number }) => Promise<void>;
    handleAttack: (active: boolean, mode: AttackMode, magnitude: number) => Promise<void>;
    addLog: (message: string, type: LogType) => void;
    clearLogs: () => void;
    fetchInitialMeters: () => Promise<void>;
}

const SimulatorContext = createContext<SimulatorContextType | undefined>(undefined);

/** Poll interval for status + meter readings (ms). The backend is REST-only — no WebSocket. */
const POLL_INTERVAL_MS = 2000;

/** Map a backend meter summary onto the UI's `Reading` shape. */
function meterToReading(m: MeterSummary, prev?: Reading): Reading {
    return {
        ...(prev ?? {}),
        meter_id: m.meter_id,
        meter_type: m.meter_type || 'Unknown',
        location_name: m.location_name ?? m.meter_id,
        latitude: m.latitude ?? undefined,
        longitude: m.longitude ?? undefined,
        phase: m.phase ?? 'A',
        energy_generated: m.generation ?? 0,
        energy_consumed: m.consumption ?? 0,
        generation_kw: m.generation_kw ?? undefined,
        consumption_kw: m.consumption_kw ?? undefined,
        surplus_energy: Math.max(0, (m.generation ?? 0) - (m.consumption ?? 0)),
        voltage: m.voltage ?? 230,
        voltage_pu: (m.voltage ?? 230) / 230,
        has_solar: m.has_solar ?? undefined,
        solar_capacity: m.solar_capacity ?? undefined,
        timestamp: new Date().toISOString(),
    } as unknown as Reading;
}

export const SimulatorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { getApiUrl } = useNetwork();
    const { logs, addLog, clearLogs } = useLogs();
    const { apiCall, isLoading } = useApi(getApiUrl, addLog);
    const api = useMemo(() => createSimulatorApi(apiCall), [apiCall]);

    const [readings, setReadings] = useState<Reading[]>([]);
    const [status, setStatus] = useState<SimulatorStatus>({
        running: false, paused: false, num_meters: 0, mode: '-', health: {}, weather_mode: 'Sunny', grid_stress: 1.0
    });
    const [analytics] = useState<GridHealth | null>(null);
    const [attackStatus, setAttackStatus] = useState<AttackStatus>({ active: false, targets: [], mode: 'bias', bias_kw: 0.0 });
    const [isConnected, setIsConnected] = useState(false);
    // Baseline consumption captured when an attack starts, used to restore on stop
    // (the backend override has no clear/expiry endpoint).
    const attackBaselineRef = useRef<Map<string, number>>(new Map());

    const refreshMeters = useCallback(async () => {
        const data = await api.listMeters({ limit: 1000 });
        if (data?.meters) {
            setReadings(prev => {
                const prevById = new Map(prev.map(r => [r.meter_id, r]));
                return data.meters.map(m => meterToReading(m, prevById.get(m.meter_id)));
            });
        }
    }, [api]);

    // Kept for API compatibility with existing consumers.
    const fetchInitialMeters = refreshMeters;

    const fetchStatus = useCallback(async () => {
        const data = await api.getStatus();
        if (data) {
            setIsConnected(true);
            setStatus({
                running: data.running,
                paused: data.paused,
                num_meters: data.total_meters,
                mode: data.mode,
                health: {},
                weather_mode: data.weather,
                grid_stress: data.grid_stress_multiplier,
                sim_time: data.current_sim_time,
                deterministic: data.deterministic,
                seed: data.seed,
                start_time: data.start_time,
                end_time: data.end_time,
                run_id: data.run_id,
                interval_seconds: data.interval_seconds,
            });
        } else {
            setIsConnected(false);
        }
    }, [api]);

    const handleControl = useCallback(async (action: string) => {
        if (action === 'restart') {
            // No backend "restart"; emulate as stop -> start.
            await api.action('stop');
            await api.action('start');
            addLog('Simulation restarted', 'success');
        } else {
            const res = await api.action(action as 'start' | 'stop' | 'pause' | 'resume' | 'step');
            if (res) addLog(`Simulation ${res.status}`, 'success');
        }
        fetchStatus();
        refreshMeters();
    }, [api, addLog, fetchStatus, refreshMeters]);

    const startDeterministic = useCallback(async (payload: StartDeterministicPayload) => {
        // POST /simulation/actions/start-deterministic — re-seed + pin clock + rebuild
        // fleet for byte-identical replay. Backend rejects a bad start_time with 400.
        const res = await api.startDeterministic(payload);
        if (res) {
            addLog(`Deterministic run ${res.status} (seed=${res.seed}, ${res.total_meters} meters @ ${res.start_time})`, 'success');
            fetchStatus();
            setTimeout(() => refreshMeters(), 500);
        }
    }, [api, addLog, fetchStatus, refreshMeters]);

    const updateEnvironment = useCallback(async (updates: { weather?: string; grid_stress?: number }) => {
        // Backend PATCH /simulation/environment accepts `weather` and `grid_stress`.
        const res = await api.updateEnvironment(updates);
        if (res) fetchStatus();
    }, [api, fetchStatus]);

    const updateMeterCount = useCallback(async (count: number, ratios?: Record<string, number>) => {
        const res = await api.updateMeterCount({ count, ...ratios });
        if (res) {
            if (res.new_count !== count) {
                addLog(`Fleet set to ${res.new_count} meters (count is pinned to the GLM bus count).`, 'warning');
            }
            fetchStatus();
            setTimeout(() => refreshMeters(), 500);
        }
    }, [api, addLog, fetchStatus, refreshMeters]);

    const deleteMeter = useCallback(async (meter_id: string) => {
        const res = await api.deleteMeter(meter_id);
        if (res) refreshMeters();
    }, [api, refreshMeters]);

    const overrideMeterReading = useCallback(async (meter_id: string, data: { value: number, field: string, duration_ticks?: number }) => {
        // Backend contract is exactly { value, field }; duration_ticks is ignored.
        const field = data.field === 'generation' ? 'generation' : 'consumption';
        await api.overrideReading(meter_id, { value: data.value, field });
        refreshMeters();
    }, [api, refreshMeters]);

    const updateMeterReading = useCallback(async (meter_id: string, data: Record<string, number>) => {
        // No PUT /readings endpoint exists — translate "set value" into reading overrides.
        if ('generation' in data) await api.overrideReading(meter_id, { value: data.generation, field: 'generation' });
        if ('consumption' in data) await api.overrideReading(meter_id, { value: data.consumption, field: 'consumption' });
        refreshMeters();
    }, [api, refreshMeters]);

    const handleAttack = useCallback(async (active: boolean, mode: AttackMode, magnitude: number) => {
        // FDI is emulated via reading overrides on a sample of meters (the backend has
        // no dedicated attack endpoint). Consumption is spiked on activate and restored
        // from a captured baseline on deactivate.
        const targets = readings.slice(0, 5);
        if (active) {
            const baseline = attackBaselineRef.current;
            for (const m of targets) {
                const current = m.energy_consumed ?? 0;
                baseline.set(m.meter_id, current);
                const value = mode === 'scale' ? current * Math.max(1, magnitude)
                    : mode === 'random' ? current + Math.abs(magnitude)
                    : current + magnitude; // 'bias' (default)
                await api.overrideReading(m.meter_id, { value, field: 'consumption' });
            }
            setAttackStatus({ active: true, mode: String(mode), targets: targets.map(t => t.meter_id), bias_kw: magnitude });
            addLog(`FDI attack engaged on ${targets.length} meters (${mode}, +${magnitude}kW)`, 'warning');
        } else {
            for (const [meter_id, value] of attackBaselineRef.current.entries()) {
                await api.overrideReading(meter_id, { value, field: 'consumption' });
            }
            attackBaselineRef.current.clear();
            setAttackStatus({ active: false, mode: String(mode), targets: [], bias_kw: 0 });
            addLog('FDI attack mitigated; baseline consumption restored', 'success');
        }
        refreshMeters();
    }, [api, readings, addLog, refreshMeters]);

    // Initial load + polling loop (REST-only backend, so we poll rather than subscribe).
    useEffect(() => {
        let cancelled = false;
        const tick = async () => {
            if (cancelled) return;
            await fetchStatus();
            await refreshMeters();
        };
        tick();
        const interval = setInterval(tick, POLL_INTERVAL_MS);
        return () => { cancelled = true; clearInterval(interval); };
    }, [fetchStatus, refreshMeters]);

    const value = useMemo(() => ({
        status, readings, analytics, attackStatus, isConnected, logs, isLoading,
        handleControl, startDeterministic, updateEnvironment, updateMeterCount, deleteMeter, updateMeterReading, overrideMeterReading, handleAttack, addLog, clearLogs, fetchInitialMeters
    }), [status, readings, analytics, attackStatus, isConnected, logs, isLoading, handleControl, startDeterministic, updateEnvironment, updateMeterCount, deleteMeter, updateMeterReading, overrideMeterReading, handleAttack, addLog, clearLogs, fetchInitialMeters]);

    return <SimulatorContext.Provider value={value}>{children}</SimulatorContext.Provider>;
};

export const useSimulator = () => {
    const context = useContext(SimulatorContext);
    if (!context) throw new Error('useSimulator must be used within a SimulatorProvider');
    return context;
};
