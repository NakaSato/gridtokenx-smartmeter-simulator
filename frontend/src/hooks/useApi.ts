import { useState, useCallback } from 'react';
import type { LogType, ApiError } from '@/lib/types';
import { createApiError } from '@/lib/common';

/**
 * Hook for API operations with error handling
 */
export function useApi(getApiUrl: (path: string) => string, addLog: (message: string, type: LogType) => void) {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const apiCall = useCallback(async <T,>(
        path: string,
        options: RequestInit = {},
        successMessage?: string,
        errorMessage?: string
    ): Promise<T | null> => {
        setIsLoading(true);
        setError(null);

        try {
            const res = await fetch(getApiUrl(path), {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });

            if (!res.ok) {
                let errorMsg = `HTTP ${res.status}: ${res.statusText}`;
                try {
                    const errorData = await res.json();
                    if (errorData.detail) {
                        errorMsg = errorData.detail;
                        if (errorData.suggestion) {
                            errorMsg += `. Suggestion: ${errorData.suggestion}`;
                        }
                    }
                } catch {
                    // Fallback to message string if not JSON
                }
                throw new Error(errorMsg);
            }

            const data = await res.json();

            if (!data.success && data.success !== undefined) {
                throw new Error(data.message || 'Operation failed');
            }

            if (successMessage) {
                addLog(successMessage, 'success');
            }

            return data;
        } catch (e) {
            const err = e instanceof Error ? e : new Error(String(e));
            const apiErr = createApiError(errorMessage || err.message);
            setError(apiErr);
            addLog(errorMessage || err.message, 'error');
            return null;
        } finally {
            setIsLoading(false);
        }
    }, [getApiUrl, addLog]);

    return { apiCall, isLoading, error, clearError: () => setError(null) };
}
