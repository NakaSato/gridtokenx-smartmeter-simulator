import { useState, useMemo, useCallback } from 'react';
import type { Reading } from '@/lib/types';

/**
 * Hook for pagination logic
 */
export function usePagination<T>(
    items: T[],
    itemsPerPage: number,
    searchQuery: string,
    meterTypeFilter: string,
    statusFilter: string
) {
    const [currentPage, setCurrentPage] = useState(1);
    const [prevFilters, setPrevFilters] = useState({ searchQuery, meterTypeFilter, statusFilter });

    if (searchQuery !== prevFilters.searchQuery || 
        meterTypeFilter !== prevFilters.meterTypeFilter || 
        statusFilter !== prevFilters.statusFilter) {
      setPrevFilters({ searchQuery, meterTypeFilter, statusFilter });
      setCurrentPage(1);
    }

    const filteredItems = useMemo(() => {
        if (!searchQuery.trim() && meterTypeFilter === 'all' && statusFilter === 'all') return items;
        
        const query = searchQuery.toLowerCase();
        return items.filter(item => {
            const reading = item as unknown as Reading;
            
            // Search filter
            const matchesSearch = !searchQuery.trim() || 
                reading.meter_id?.toLowerCase().includes(query) ||
                reading.location?.toLowerCase().includes(query);
            
            // Type filter
            const matchesType = meterTypeFilter === 'all' || 
                reading.meter_type?.toLowerCase() === meterTypeFilter.toLowerCase();
            
            // Status filter (producer/consumer based on generation vs consumption)
            let matchesStatus = true;
            if (statusFilter !== 'all') {
                const isProducer = (reading.energy_generated || 0) > (reading.energy_consumed || 0);
                const isConsumer = (reading.energy_consumed || 0) > (reading.energy_generated || 0);
                const hasBattery = (reading.battery_level || 0) > 0;
                
                if (statusFilter === 'producing') matchesStatus = isProducer;
                else if (statusFilter === 'consuming') matchesStatus = isConsumer;
                else if (statusFilter === 'battery') matchesStatus = hasBattery;
            }
            
            return matchesSearch && matchesType && matchesStatus;
        });
    }, [items, searchQuery, meterTypeFilter, statusFilter]);

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
