import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface StatCardProps {
    title: string;
    value: string | number;
    unit: string;
    icon: React.ReactNode;
    color?: string;
    status?: 'success' | 'warning' | 'error' | 'info' | 'neutral';
    trend?: string | number;
    trendLabel?: string;
}

export const StatCard = ({ title, value, unit, icon, color, status, trend, trendLabel }: StatCardProps) => {

    let activeColor = color;
    if (!activeColor && status) {
        const statusMap: Record<string, string> = {
            success: "emerald",
            warning: "purple", // using purple for warning to match dashboard style
            error: "rose",
            info: "blue",
            neutral: "slate"
        };
        activeColor = statusMap[status] || "blue";
    }

    const colorMap: Record<string, string> = {
        emerald: "shadow-emerald-500/10 border-emerald-500/20",
        blue: "shadow-blue-500/10 border-blue-500/20",
        purple: "shadow-purple-500/10 border-purple-500/20",
        rose: "shadow-rose-500/10 border-rose-500/20",
        slate: "shadow-slate-500/10 border-slate-500/20",
        indigo: "shadow-indigo-500/10 border-indigo-500/20"
    };

    const finalColorClass = colorMap[activeColor || "blue"] || colorMap["blue"];

    return (
        <div className={cn("glass rounded-[2rem] p-6 space-y-4 shadow-2xl transition-all hover:-translate-y-1 border", finalColorClass)}>
            <div className="flex justify-between items-center">
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{title}</span>
                <div className="p-2 bg-slate-900 rounded-xl">{icon}</div>
            </div>
            <div>
                <span className="text-4xl font-black">{value}</span>
                <span className="text-xs font-black text-slate-500 ml-2 uppercase tracking-widest">{unit}</span>
            </div>
            {trend && (
                <div className="flex items-center gap-2 pt-2 border-t border-white/5">
                    <span className={cn(
                        "text-xs font-bold",
                        (typeof trend === 'number' && trend > 0) || (typeof trend === 'string' && !trend.startsWith('-'))
                            ? "text-emerald-400" : "text-rose-400"
                    )}>
                        {typeof trend === 'number' && trend > 0 ? '+' : ''}{trend}
                    </span>
                    <span className="text-[10px] font-medium text-slate-500 uppercase tracking-widest">{trendLabel || 'trend'}</span>
                </div>
            )}
        </div>
    );
};
