export interface MeterTheme {
    primary: string;
    gradient: string;
    border: string;
    accent: string;
    icon: string;
    glow: string;
}

// High-Performance HMI: meter types are NOT color-coded. Every type resolves to
// the same flat grayscale treatment — color is reserved for status (alarm/warn/ok).
// Fields kept for API compatibility with existing consumers (StatBox, EditMeterModal).
const neutral: MeterTheme = {
    primary: 'neutral',
    gradient: '',
    border: 'border-[var(--line-2)]',
    accent: 'bg-[var(--lbl)]',
    icon: 'text-[var(--lbl)]',
    glow: '',
};

export function getMeterTheme(meterType: string): MeterTheme {
    void meterType; // type no longer drives color in HMI; kept for API compatibility
    return neutral;
}
