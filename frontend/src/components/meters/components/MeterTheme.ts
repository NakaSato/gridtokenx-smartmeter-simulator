export interface MeterTheme {
    primary: string;
    gradient: string;
    border: string;
    accent: string;
    icon: string;
    glow: string;
}

const themeColors: Record<string, MeterTheme> = {
    Solar_Prosumer: {
        primary: 'emerald',
        gradient: 'from-emerald-500/20 via-emerald-500/5 to-transparent',
        border: 'border-emerald-500/30',
        accent: 'bg-emerald-500',
        icon: 'text-emerald-400',
        glow: 'shadow-emerald-500/20',
    },
    Grid_Consumer: {
        primary: 'blue',
        gradient: 'from-blue-500/20 via-blue-500/5 to-transparent',
        border: 'border-blue-500/30',
        accent: 'bg-blue-500',
        icon: 'text-blue-400',
        glow: 'shadow-blue-500/20',
    },
    Hybrid_Prosumer: {
        primary: 'violet',
        gradient: 'from-violet-500/20 via-violet-500/5 to-transparent',
        border: 'border-violet-500/30',
        accent: 'bg-violet-500',
        icon: 'text-violet-400',
        glow: 'shadow-violet-500/20',
    },
    Battery_Storage: {
        primary: 'amber',
        gradient: 'from-amber-500/20 via-amber-500/5 to-transparent',
        border: 'border-amber-500/30',
        accent: 'bg-amber-500',
        icon: 'text-amber-400',
        glow: 'shadow-amber-500/20',
    },
    EV_Charger: {
        primary: 'cyan',
        gradient: 'from-cyan-500/20 via-cyan-500/5 to-transparent',
        border: 'border-cyan-500/30',
        accent: 'bg-cyan-500',
        icon: 'text-cyan-400',
        glow: 'shadow-cyan-500/20',
    },
    DC_Fast_Charger: {
        primary: 'orange',
        gradient: 'from-orange-500/20 via-orange-500/5 to-transparent',
        border: 'border-orange-500/30',
        accent: 'bg-orange-500',
        icon: 'text-orange-400',
        glow: 'shadow-orange-500/20',
    },
};

const defaultTheme: MeterTheme = {
    primary: 'slate',
    gradient: 'from-slate-500/20 via-slate-500/5 to-transparent',
    border: 'border-slate-500/30',
    accent: 'bg-slate-500',
    icon: 'text-slate-400',
    glow: 'shadow-slate-500/20',
};

export function getMeterTheme(meterType: string): MeterTheme {
    return themeColors[meterType] || defaultTheme;
}
