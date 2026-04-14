"use client";

import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';

export interface NetworkTarget {
    label: string;
    value: string;
    isCustom?: boolean;
}

interface NetworkContextType {
    apiTarget: string;
    setApiTarget: (target: string) => void;
    availableTargets: NetworkTarget[];
    removeTarget: (value: string) => void;
    getApiUrl: (path: string) => string;
    getWsUrl: (path: string) => string;
}

const PREDEFINED_TARGETS: NetworkTarget[] = [
    { label: 'Relative (Default)', value: '' },
    { label: 'APISIX (4001)', value: 'http://localhost:4001' },
    { label: 'Local Simulator (8082)', value: 'http://localhost:8082' },
    { label: 'Production Mesh (4030)', value: 'http://localhost:4030' },
];

const NetworkContext = createContext<NetworkContextType | undefined>(undefined);

function getStoredApiTarget(): string {
    if (typeof window === 'undefined') return 'http://localhost:8082';
    return localStorage.getItem('gridtokenx_api_target') || 'http://localhost:8082';
}

function getStoredCustomTargets(): NetworkTarget[] {
    if (typeof window === 'undefined') return [];
    const saved = localStorage.getItem('gridtokenx_custom_targets');
    return saved ? JSON.parse(saved) : [];
}

function storeApiTarget(target: string) {
    if (typeof window === 'undefined') return;
    localStorage.setItem('gridtokenx_api_target', target);
}

function storeCustomTargets(targets: NetworkTarget[]) {
    if (typeof window === 'undefined') return;
    localStorage.setItem('gridtokenx_custom_targets', JSON.stringify(targets));
}

export const NetworkProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [apiTarget, setApiTargetState] = useState<string>(getStoredApiTarget);
    const [customTargets, setCustomTargets] = useState<NetworkTarget[]>(getStoredCustomTargets);

    const availableTargets = useMemo(() => [
        ...PREDEFINED_TARGETS,
        ...customTargets.map(t => ({ ...t, isCustom: true })),
    ], [customTargets]);

    const setApiTarget = useCallback((target: string) => {
        let normalized = target.trim().replace(/\/+$/, '');
        if (normalized && !normalized.startsWith('http')) {
            normalized = `http://${normalized}`;
        }
        setApiTargetState(normalized);
        storeApiTarget(normalized);

        if (normalized && !PREDEFINED_TARGETS.some(t => t.value === normalized) && !customTargets.some(t => t.value === normalized)) {
            const newTarget: NetworkTarget = { label: normalized, value: normalized };
            const updated = [...customTargets, newTarget];
            setCustomTargets(updated);
            storeCustomTargets(updated);
        }
    }, [customTargets]);

    const removeTarget = useCallback((value: string) => {
        const updated = customTargets.filter(t => t.value !== value);
        setCustomTargets(updated);
        storeCustomTargets(updated);
        if (apiTarget === value) {
            setApiTargetState('http://localhost:8082');
            storeApiTarget('http://localhost:8082');
        }
    }, [customTargets, apiTarget]);

    const getApiUrl = useCallback((path: string) => {
        if (!apiTarget) return path;
        return `${apiTarget}${path}`;
    }, [apiTarget]);

    const getWsUrl = useCallback((path: string) => {
        if (!apiTarget) return path.replace(/^http/, 'ws');
        return apiTarget.replace(/^http/, 'ws') + path;
    }, [apiTarget]);

    const value = useMemo(() => ({
        apiTarget,
        setApiTarget,
        availableTargets,
        removeTarget,
        getApiUrl,
        getWsUrl,
    }), [apiTarget, setApiTarget, availableTargets, removeTarget, getApiUrl, getWsUrl]);

    return <NetworkContext.Provider value={value}>{children}</NetworkContext.Provider>;
};

export const useNetwork = (): NetworkContextType => {
    const context = useContext(NetworkContext);
    if (!context) {
        throw new Error('useNetwork must be used within NetworkProvider');
    }
    return context;
};
