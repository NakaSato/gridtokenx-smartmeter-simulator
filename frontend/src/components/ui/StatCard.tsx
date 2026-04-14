import React from 'react';
import { cn } from '@/lib/common';

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
            warning: "purple",
            error: "rose",
            info: "blue",
            neutral: "slate"
        };
        activeColor = statusMap[status] || "blue";
    }

    const themeMap: Record<string, { shadow: string, border: string, bg: string, text: string }> = {
        emerald: { shadow: "shadow-emerald-500/10 hover:shadow-emerald-500/20", border: "border-emerald-500/20", bg: "from-emerald-500/10 to-emerald-500/5", text: "text-emerald-400" },
        blue: { shadow: "shadow-blue-500/10 hover:shadow-blue-500/20", border: "border-blue-500/20", bg: "from-blue-500/10 to-blue-500/5", text: "text-blue-400" },
        purple: { shadow: "shadow-purple-500/10 hover:shadow-purple-500/20", border: "border-purple-500/20", bg: "from-purple-500/10 to-purple-500/5", text: "text-purple-400" },
        rose: { shadow: "shadow-rose-500/10 hover:shadow-rose-500/20", border: "border-rose-500/20", bg: "from-rose-500/10 to-rose-500/5", text: "text-rose-400" },
        slate: { shadow: "shadow-slate-500/10 hover:shadow-slate-500/20", border: "border-slate-500/20", bg: "from-slate-500/10 to-slate-500/5", text: "text-slate-400" },
        indigo: { shadow: "shadow-indigo-500/10 hover:shadow-indigo-500/20", border: "border-indigo-500/20", bg: "from-indigo-500/10 to-indigo-500/5", text: "text-indigo-400" }
    };

    const theme = themeMap[activeColor || "blue"] || themeMap["blue"];

    return (
        <div className={cn(
            "group relative overflow-hidden rounded-[2.5rem] p-6 space-y-4 transition-all duration-300",
            "bg-gradient-to-br backdrop-blur-3xl shadow-xl border hover:-translate-y-1 hover:scale-[1.01]",
            theme.bg, theme.border, theme.shadow
        )}>
            <div className="flex justify-between items-center relative z-10">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">{title}</span>
                <div className="p-3 bg-slate-900/40 rounded-2xl border border-white/5 group-hover:bg-slate-900/60 transition-colors">
                    {icon}
                </div>
            </div>
            <div className="relative z-10">
                <span className="text-4xl font-black bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60 tracking-tight">
                    {value}
                </span>
                <span className="text-[10px] font-black text-slate-500 ml-3 uppercase tracking-widest">{unit}</span>
            </div>
            {trend && (
                <div className="flex items-center gap-2 pt-4 border-t border-white/5 relative z-10">
                    <span className={cn(
                        "text-xs font-black",
                        (typeof trend === 'number' && trend > 0) || (typeof trend === 'string' && !trend.startsWith('-'))
                            ? "text-emerald-400" : "text-rose-400"
                    )}>
                        {typeof trend === 'number' && trend > 0 ? '+' : ''}{trend}
                    </span>
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest opacity-60">{trendLabel || 'trend'}</span>
                </div>
            )}

            {/* Decorative Glow */}
            <div className={cn("absolute -bottom-12 -right-12 w-32 h-32 rounded-full blur-[60px] opacity-20 transition-opacity group-hover:opacity-40", theme.bg)} />
        </div>
    );
};
