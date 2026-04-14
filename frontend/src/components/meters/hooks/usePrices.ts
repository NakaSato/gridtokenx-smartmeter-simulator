import { useState, useCallback } from 'react';
import type {
    PriceCompareRequest,
    PriceCompareResponse,
    UtilityRatesResponse,
    P2PCalculateCostRequest,
    P2PCalculateCostResponse
} from '@/lib/types';

interface UsePricesResult {
    // Price comparison
    comparePrices: (request: PriceCompareRequest) => Promise<PriceCompareResponse | null>;
    // Utility rates
    getUtilityRates: () => Promise<UtilityRatesResponse | null>;
    // P2P cost calculation
    calculateP2PCost: (request: P2PCalculateCostRequest) => Promise<P2PCalculateCostResponse | null>;
    // Loading and error states
    isLoading: boolean;
    error: string | null;
}

/**
 * Hook for price-related API calls
 * 
 * Provides methods to:
 * - Compare utility vs P2P prices
 * - Get utility rate information
 * - Calculate P2P transaction costs
 * 
 * @param getApiUrl - Function to get API URL with base path
 * @returns Price API methods and state
 */
export const usePrices = (getApiUrl: (path: string) => string): UsePricesResult => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    /**
     * Compare utility vs P2P prices
     */
    const comparePrices = useCallback(async (
        request: PriceCompareRequest
    ): Promise<PriceCompareResponse | null> => {
        setIsLoading(true);
        setError(null);

        try {
            const res = await fetch(getApiUrl('/api/v1/market/price/compare'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }

            const data = await res.json();
            return data;
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to compare prices';
            setError(errorMessage);
            return null;
        } finally {
            setIsLoading(false);
        }
    }, [getApiUrl]);

    /**
     * Get utility rates information
     */
    const getUtilityRates = useCallback(async (): Promise<UtilityRatesResponse | null> => {
        setIsLoading(true);
        setError(null);

        try {
            const res = await fetch(getApiUrl('/api/v1/market/price/utility-rates'), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }

            const data = await res.json();
            return data;
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to get utility rates';
            setError(errorMessage);
            return null;
        } finally {
            setIsLoading(false);
        }
    }, [getApiUrl]);

    /**
     * Calculate P2P transaction cost
     */
    const calculateP2PCost = useCallback(async (
        request: P2PCalculateCostRequest
    ): Promise<P2PCalculateCostResponse | null> => {
        setIsLoading(true);
        setError(null);

        try {
            const res = await fetch(getApiUrl('/api/v1/market/p2p/calculate-cost'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }

            const data = await res.json();
            return data;
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to calculate P2P cost';
            setError(errorMessage);
            return null;
        } finally {
            setIsLoading(false);
        }
    }, [getApiUrl]);

    return {
        comparePrices,
        getUtilityRates,
        calculateP2PCost,
        isLoading,
        error,
    };
};
