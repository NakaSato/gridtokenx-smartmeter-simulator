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

// High-Performance HMI KPI card: flat panel, 1px border, mono value, status chip.
// Color appears only via `status` (ok/warn/alarm) — never decoratively.
const STATUS_CLASS: Record<string, string> = {
    success: 'ok',
    warning: 'warn',
    error: 'alarm',
    info: 'info',
    neutral: '',
};

export const StatCard = ({ title, value, unit, status, trend, trendLabel }: StatCardProps) => {
    const chip = status ? STATUS_CLASS[status] : '';
    const trendUp = (typeof trend === 'number' && trend > 0) || (typeof trend === 'string' && !trend.startsWith('-'));

    return (
        <div className="hmi-kpi">
            <div className="top">
                <span className="hmi-lbl">{title}</span>
                {status && status !== 'neutral' && (
                    <span className={cn('hmi-chip', chip)}>{status}</span>
                )}
            </div>
            <div className="num">
                <span className={cn('hmi-val mono', chip)}>{value}</span>
                <span className="hmi-unit">{unit}</span>
            </div>
            {trend && (
                <div className="sub flex items-center gap-2">
                    <span className={cn('mono', trendUp ? 'text-[var(--ok)]' : 'text-[var(--alarm)]')}>
                        {typeof trend === 'number' && trend > 0 ? '+' : ''}{trend}
                    </span>
                    <span className="hmi-lbl">{trendLabel || 'trend'}</span>
                </div>
            )}
        </div>
    );
};
