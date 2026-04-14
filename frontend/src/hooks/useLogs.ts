import { useState, useCallback } from 'react';
import type { Reading, LogEntry } from '@/lib/types';
import { formatTimestamp } from '@/lib/common';

/**
 * Hook for managing console logs with max entries limit
 */
export function useLogs(maxEntries: number = 100) {
    const [logs, setLogs] = useState<LogEntry[]>([]);

    const addLog = useCallback((message: string, type: LogEntry['type'], reading?: Reading) => {
        const entry: LogEntry = {
            timestamp: formatTimestamp(),
            message,
            type,
            reading
        };
        setLogs(prev => [entry, ...prev].slice(0, maxEntries));
    }, [maxEntries]);

    const clearLogs = useCallback(() => setLogs([]), []);

    return { logs, addLog, clearLogs };
}
