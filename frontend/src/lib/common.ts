import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { ApiError, Reading } from './types';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

/**
 * Opaque id for client-side list keys.
 *
 * `crypto.randomUUID` only exists in a secure context, so it is missing when the
 * dev server is reached over plain http on a LAN address (http://192.168.x.x:3000)
 * — hence the fallback. These ids never leave the browser, so non-crypto entropy
 * is fine.
 */
export function randomId(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
    }
    return `id-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * Copy text to the clipboard, returning whether it worked.
 *
 * `navigator.clipboard` is secure-context-only and therefore undefined when the
 * dashboard is reached over plain http on a LAN address — same constraint as
 * {@link randomId}. Falls back to the deprecated `execCommand('copy')`, which
 * still works in insecure contexts.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
    try {
        if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(text);
            return true;
        }
    } catch {
        // Fall through — permission denied or not focused; try execCommand.
    }

    try {
        const el = document.createElement('textarea');
        el.value = text;
        el.setAttribute('readonly', '');
        el.style.position = 'fixed';
        el.style.opacity = '0';
        document.body.appendChild(el);
        el.select();
        const ok = document.execCommand('copy');
        document.body.removeChild(el);
        return ok;
    } catch {
        return false;
    }
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
