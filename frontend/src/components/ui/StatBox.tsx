import React from 'react';
import { Coins } from 'lucide-react';
import { cn } from '@/lib/common';
import type { MeterTheme } from '@/components/meters/components/MeterTheme';

interface StatBoxProps {
    icon?: React.ElementType;
    iconColor?: string;
    label: string;
    value: string;
    unit: string;
    theme: MeterTheme;
    badge?: string;
    price?: number;
}

// High-Performance HMI: flat panel, grayscale, no gradient/glow/scale.
export const StatBox = ({ icon: Icon, label, value, unit, badge, price }: StatBoxProps) => {
    return (
        <div className="hmi-panel p-3.5">
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    {Icon ? <Icon className="w-3.5 h-3.5 text-[var(--lbl)]" /> : null}
                    <span className="hmi-lbl">{label}</span>
                </div>
                {badge ? <span className="hmi-chip">{badge}</span> : null}
            </div>
            <div className="space-y-1">
                <div className="text-[var(--txt-val)] text-lg mono">
                    {value}<span className="text-[9px] ml-1 text-[var(--lbl)]">{unit}</span>
                </div>
                {price !== undefined && price > 0 ? (
                    <div className={cn('flex items-center gap-1.5 px-2 py-1 bg-[var(--bar-bg)] border border-[var(--line)]')}>
                        <Coins className="w-3 h-3 text-[var(--lbl)]" />
                        <span className="text-xs mono text-[var(--txt)]">{price.toFixed(2)} ฿</span>
                    </div>
                ) : null}
            </div>
        </div>
    );
};
