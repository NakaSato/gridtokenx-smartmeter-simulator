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

// HMI: neutral by default; status color only where the action carries meaning
// (caution = warn/amber, stop/destructive = alarm/red). Start/primary stay neutral-bright.
const variantClasses: Record<ControlButtonProps['variant'], string> = {
    emerald: "hmi-btn primary",
    amber: "hmi-btn warn",
    blue: "hmi-btn",
    rose: "hmi-btn alarm",
    indigo: "hmi-btn primary",
};

export const ControlButton = memo(({ onClick, disabled, variant, icon: Icon, active }: ControlButtonProps) => {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={cn(
                "p-4",
                variantClasses[variant],
                active && "active"
            )}
            aria-label={`${variant} action`}
        >
            <Icon className="fill-current w-5 h-5" />
        </button>
    );
});

ControlButton.displayName = 'ControlButton';
