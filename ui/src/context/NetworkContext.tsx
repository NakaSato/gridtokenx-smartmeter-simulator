import React, { createContext, useContext, useState } from 'react';

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
    { label: 'Kong Gateway (4000)', value: 'http://localhost:4000' },
    { label: 'Local Simulator (8082)', value: 'http://localhost:8082' },
    { label: 'Production Mesh (8080)', value: 'http://localhost:8080' },
];

const NetworkContext = createContext<NetworkContextType | undefined>(undefined);

export const NetworkProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [apiTarget, setApiTargetState] = useState<string>(() => {
        return localStorage.getItem('gridtokenx_api_target') || 'http://localhost:8082';
    });

    const [customTargets, setCustomTargets] = useState<NetworkTarget[]>(() => {
        const saved = localStorage.getItem('gridtokenx_custom_targets');
        return saved ? JSON.parse(saved) : [];
    });

    const availableTargets = [
        ...PREDEFINED_TARGETS,
        ...customTargets.map(t => ({ ...t, isCustom: true }))
    ];

    const setApiTarget = (target: string) => {
        let normalized = target.trim().replace(/\/+$/, '');
        if (normalized && !normalized.startsWith('http')) {
            normalized = `http://${normalized}`;
        }
        setApiTargetState(normalized);
        localStorage.setItem('gridtokenx_api_target', normalized);

        // If it's a new custom target, add it to the list
        if (normalized && !availableTargets.some(t => t.value === normalized)) {
            const newTarget = { label: normalized, value: normalized };
            const updated = [...customTargets, newTarget];
            setCustomTargets(updated);
            localStorage.setItem('gridtokenx_custom_targets', JSON.stringify(updated));
        }
    };

    const removeTarget = (value: string) => {
        const updated = customTargets.filter(t => t.value !== value);
        setCustomTargets(updated);
        localStorage.setItem('gridtokenx_custom_targets', JSON.stringify(updated));

        // If the removed target was active, switch to default
        if (apiTarget === value) {
            setApiTarget('');
        }
    };

    const getApiUrl = (path: string) => {
        if (!apiTarget) return path;
        const separator = path.startsWith('/') ? '' : '/';
        return `${apiTarget}${separator}${path}`;
    };

    const getWsUrl = (path: string) => {
        const separator = path.startsWith('/') ? '' : '/';
        if (!apiTarget) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            return `${protocol}//${window.location.host}${separator}${path}`;
        }

        const wsBase = apiTarget.replace(/^http/, 'ws');
        return `${wsBase}${separator}${path}`;
    };

    return (
        <NetworkContext.Provider value={{ apiTarget, setApiTarget, availableTargets, removeTarget, getApiUrl, getWsUrl }}>
            {children}
        </NetworkContext.Provider>
    );
};

export const useNetwork = () => {
    const context = useContext(NetworkContext);
    if (context === undefined) {
        throw new Error('useNetwork must be used within a NetworkProvider');
    }
    return context;
};
