import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { ApiError, Reading } from './types';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function formatTimestamp(date: Date = new Date()): string {
    return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
}

export function createApiError(message: string, code?: string): ApiError {
    return {
        message,
        code,
        timestamp: new Date().toISOString(),
    };
}

export function calculateEnergyMW(
    readings: Reading[],
    field: 'energy_generated' | 'energy_consumed' | 'surplus_energy' | 'deficit_energy',
    preferPower = false
): number {
    const powerField = field === 'energy_generated'
        ? 'generation_kw'
        : field === 'energy_consumed'
            ? 'consumption_kw'
            : undefined;

    const totalKw = readings.reduce((sum, reading) => {
        if (preferPower && powerField && typeof reading[powerField] === 'number') {
            return sum + (reading[powerField] ?? 0);
        }
        return sum + (reading[field] ?? 0);
    }, 0);

    return totalKw / 1000;
}
