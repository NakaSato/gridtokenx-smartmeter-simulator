"use client";

import React, { createContext, useContext, useState, useCallback, useMemo, useEffect } from 'react';

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
    { label: 'Native Simulator (8082)', value: 'http://127.0.0.1:8082' },
    { label: 'Docker Simulator (8080)', value: 'http://127.0.0.1:8080' },
    { label: 'APISIX Gateway', value: 'http://apisix.gridtokenx-coresystem.orb.local' },
    { label: 'Production Mesh (4030)', value: 'http://127.0.0.1:4030' },
];

const NetworkContext = createContext<NetworkContextType | undefined>(undefined);

function storeApiTarget(target: string) {
    if (typeof window === 'undefined') return;
    localStorage.setItem('gridtokenx_api_target', target);
}

function storeCustomTargets(targets: NetworkTarget[]) {
    if (typeof window === 'undefined') return;
    localStorage.setItem('gridtokenx_custom_targets', JSON.stringify(targets));
}

export const NetworkProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [apiTarget, setApiTargetState] = useState<string>('');
    const [customTargets, setCustomTargets] = useState<NetworkTarget[]>([]);

    useEffect(() => {
        // Load initial state from localStorage after mount
        const storedTarget = localStorage.getItem('gridtokenx_api_target');
        if (storedTarget) {
            setApiTargetState(storedTarget);
        }

        const storedCustom = localStorage.getItem('gridtokenx_custom_targets');
        if (storedCustom) {
            try {
                setCustomTargets(JSON.parse(storedCustom));
            } catch (e) {
                console.error('Failed to parse custom targets', e);
            }
        }
    }, []);

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
            setApiTargetState('');
            storeApiTarget('');
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
