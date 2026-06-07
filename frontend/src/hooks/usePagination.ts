import { useState, useMemo, useCallback } from 'react';
import type { Reading } from '@/lib/types';

/**
 * Hook for pagination logic
 */
// Net power balance (kW), preferring instantaneous power, falling back to per-interval energy.
function netBalance(r: Reading): number {
    const gen = r.generation_kw ?? r.energy_generated ?? 0;
    const cons = r.consumption_kw ?? r.energy_consumed ?? 0;
    return gen - cons;
}

// Comparators keyed by the sort dropdown value. Each sorts a *copy* of the filtered list.
const SORTERS: Record<string, (a: Reading, b: Reading) => number> = {
    balance_desc: (a, b) => netBalance(b) - netBalance(a),
    balance_asc: (a, b) => netBalance(a) - netBalance(b),
    name: (a, b) => (a.location_name || a.meter_id).localeCompare(b.location_name || b.meter_id),
    generation: (a, b) => (b.generation_kw ?? b.energy_generated ?? 0) - (a.generation_kw ?? a.energy_generated ?? 0),
    consumption: (a, b) => (b.consumption_kw ?? b.energy_consumed ?? 0) - (a.consumption_kw ?? a.energy_consumed ?? 0),
    voltage: (a, b) => (a.voltage_pu ?? 1) - (b.voltage_pu ?? 1),
    battery: (a, b) => (b.battery_level || 0) - (a.battery_level || 0),
};

export function usePagination<T>(
    items: T[],
    itemsPerPage: number,
    searchQuery: string,
    meterTypeFilter: string,
    statusFilter: string,
    sortKey: string = 'default'
) {
    const [currentPage, setCurrentPage] = useState(1);
    const [prevFilters, setPrevFilters] = useState({ searchQuery, meterTypeFilter, statusFilter, sortKey });

    if (searchQuery !== prevFilters.searchQuery ||
        meterTypeFilter !== prevFilters.meterTypeFilter ||
        statusFilter !== prevFilters.statusFilter ||
        sortKey !== prevFilters.sortKey) {
      setPrevFilters({ searchQuery, meterTypeFilter, statusFilter, sortKey });
      setCurrentPage(1);
    }

    const filteredItems = useMemo(() => {
        const query = searchQuery.toLowerCase();
        const noFilter = !searchQuery.trim() && meterTypeFilter === 'all' && statusFilter === 'all';

        const base = noFilter ? items : items.filter(item => {
            const reading = item as unknown as Reading;

            // Search filter
            const matchesSearch = !searchQuery.trim() ||
                reading.meter_id?.toLowerCase().includes(query) ||
                reading.location?.toLowerCase().includes(query) ||
                reading.location_name?.toLowerCase().includes(query);

            // Type filter
            const matchesType = meterTypeFilter === 'all' ||
                reading.meter_type?.toLowerCase() === meterTypeFilter.toLowerCase();

            // Status filter
            let matchesStatus = true;
            if (statusFilter !== 'all') {
                const isProducer = netBalance(reading) > 0;
                if (statusFilter === 'producing') matchesStatus = isProducer;
                else if (statusFilter === 'consuming') matchesStatus = !isProducer;
                else if (statusFilter === 'battery') matchesStatus = (reading.battery_level || 0) > 0;
                else if (statusFilter === 'compromised') matchesStatus = !!(reading.is_compromised || (reading.norm_residual && reading.norm_residual > 4.0));
                else if (statusFilter === 'shed') matchesStatus = !!reading.is_shed;
            }

            return matchesSearch && matchesType && matchesStatus;
        });

        const sorter = SORTERS[sortKey];
        if (!sorter) return base;
        // Copy before sort so we never mutate the caller's array in place.
        return [...base].sort((x, y) => sorter(x as unknown as Reading, y as unknown as Reading));
    }, [items, searchQuery, meterTypeFilter, statusFilter, sortKey]);

    const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
    const paginatedItems = useMemo(() => {
        const start = (currentPage - 1) * itemsPerPage;
        return filteredItems.slice(start, start + itemsPerPage);
    }, [filteredItems, currentPage, itemsPerPage]);

    const goToPage = useCallback((page: number) => {
        setCurrentPage(Math.max(1, Math.min(page, totalPages)));
    }, [totalPages]);

    const nextPage = useCallback(() => {
        goToPage(currentPage + 1);
    }, [currentPage, goToPage]);

    const prevPage = useCallback(() => {
        goToPage(currentPage - 1);
    }, [currentPage, goToPage]);

    return {
        currentPage,
        totalPages,
        paginatedItems,
        filteredItems,
        goToPage,
        nextPage,
        prevPage,
        totalItems: filteredItems.length,
        startIndex: (currentPage - 1) * itemsPerPage + 1,
        endIndex: Math.min(currentPage * itemsPerPage, filteredItems.length),
    };
}
