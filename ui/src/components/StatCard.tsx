import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export const StatCard = ({ title, value, unit, icon, color }: { title: string, value: string, unit: string, icon: React.ReactNode, color: string }) => {
    const colorMap: Record<string, string> = {
        emerald: "shadow-emerald-500/10 border-emerald-500/20",
        blue: "shadow-blue-500/10 border-blue-500/20",
        purple: "shadow-purple-500/10 border-purple-500/20",
        rose: "shadow-rose-500/10 border-rose-500/20"
    };

    return (
        <div className={cn("glass rounded-[2rem] p-6 space-y-4 shadow-2xl transition-all hover:-translate-y-1 border", colorMap[color])}>
            <div className="flex justify-between items-center">
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{title}</span>
                <div className="p-2 bg-slate-900 rounded-xl">{icon}</div>
            </div>
            <div>
                <span className="text-4xl font-black">{value}</span>
                <span className="text-xs font-black text-slate-500 ml-2 uppercase tracking-widest">{unit}</span>
            </div>
        </div>
    );
};
