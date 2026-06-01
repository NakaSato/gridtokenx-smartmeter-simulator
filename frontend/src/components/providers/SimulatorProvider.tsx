"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNetwork } from './NetworkProvider';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useApi } from '@/hooks/useApi';
import { useLogs } from '@/hooks/useLogs';
import type { Reading, GridHealth, SimulatorStatus, AttackStatus, AttackMode, WsMessage, LogEntry, LogType } from '@/lib/types';

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
    updateEnvironment: (updates: { weather?: string; grid_stress?: number; scenario?: string }) => Promise<void>;
    updateMeterCount: (count: number, ratios?: Record<string, number>) => Promise<void>;
    handleAttack: (active: boolean, mode: AttackMode, magnitude: number) => Promise<void>;
    addLog: (message: string, type: LogType) => void;
    clearLogs: () => void;
    fetchInitialMeters: () => Promise<void>;
}

const SimulatorContext = createContext<SimulatorContextType | undefined>(undefined);

interface SimulationStatusResponse {
    running: boolean;
    paused: boolean;
    num_meters: number;
    mode: string;
    weather: string;
    grid_stress_multiplier: number;
}

export const SimulatorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { getApiUrl, getWsUrl } = useNetwork();
    const { logs, addLog, clearLogs } = useLogs();
    const { apiCall, isLoading } = useApi(getApiUrl, addLog);

    const [readings, setReadings] = useState<Reading[]>([]);
    const [status, setStatus] = useState<SimulatorStatus>({
        running: false, paused: false, num_meters: 0, mode: '-', health: {}, weather_mode: 'Sunny', grid_stress: 1.0
    });
    const [analytics, setAnalytics] = useState<GridHealth | null>(null);
    const [attackStatus, setAttackStatus] = useState<AttackStatus>({ active: false, targets: [], mode: 'bias', bias_kw: 0.0 });
    const isInitialMount = useRef(true);

    const handleWsMessage = useCallback((data: unknown) => {
        const msg = data as WsMessage;
        if (msg.type === 'meter_readings' && msg.readings) setReadings(msg.readings);
        else if (msg.type === 'grid_status' && msg.data) setAnalytics(msg.data as GridHealth);
    }, []);

    const { isConnected } = useWebSocket(getWsUrl('/ws'), handleWsMessage, addLog);

    const fetchInitialMeters = useCallback(async () => {
        const data = await apiCall<{ meters: any[] }>('/api/v1/meters');
        if (data && data.meters) {
            const initialReadings: Reading[] = data.meters.map(m => ({
                meter_id: m.meter_id,
                meter_type: m.meter_type || 'Unknown',
                energy_generated: 0,
                energy_consumed: 0,
                voltage: 230,
                frequency: 50,
                timestamp: new Date().toISOString(),
                latitude: m.latitude,
                longitude: m.longitude,
                battery_level: 0,
                temperature: 25,
                surplus_energy: 0,
                voltage_pu: 1.0,
                freq_hz: 50,
                power_factor: 0.98,
                location: m.province || 'Unknown',
                location_name: m.meter_id,
                is_compromised: false,
                is_synced_with_solana: false,
                solana_sol_balance: 0,
                solana_gtnx_balance: 0,
                norm_residual: 0,
                phase: 'A'
            } as unknown as Reading));
            setReadings(prev => prev.length === 0 ? initialReadings : prev);
        }
    }, [apiCall]);

    const fetchStatus = useCallback(async () => {
        const data = await apiCall<SimulationStatusResponse>('/api/v1/simulation/status');
        if (data) {
            setStatus({
                running: data.running, paused: data.paused, num_meters: data.num_meters,
                mode: data.mode, health: {}, weather_mode: data.weather, grid_stress: data.grid_stress_multiplier
            });
            // If running, we might already have meters
            fetchInitialMeters();
        }
    }, [apiCall, fetchInitialMeters]);

    const handleControl = useCallback(async (action: string) => {
        const res = await apiCall<{ success: boolean }>(`/api/v1/simulation/actions/${action}`, { method: 'POST' });
        if (res?.success) fetchStatus();
    }, [apiCall, fetchStatus]);

    const updateEnvironment = useCallback(async (updates: { weather?: string; grid_stress?: number; scenario?: string }) => {
        const res = await apiCall<{ success: boolean; status?: string }>('/api/v1/simulation/environment', { method: 'PATCH', body: JSON.stringify(updates) });
        if (res) {
            fetchStatus();
            if (updates.scenario) {
                // Scenario change resets meters, so fetch new ones
                setTimeout(() => fetchInitialMeters(), 1000);
            }
        }
    }, [apiCall, fetchStatus, fetchInitialMeters]);

    const updateMeterCount = useCallback(async (count: number, ratios?: Record<string, number>) => {
        const res = await apiCall<{ status: string }>('/api/v1/meters/count', { 
            method: 'PUT', 
            body: JSON.stringify({ count, ...ratios }) 
        });
        if (res) {
            fetchStatus();
            setTimeout(() => fetchInitialMeters(), 1000);
        }
    }, [apiCall, fetchStatus, fetchInitialMeters]);

    const handleAttack = useCallback(async (active: boolean, mode: AttackMode, magnitude: number) => {
        const res = await apiCall<{ success: boolean, status: AttackStatus }>('/api/v1/simulation/scenarios/fdi-attack', {
            method: 'POST', body: JSON.stringify({ attack_type: mode, magnitude, active })
        });
        if (res?.success) setAttackStatus(res.status);
    }, [apiCall]);

    useEffect(() => {
        const timeoutId = setTimeout(() => {
            fetchStatus();
        }, 0);
        return () => clearTimeout(timeoutId);
    }, [fetchStatus]);

    const value = useMemo(() => ({
        status, readings, analytics, attackStatus, isConnected, logs, isLoading,
        handleControl, updateEnvironment, updateMeterCount, handleAttack, addLog, clearLogs, fetchInitialMeters
    }), [status, readings, analytics, attackStatus, isConnected, logs, isLoading, handleControl, updateEnvironment, updateMeterCount, handleAttack, addLog, clearLogs, fetchInitialMeters]);

    return <SimulatorContext.Provider value={value}>{children}</SimulatorContext.Provider>;
};

export const useSimulator = () => {
    const context = useContext(SimulatorContext);
    if (!context) throw new Error('useSimulator must be used within a SimulatorProvider');
    return context;
};
