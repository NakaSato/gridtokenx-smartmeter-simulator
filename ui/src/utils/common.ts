import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { Reading, ApiError } from '../types';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Formats energy value from readings to MW
 */
export const calculateEnergyMW = (readings: Reading[], key: 'energy_generated' | 'energy_consumed'): number => {
    return readings.reduce((acc, r) => acc + (r[key] || 0), 0) * 4.0 / 1000.0;
};

/**
 * Creates a timestamp string for logging
 */
export const formatTimestamp = (): string => new Date().toLocaleTimeString();

/**
 * Creates an API error object
 */
export const createApiError = (message: string, code?: string): ApiError => ({
    message,
    code,
    timestamp: formatTimestamp(),
});
