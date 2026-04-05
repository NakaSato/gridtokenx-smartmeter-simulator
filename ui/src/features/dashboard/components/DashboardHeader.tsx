import { memo } from 'react';
import { NavLink } from '../../../components/ui/NavLink';
import { NetworkTargetSelector } from './NetworkTargetSelector';
import { Box, Map as MapIcon, Activity, Globe } from 'lucide-react';

export const NAV_LINKS = [
    { to: "/vpp", icon: Box, label: "Manage", title: "VPP Ops", color: "emerald" },
    { to: "/grid-map", icon: MapIcon, label: "View", title: "Grid Map", color: "indigo" },
    { to: "/open-infra-map", icon: MapIcon, label: "Open Infra", title: "Open Infrastructure Map", color: "indigo" },
    { to: "/adr", icon: Activity, label: "Control", title: "ADR Ops", color: "rose" },
    { to: "/lpc", icon: Globe, label: "Green", title: "Carbon/LMP", color: "emerald" },
] as const;

interface DashboardHeaderProps {
    apiTarget: string;
    setApiTarget: (target: string) => void;
    availableTargets: Array<{ label: string; value: string; isCustom?: boolean }>;
    removeTarget: (value: string) => void;
    isConnected: boolean;
}

export const DashboardHeader = memo(({
    apiTarget,
    setApiTarget,
    availableTargets,
    removeTarget,
    isConnected
}: DashboardHeaderProps) => (
    <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
        <div className="flex flex-col">
            <h1 className="text-5xl font-black tracking-tighter bg-gradient-to-r from-emerald-400 via-teal-400 to-indigo-500 bg-clip-text text-transparent drop-shadow-sm">
                GRIDTOKENX
            </h1>
            <div className="flex items-center gap-2 mt-1">
                <div className="h-0.5 w-8 bg-emerald-500/50 rounded-full" />
                <p className="text-[10px] uppercase font-black tracking-[0.2em] text-slate-500">Real-Time Grid Intelligence</p>
            </div>
        </div>

        <nav className="grid grid-cols-2 md:grid-cols-3 lg:flex gap-3 w-full lg:w-auto" aria-label="Main navigation">
            {NAV_LINKS.map((link) => (
                <NavLink key={link.to} {...link} />
            ))}
            <NetworkTargetSelector
                apiTarget={apiTarget}
                setApiTarget={setApiTarget}
                availableTargets={availableTargets}
                removeTarget={removeTarget}
                isConnected={isConnected}
            />
        </nav>
    </header>
));

DashboardHeader.displayName = 'DashboardHeader';
