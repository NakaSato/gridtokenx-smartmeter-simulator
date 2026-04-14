import React from 'react';
import { Coins } from 'lucide-react';
import { cn } from '@/lib/common';
import type { MeterTheme } from '@/components/meters/components/MeterTheme';

interface StatBoxProps {
    icon: React.ElementType;
    iconColor: string;
    label: string;
    value: string;
    unit: string;
    theme: MeterTheme;
    badge?: string;
    price?: number;
}

export const StatBox = ({ icon: Icon, iconColor, label, value, unit, theme, badge, price }: StatBoxProps) => (
    <div className={cn(
        'relative group/stat bg-slate-900/40 p-3.5 rounded-2xl border border-white/5 overflow-hidden transition-all duration-300',
        'hover:bg-slate-900/60 hover:border-white/10 hover:scale-[1.02]'
    )}>
        <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
                <Icon className={cn('w-3.5 h-3.5', iconColor)} />
                <span className="text-[9px] font-black uppercase tracking-wider text-slate-500">{label}</span>
            </div>
            {badge && (
                <span className={cn(
                    'text-[7px] font-black uppercase tracking-wider px-1.5 py-0.5 rounded-md',
                    theme.accent.replace('bg-', 'bg-').replace('500', '500/20'),
                    theme.icon
                )}>
                    {badge}
                </span>
            )}
        </div>
        <div className="space-y-1">
            <div className={cn('font-black text-lg', iconColor)}>
                {value}<span className="text-[9px] ml-1 opacity-50">{unit}</span>
            </div>
            {price !== undefined && price > 0 && (
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-slate-800/50 border border-white/5">
                    <Coins className="w-3 h-3 text-amber-400" />
                    <span className="text-xs font-bold text-amber-400">{price.toFixed(2)} ฿</span>
                </div>
            )}
        </div>
    </div>
);
