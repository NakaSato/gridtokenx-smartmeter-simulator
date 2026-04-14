import { memo } from 'react';

export const DashboardHeader = memo(() => (
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
    </header>
));

DashboardHeader.displayName = 'DashboardHeader';
