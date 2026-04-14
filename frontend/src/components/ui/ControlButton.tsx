import { memo } from 'react';
import type { ElementType } from 'react';
import { cn } from '@/lib/common';

interface ControlButtonProps {
    onClick: () => void;
    disabled?: boolean;
    variant: 'emerald' | 'amber' | 'blue' | 'rose' | 'indigo';
    icon: ElementType;
    active?: boolean;
}

export const ControlButton = memo(({ onClick, disabled, variant, icon: Icon, active }: ControlButtonProps) => {
    const variantClasses = {
        emerald: !disabled ? "bg-emerald-500 text-white hover:bg-emerald-400 hover:shadow-emerald-500/20" : "bg-slate-800 text-slate-600 grayscale",
        amber: !disabled ? "bg-amber-500 text-white hover:bg-amber-400 hover:shadow-amber-500/20" : "bg-slate-800 text-slate-600 grayscale",
        blue: !disabled ? "bg-blue-500 text-white hover:bg-blue-400 hover:shadow-blue-500/20" : "bg-slate-800 text-slate-600 grayscale",
        rose: !disabled ? "bg-rose-500 text-white hover:bg-rose-400 hover:shadow-rose-500/20" : "bg-slate-800 text-slate-600 grayscale",
        indigo: "bg-indigo-500 text-white hover:bg-indigo-400 shadow-indigo-500/20",
    };

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={cn(
                "p-4 rounded-2xl flex items-center justify-center transition-all shadow-lg active:scale-95",
                variantClasses[variant],
                active && "ring-2 ring-white/50 ring-offset-2 ring-offset-slate-900 scale-105 shadow-xl"
            )}
            aria-label={`${variant} action`}
        >
            <Icon className="fill-current w-5 h-5" />
        </button>
    );
});

ControlButton.displayName = 'ControlButton';
