"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { useNetwork } from './NetworkProvider';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useApi } from '@/hooks/useApi';
import { useLogs } from '@/hooks/useLogs';
import type { Reading, GridHealth, SimulatorStatus, AttackStatus, AttackMode, WsMessage, LogEntry, LogType } from '@/lib/types';
import { STATUS_REFRESH_DELAY_MS, DEFAULT_METER_COUNT } from '@/lib/constants';

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
    updateEnvironment: (updates: { weather?: string; grid_stress?: number }) => Promise<void>;
    handleAttack: (active: boolean, mode: AttackMode, magnitude: number) => Promise<void>;
    addLog: (message: string, type: LogType) => void;
    clearLogs: () => void;
}

const SimulatorContext = createContext<SimulatorContextType | undefined>(undefined);

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

    const handleWsMessage = useCallback((data: unknown) => {
        const msg = data as WsMessage;
        if (msg.type === 'meter_readings' && msg.readings) setReadings(msg.readings);
        else if (msg.type === 'grid_status' && msg.data) setAnalytics(msg.data as GridHealth);
    }, []);

    const { isConnected } = useWebSocket(getWsUrl('/ws'), handleWsMessage, addLog);

    const fetchStatus = useCallback(async () => {
        const data = await apiCall<any>('/api/v1/simulation/status');
        if (data) setStatus({
            running: data.running, paused: data.paused, num_meters: data.num_meters,
            mode: data.mode, health: {}, weather_mode: data.weather, grid_stress: data.grid_stress_multiplier
        });
    }, [apiCall]);

    const handleControl = useCallback(async (action: string) => {
        const res = await apiCall<any>(`/api/v1/simulation/actions/${action}`, { method: 'POST' });
        if (res?.success) fetchStatus();
    }, [apiCall, fetchStatus]);

    const updateEnvironment = useCallback(async (updates: any) => {
        const res = await apiCall<any>('/api/v1/simulation/environment', { method: 'PATCH', body: JSON.stringify(updates) });
        if (res?.success) fetchStatus();
    }, [apiCall, fetchStatus]);

    const handleAttack = useCallback(async (active: boolean, mode: AttackMode, magnitude: number) => {
        const res = await apiCall<any>('/api/v1/simulation/scenarios/fdi-attack', {
            method: 'POST', body: JSON.stringify({ attack_type: mode, magnitude, active })
        });
        if (res?.success) setAttackStatus(res.status);
    }, [apiCall]);

    useEffect(() => { fetchStatus(); }, [fetchStatus]);

    const value = useMemo(() => ({
        status, readings, analytics, attackStatus, isConnected, logs, isLoading,
        handleControl, updateEnvironment, handleAttack, addLog, clearLogs
    }), [status, readings, analytics, attackStatus, isConnected, logs, isLoading, handleControl, updateEnvironment, handleAttack, addLog, clearLogs]);

    return <SimulatorContext.Provider value={value}>{children}</SimulatorContext.Provider>;
};

export const useSimulator = () => {
    const context = useContext(SimulatorContext);
    if (!context) throw new Error('useSimulator must be used within a SimulatorProvider');
    return context;
};
