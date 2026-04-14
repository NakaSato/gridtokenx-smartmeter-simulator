import { useState, useEffect, useCallback, useRef } from 'react';
import type { LogType } from '@/lib/types';

/**
 * Hook for WebSocket connection management with auto-reconnect
 */
export function useWebSocket(
    wsUrl: string,
    onMessage: (data: unknown) => void,
    addLog: (message: string, type: LogType) => void,
    reconnectDelayMs: number = 5000
) {
    const wsRef = useRef<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const isUnmountedRef = useRef(false);
    const connectRef = useRef<() => void>(undefined);

    const connect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
        }

        try {
            wsRef.current = new WebSocket(wsUrl);

            wsRef.current.onopen = () => {
                if (!isUnmountedRef.current) {
                    setIsConnected(true);
                    addLog('WebSocket connected', 'success');

                    // Subscribe to market events (required by API Gateway's new Pub/Sub model)
                    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                        wsRef.current.send(JSON.stringify({ type: 'subscribe', channel: 'market_events' }));
                    }
                }
            };

            wsRef.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    onMessage(data);
                } catch {
                    addLog('Error parsing message', 'error');
                }
            };

            wsRef.current.onclose = () => {
                if (!isUnmountedRef.current) {
                    setIsConnected(false);
                    addLog('WebSocket disconnected. Retrying...', 'warning');
                    reconnectTimeoutRef.current = setTimeout(() => {
                        if (connectRef.current) connectRef.current();
                    }, reconnectDelayMs);
                }
            };

            wsRef.current.onerror = () => {
                addLog('WebSocket connection error', 'error');
            };
        } catch {
            addLog('Failed to create WebSocket connection', 'error');
        }
    }, [wsUrl, onMessage, addLog, reconnectDelayMs]);

    useEffect(() => {
        connectRef.current = connect;
    }, [connect]);

    const disconnect = useCallback(() => {
        isUnmountedRef.current = true;
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
        }
    }, []);

    useEffect(() => {
        isUnmountedRef.current = false;
        connect();
        return disconnect;
    }, [connect, disconnect]);

    return { isConnected, wsRef };
}
