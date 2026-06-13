import { cn } from '@/lib/common';

interface MetricItemProps {
    label: string;
    value: string;
    unit: string;
    color: string;
    status: 'good' | 'warning';
}

// High-Performance HMI: grayscale value; color only when the metric is out of band.
export const MetricItem = ({ label, value, unit, status }: MetricItemProps) => (
    <div className="text-center">
        <div className="hmi-lbl mb-1">{label}</div>
        <div className={cn('text-sm mono', status === 'warning' ? 'text-[var(--warn)]' : 'text-[var(--txt-val)]')}>
            {value}<span className="text-[8px] ml-0.5 text-[var(--lbl)] uppercase">{unit}</span>
        </div>
        {status === 'warning' && (
            <div className="text-[8px] text-[var(--warn)] mt-0.5 uppercase tracking-wide">⚠ Check</div>
        )}
    </div>
);
