import { cn } from '@/lib/common';

interface MetricItemProps {
    label: string;
    value: string;
    unit: string;
    color: string;
    status: 'good' | 'warning';
}

export const MetricItem = ({ label, value, unit, color, status }: MetricItemProps) => (
    <div className="text-center">
        <div className="text-[9px] font-black uppercase tracking-wider text-slate-500 mb-1">{label}</div>
        <div className={cn('font-black text-sm', color)}>
            {value}<span className="text-[8px] ml-0.5 opacity-40 uppercase">{unit}</span>
        </div>
        {status === 'warning' && (
            <div className="text-[6px] font-bold text-amber-400 mt-0.5">⚠ Check</div>
        )}
    </div>
);
