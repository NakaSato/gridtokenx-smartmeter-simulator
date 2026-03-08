import { useState, useEffect, useCallback, useRef, useMemo, memo } from 'react';
import {
    Play,
    Square,
    Pause,
    RotateCcw,
    Activity,
    Zap,
    Sun,
    Terminal,
    Search,
    Database,
    History,
    Shield,
    ShieldAlert,
    AlertTriangle,
    Settings,
    ChevronLeft,
    ChevronRight,
    Box,
    Map as MapIcon,
    Plus,
    TrendingUp,
    LayoutGrid,
    List as ListIcon,
    Globe,
    ChevronDown,
    Trash2
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { MeterCard } from '../components/MeterCard';
import { MeterListItem } from '../components/MeterListItem';
import { StatCard } from '../components/StatCard';
import { SolarDetection } from '../components/SolarDetection';
import AddMeterModal from '../components/AddMeterModal';
import { useNetwork } from '../context/NetworkContext';
import type { Reading, GridHealth, AttackAlert } from '../types';

// =============================================================================
// Constants
// =============================================================================

const LOG_MAX_ENTRIES = 100;
const WS_RECONNECT_DELAY_MS = 5000;
const STATUS_REFRESH_DELAY_MS = 1000;
const DEFAULT_METER_COUNT = 20;
const DEFAULT_ITEMS_PER_PAGE_GRID = 6;
const DEFAULT_ITEMS_PER_PAGE_LIST = 10;

const ATTACK_MODES = ['bias', 'scale', 'random'] as const;
type AttackMode = typeof ATTACK_MODES[number];

const NAV_LINKS = [
    { to: "/vpp", icon: Box, label: "Manage", title: "VPP Ops", color: "emerald" },
    { to: "/map", icon: MapIcon, label: "View", title: "Grid Map", color: "indigo" },
    { to: "/adr", icon: Activity, label: "Control", title: "ADR Ops", color: "rose" },
    { to: "/resilience", icon: Shield, label: "Safety", title: "Resilience", color: "amber" },
] as const;

// =============================================================================
// Types
// =============================================================================

interface LogEntry {
    timestamp: string;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error' | 'reading';
    reading?: Reading;
}

interface SimulatorStatus {
    running: boolean;
    paused: boolean;
    num_meters: number;
    mode: 'random' | 'playback' | '-';
    health: Partial<GridHealth>;
}

interface AttackStatus {
    active: boolean;
    targets: string[];
    mode: AttackMode;
    bias_kw: number;
}

interface AttackConfig {
    active: boolean;
    targets: string[];
    mode: AttackMode;
    bias: number;
    stealthy: boolean;
    scale: number;
}

interface ApiError {
    message: string;
    code?: string;
    timestamp: string;
}

// =============================================================================
// Utility Functions
// =============================================================================

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

/**
 * Formats energy value from readings to MW
 * @param readings - Array of readings
 * @param key - Property to sum ('energy_generated' | 'energy_consumed')
 * @returns Value in MW
 */
const calculateEnergyMW = (readings: Reading[], key: 'energy_generated' | 'energy_consumed'): number => {
    return readings.reduce((acc, r) => acc + (r[key] || 0), 0) * 4.0 / 1000.0;
};

/**
 * Creates a timestamp string for logging
 */
const formatTimestamp = (): string => new Date().toLocaleTimeString();

/**
 * Creates an API error object
 */
const createApiError = (message: string, code?: string): ApiError => ({
    message,
    code,
    timestamp: formatTimestamp(),
});

// =============================================================================
// Custom Hooks
// =============================================================================

/**
 * Hook for managing console logs with max entries limit
 */
function useLogs(maxEntries: number = LOG_MAX_ENTRIES) {
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

/**
 * Hook for WebSocket connection management with auto-reconnect
 */
function useWebSocket(
    wsUrl: string,
    onMessage: (data: any) => void,
    addLog: (message: string, type: LogEntry['type']) => void
) {
    const wsRef = useRef<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const isUnmountedRef = useRef(false);

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
                } catch (e) {
                    addLog('Error parsing message', 'error');
                }
            };

            wsRef.current.onclose = () => {
                if (!isUnmountedRef.current) {
                    setIsConnected(false);
                    addLog('WebSocket disconnected. Retrying...', 'warning');
                    reconnectTimeoutRef.current = setTimeout(connect, WS_RECONNECT_DELAY_MS);
                }
            };

            wsRef.current.onerror = () => {
                addLog('WebSocket connection error', 'error');
            };
        } catch (e) {
            addLog('Failed to create WebSocket connection', 'error');
        }
    }, [wsUrl, onMessage, addLog]);

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

/**
 * Hook for API operations with error handling
 */
function useApi(getApiUrl: (path: string) => string, addLog: (message: string, type: LogEntry['type']) => void) {
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
                } catch (e) {
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
            const err = e as Error;
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

/**
 * Hook for pagination logic
 */
function usePagination<T>(
    items: T[],
    itemsPerPage: number,
    searchQuery: string
) {
    const [currentPage, setCurrentPage] = useState(1);

    // Reset to first page when search changes
    useEffect(() => {
        setCurrentPage(1);
    }, [searchQuery]);

    const filteredItems = useMemo(() => {
        if (!searchQuery.trim()) return items;
        const query = searchQuery.toLowerCase();
        return items.filter(item => {
            const reading = item as Reading;
            return (
                reading.meter_id?.toLowerCase().includes(query) ||
                reading.location?.toLowerCase().includes(query)
            );
        });
    }, [items, searchQuery]);

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

// =============================================================================
// Sub-Components
// =============================================================================

interface NavLinkProps {
    to: string;
    icon: typeof Box;
    label: string;
    title: string;
    color: string;
}

const NavLink = memo(({ to, icon: Icon, label, title, color }: NavLinkProps) => (
    <Link
        to={to}
        className="glass px-5 py-3.5 rounded-2xl flex items-center gap-4 hover:bg-white/5 border-white/5 hover:border-white/10 transition-all group flex-1"
    >
        <div className={cn(
            "p-2 rounded-xl transition-all group-hover:scale-110",
            color === "emerald" && "bg-emerald-500/10 text-emerald-400 group-hover:bg-emerald-500/20",
            color === "indigo" && "bg-indigo-500/10 text-indigo-400 group-hover:bg-indigo-500/20",
            color === "rose" && "bg-rose-500/10 text-rose-400 group-hover:bg-rose-500/20",
            color === "amber" && "bg-amber-500/10 text-amber-400 group-hover:bg-amber-500/20",
        )}>
            <Icon className="w-5 h-5" />
        </div>
        <div className="flex flex-col">
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 leading-none mb-1">{label}</span>
            <span className="text-sm font-black text-white group-hover:text-indigo-200 transition-colors leading-none">{title}</span>
        </div>
    </Link>
));

NavLink.displayName = 'NavLink';

interface ControlButtonProps {
    onClick: () => void;
    disabled?: boolean;
    variant: 'emerald' | 'amber' | 'blue' | 'rose' | 'indigo';
    icon: typeof Play;
    active?: boolean;
}

const ControlButton = memo(({ onClick, disabled, variant, icon: Icon, active }: ControlButtonProps) => {
    const variantClasses = {
        emerald: !disabled ? "bg-emerald-500 text-white hover:bg-emerald-400 hover:shadow-emerald-500/20" : "bg-slate-800 text-slate-600 grayscale",
        amber: !disabled ? "bg-amber-500 text-white hover:bg-amber-400 hover:shadow-amber-500/20" : "bg-slate-800 text-slate-600 grayscale",
        blue: !disabled ? "bg-blue-500 text-white hover:bg-blue-400 hover:shadow-blue-500/20" : "bg-slate-800 text-slate-600 grayscale",
        rose: !disabled ? "bg-rose-500 text-white hover:bg-rose-400 hover:shadow-rose-500/20" : "bg-slate-800 text-slate-600 grayscale",
        indigo: "bg-indigo-500 text-white hover:bg-indigo-400 shadow-indigo-500/20",
    };

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={cn(
                "p-4 rounded-2xl flex items-center justify-center transition-all shadow-lg active:scale-95",
                variantClasses[variant],
                active && "ring-2 ring-white/50 ring-offset-2 ring-offset-slate-900 scale-105 shadow-xl"
            )}
            aria-label={`${variant} action`}
        >
            <Icon className="fill-current w-5 h-5" />
        </button>
    );
});

ControlButton.displayName = 'ControlButton';

interface NetworkTargetSelectorProps {
    apiTarget: string;
    setApiTarget: (target: string) => void;
    availableTargets: Array<{ label: string; value: string; isCustom?: boolean }>;
    removeTarget: (value: string) => void;
    isConnected: boolean;
}

const NetworkTargetSelector = memo(({
    apiTarget,
    setApiTarget,
    availableTargets,
    removeTarget,
    isConnected
}: NetworkTargetSelectorProps) => {
    const [showModal, setShowModal] = useState(false);
    const [newTargetUrl, setNewTargetUrl] = useState('');

    const handleAddTarget = useCallback(() => {
        if (newTargetUrl.trim()) {
            setApiTarget(newTargetUrl.trim());
            setNewTargetUrl('');
            setShowModal(false);
        }
    }, [newTargetUrl, setApiTarget]);

    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleAddTarget();
        }
    }, [handleAddTarget]);

    return (
        <>
            <div className="glass px-5 py-3.5 rounded-2xl flex items-center gap-4 border-indigo-500/10 hover:border-indigo-500/20 transition-all min-w-[200px] lg:min-w-[260px] relative group flex-1">
                <div className="p-2 bg-indigo-500/10 rounded-xl text-indigo-400 group-hover:bg-indigo-500/20 transition-all">
                    <Globe className="w-5 h-5" />
                </div>
                <div className="flex flex-col flex-1 min-w-0 pr-6">
                    <div className="flex items-center justify-between gap-2">
                        <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 leading-none mb-1">Network Target</span>
                        <button
                            onClick={() => setShowModal(true)}
                            className="p-1 hover:bg-white/5 rounded transition-colors -mt-1"
                            aria-label="Network settings"
                        >
                            <Settings className="w-2.5 h-2.5 text-slate-600 hover:text-indigo-400" />
                        </button>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5 relative">
                        <select
                            value={apiTarget}
                            onChange={(e) => {
                                if (e.target.value === 'CUSTOM') {
                                    setShowModal(true);
                                } else {
                                    setApiTarget(e.target.value);
                                }
                            }}
                            className="bg-transparent border-none outline-none text-sm font-black text-white/90 w-full cursor-pointer appearance-none truncate pr-4"
                            aria-label="Select network target"
                        >
                            {availableTargets.map(t => (
                                <option key={t.value} value={t.value} className="bg-slate-900">{t.label}</option>
                            ))}
                            <option value="CUSTOM" className="bg-slate-900">+ Add Custom...</option>
                        </select>
                        <ChevronDown className="w-3 h-3 text-slate-600 absolute right-0 pointer-events-none" />
                    </div>
                </div>
                <div className={cn(
                    "absolute top-3.5 right-3 w-1.5 h-1.5 rounded-full flex-shrink-0 animate-pulse-subtle",
                    isConnected ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]"
                )} />
            </div>

            {/* Target Modal */}
            {showModal && (
                <div className="fixed inset-0 z-[3000] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" role="dialog" aria-modal="true">
                    <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-sm p-6 shadow-2xl animate-in zoom-in-95 duration-200">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-bold text-white">Network Targets</h3>
                            <button onClick={() => setShowModal(false)} className="p-2 hover:bg-white/5 rounded-lg transition-colors" aria-label="Close modal">
                                <ChevronDown className="w-5 h-5 text-slate-400" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Saved Environments</label>
                                <div className="space-y-1 max-h-[120px] overflow-y-auto pr-1 custom-scrollbar">
                                    {availableTargets.map(t => (
                                        <div key={t.value} className="flex items-center justify-between p-2 bg-slate-950/50 rounded-lg group">
                                            <div className="flex flex-col">
                                                <span className="text-xs font-bold text-white">{t.label}</span>
                                                <span className="text-[10px] text-slate-500 truncate max-w-[180px]">{t.value || 'Current Origin'}</span>
                                            </div>
                                            {t.isCustom && (
                                                <button
                                                    onClick={() => removeTarget(t.value)}
                                                    className="p-1.5 hover:bg-rose-500/20 rounded-md transition-colors opacity-0 group-hover:opacity-100"
                                                    aria-label={`Remove ${t.label}`}
                                                >
                                                    <Trash2 className="w-3 h-3 text-rose-500" />
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="h-px bg-white/5 my-4" />

                            <div className="space-y-1">
                                <label htmlFor="newTargetUrl" className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Connect to URL</label>
                                <input
                                    id="newTargetUrl"
                                    type="text"
                                    value={newTargetUrl}
                                    onChange={(e) => setNewTargetUrl(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="http://localhost:8082"
                                    className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors"
                                    autoFocus
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={() => setShowModal(false)}
                                    className="flex-1 py-3 rounded-xl text-xs font-bold text-slate-400 hover:bg-white/5 transition-colors"
                                >
                                    Close
                                </button>
                                <button
                                    onClick={handleAddTarget}
                                    disabled={!newTargetUrl.trim()}
                                    className="flex-1 py-3 rounded-xl text-xs font-bold bg-indigo-500 text-white hover:bg-indigo-400 transition-all shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Add & Connect
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
});

NetworkTargetSelector.displayName = 'NetworkTargetSelector';

interface ConsoleProps {
    logs: LogEntry[];
    onClear: () => void;
}

const Console = memo(({ logs, onClear }: ConsoleProps) => {
    const consoleRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom on new logs (optional - currently shows newest first)
    useEffect(() => {
        if (consoleRef.current && logs.length > 0) {
            // Uncomment to auto-scroll: consoleRef.current.scrollTop = 0;
        }
    }, [logs]);

    return (
        <div className="glass rounded-3xl overflow-hidden shadow-2xl h-[600px] flex flex-col border border-indigo-500/20">
            <div className="bg-slate-900/80 p-4 border-b border-white/5 flex justify-between items-center">
                <span className="text-[10px] font-black uppercase tracking-widest text-indigo-400">System Logs</span>
                <button
                    onClick={onClear}
                    className="text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors"
                    aria-label="Clear logs"
                >
                    Clear
                </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-2 font-mono text-[11px]" ref={consoleRef} role="log">
                {logs.map((log, i) => (
                    <div key={`${log.timestamp}-${i}`} className="flex gap-3">
                        <span className="text-slate-600 shrink-0">[{log.timestamp}]</span>
                        <div className="space-y-1">
                            {log.type === 'reading' && log.reading ? (
                                <div className="flex items-center gap-2">
                                    <span className="text-blue-400 font-bold">{log.reading.meter_id}</span>
                                    <span className="text-slate-500">→</span>
                                    <span className="text-emerald-400">+{log.reading.energy_generated.toFixed(2)}</span>
                                    <span className="text-slate-500">/</span>
                                    <span className="text-rose-400">-{log.reading.energy_consumed.toFixed(2)}</span>
                                </div>
                            ) : (
                                <span className={cn(
                                    log.type === 'error' && "text-rose-400",
                                    log.type === 'warning' && "text-amber-400",
                                    log.type === 'success' && "text-emerald-400",
                                    log.type === 'info' && "text-blue-400"
                                )}>
                                    {log.message}
                                </span>
                            )}
                        </div>
                    </div>
                ))}
                {logs.length === 0 && (
                    <div className="text-slate-600 animate-pulse uppercase tracking-widest text-center py-10">
                        Listening for signals...
                    </div>
                )}
            </div>
        </div>
    );
});

Console.displayName = 'Console';

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    startIndex: number;
    endIndex: number;
    totalItems: number;
    onPageChange: (page: number) => void;
    onPrevPage: () => void;
    onNextPage: () => void;
}

const Pagination = memo(({
    currentPage,
    totalPages,
    startIndex,
    endIndex,
    totalItems,
    onPageChange,
    onPrevPage,
    onNextPage
}: PaginationProps) => {
    if (totalPages <= 1) return null;

    const pageNumbers = useMemo(() =>
        Array.from({ length: totalPages }, (_, i) => i + 1),
        [totalPages]
    );

    return (
        <div className="flex items-center justify-between bg-slate-900/50 p-4 rounded-2xl border border-white/5 mt-6">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                Showing <span className="text-slate-300">{startIndex}</span> - <span className="text-slate-300">{endIndex}</span> of <span className="text-slate-300">{totalItems}</span> Meters
            </div>
            <div className="flex items-center gap-2">
                <button
                    onClick={onPrevPage}
                    disabled={currentPage === 1}
                    className="p-2 bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-white/5 rounded-xl transition-all active:scale-95"
                    aria-label="Previous page"
                >
                    <ChevronLeft className="w-4 h-4 text-slate-300" />
                </button>

                <div className="flex items-center gap-1 px-2">
                    {pageNumbers.map(page => (
                        <button
                            key={page}
                            onClick={() => onPageChange(page)}
                            className={cn(
                                "w-8 h-8 rounded-lg text-[10px] font-black transition-all",
                                currentPage === page
                                    ? "bg-emerald-500 text-slate-900 shadow-lg shadow-emerald-500/20"
                                    : "hover:bg-white/10 text-slate-400"
                            )}
                            aria-label={`Go to page ${page}`}
                            aria-current={currentPage === page ? 'page' : undefined}
                        >
                            {page}
                        </button>
                    ))}
                </div>

                <button
                    onClick={onNextPage}
                    disabled={currentPage === totalPages}
                    className="p-2 bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-white/5 rounded-xl transition-all active:scale-95"
                    aria-label="Next page"
                >
                    <ChevronRight className="w-4 h-4 text-slate-300" />
                </button>
            </div>
        </div>
    );
});

Pagination.displayName = 'Pagination';

// =============================================================================
// Main Component
// =============================================================================

const Dashboard = () => {
    // ---------------------------------------------------------------------------
    // State
    // ---------------------------------------------------------------------------
    const [readings, setReadings] = useState<Reading[]>([]);
    const [status, setStatus] = useState<SimulatorStatus>({
        running: false,
        paused: false,
        num_meters: 0,
        mode: '-',
        health: {}
    });
    const [meterCount, setMeterCount] = useState(DEFAULT_METER_COUNT);
    const [search, setSearch] = useState('');
    const [profiles, setProfiles] = useState<string[]>([]);
    const [activeProfile, setActiveProfile] = useState<string>('');
    const [attackStatus, setAttackStatus] = useState<AttackStatus>({
        active: false,
        targets: [],
        mode: 'bias',
        bias_kw: 0.0
    });
    const [attackMode, setAttackMode] = useState<AttackMode>('bias');
    const [biasKW, setBiasKW] = useState(5.0);
    const [stealthy, setStealthy] = useState(false);
    const [analytics, setAnalytics] = useState<GridHealth | null>(null);
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [viewType, setViewType] = useState<'grid' | 'list'>('grid');
    const [itemsPerPage, setItemsPerPage] = useState(DEFAULT_ITEMS_PER_PAGE_GRID);

    // ---------------------------------------------------------------------------
    // Context & Refs
    // ---------------------------------------------------------------------------
    const { apiTarget, setApiTarget, availableTargets, removeTarget, getApiUrl, getWsUrl } = useNetwork();

    // ---------------------------------------------------------------------------
    // Custom Hooks
    // ---------------------------------------------------------------------------
    const { logs, addLog, clearLogs } = useLogs();

    const { apiCall } = useApi(getApiUrl, addLog);

    // ---------------------------------------------------------------------------
    // WebSocket Message Handler
    // ---------------------------------------------------------------------------
    const handleWsMessage = useCallback((data: any) => {
        // Tag-based handling (API Gateway standardized)
        if (data.tag === 'READING_RECEIVED') {
            const reading: Reading = {
                meter_id: data.data.meter_serial,
                meter_type: 'unknown', // Gateway doesn't always send type in broadcast
                location: 'Grid',
                energy_generated: data.data.kwh_amount,
                energy_consumed: 0,
                surplus_energy: 0,
                deficit_energy: 0,
                battery_level: 0,
                temperature: 25,
                weather_condition: 'Sunny',
                rec_eligible: false,
                carbon_offset: 0,
                voltage_pu: data.data.voltage,
                current_a: data.data.current,
            };
            setReadings(prev => {
                const idx = prev.findIndex(r => r.meter_id === reading.meter_id);
                if (idx >= 0) {
                    const updated = [...prev];
                    updated[idx] = { ...updated[idx], ...reading };
                    return updated;
                }
                return [...prev, reading];
            });
        } else if (data.tag === 'GRID_LOAD_UPDATE') {
            setAnalytics(data.data as GridHealth);
            addLog(`Grid Load Updated: ${data.data.total_consumption?.toFixed(2)} MW`, 'info');
        } else if (data.tag === 'METER_ALERT') {
            addLog(`METER ALERT: ${data.data.meter_id} - ${data.data.message} (${data.data.severity})`, 'warning');
        }

        // Legacy handling (Simulator backend direct)
        else if (data.type === 'meter_readings' || Array.isArray(data)) {
            const newReadings = data.readings || data;
            setReadings(newReadings);
        } else if (data.type === 'meter_reading') {
            setReadings(prev => {
                const idx = prev.findIndex(r => r.meter_id === data.reading.meter_id);
                if (idx >= 0) {
                    const updated = [...prev];
                    updated[idx] = data.reading;
                    return updated;
                }
                return [...prev, data.reading];
            });
        } else if (data.type === 'grid_status') {
            setAnalytics(data.data as GridHealth);
            addLog(`Grid estimation converged: ${data.data.num_violations || 0} violations`, 'info');
        }
    }, [addLog]);

    const wsUrl = useMemo(() => getWsUrl('/ws'), [getWsUrl]);
    const { isConnected } = useWebSocket(wsUrl, handleWsMessage, addLog);

    // ---------------------------------------------------------------------------
    // API Operations
    // ---------------------------------------------------------------------------
    const fetchStatus = useCallback(async () => {
        const data = await apiCall<SimulatorStatus>('/api/status', {}, undefined, 'Failed to fetch status');
        if (data) {
            setStatus(data);
            if (data.num_meters) setMeterCount(data.num_meters);
        }
    }, [apiCall]);

    const fetchProfiles = useCallback(async () => {
        const data = await apiCall<{ profiles: string[] }>('/api/profiles', {}, undefined, 'Failed to fetch profiles');
        if (data) {
            setProfiles(data.profiles || []);
        }
    }, [apiCall]);

    const fetchAnalytics = useCallback(async () => {
        const data = await apiCall<GridHealth>('/api/analytics/report', {}, undefined, 'Failed to fetch analytics');
        if (data) {
            setAnalytics(data);
        }
    }, [apiCall]);

    // ---------------------------------------------------------------------------
    // Control Handlers
    // ---------------------------------------------------------------------------
    const handleControl = useCallback(async (action: string) => {
        addLog(`Sending ${action} command...`, 'info');
        const data = await apiCall<{ success: boolean; message?: string }>(
            `/api/control/${action}`,
            { method: 'POST' },
            `${action} successful`,
            `Error during ${action}`
        );
        if (data?.success) {
            fetchStatus();
        }
    }, [apiCall, addLog, fetchStatus]);

    const updateMeters = useCallback(async () => {
        addLog(`Updating meter count to ${meterCount}...`, 'info');
        const data = await apiCall<{ success: boolean }>(
            '/api/control/meters',
            {
                method: 'POST',
                body: JSON.stringify({ num_meters: meterCount })
            },
            'Meter count updated',
            'Error updating meters'
        );
        if (data?.success) {
            setTimeout(fetchStatus, STATUS_REFRESH_DELAY_MS);
        }
    }, [apiCall, addLog, meterCount, fetchStatus]);

    const toggleMode = useCallback(async (mode: 'random' | 'playback', profile?: string) => {
        addLog(`Switching to ${mode} mode...`, 'info');
        const data = await apiCall<{ success: boolean; message?: string }>(
            '/api/control/mode',
            {
                method: 'POST',
                body: JSON.stringify({ mode, profile })
            },
            `Mode switched to ${mode}`,
            'Error switching mode'
        );
        if (data?.success) {
            fetchStatus();
            if (profile) setActiveProfile(profile);
        }
    }, [apiCall, addLog, fetchStatus]);

    const handleAttack = useCallback(async (active: boolean) => {
        const config: AttackConfig = {
            active,
            targets: [],
            mode: attackMode,
            bias: biasKW,
            stealthy: stealthy,
            scale: 1.2
        };

        addLog(`${active ? 'Starting' : 'Stopping'} FDI attack simulation (${attackMode})...`, active ? 'warning' : 'info');
        const data = await apiCall<{ success: boolean; status?: AttackStatus }>(
            '/api/control/attack',
            {
                method: 'POST',
                body: JSON.stringify(config)
            },
            `Attack simulation ${active ? 'active' : 'stopped'}`,
            'Error controlling attack'
        );

        if (data?.success && data.status) {
            setAttackStatus({ ...data.status, mode: attackMode, bias_kw: biasKW });
            if (active) setTimeout(fetchAnalytics, STATUS_REFRESH_DELAY_MS);
        }
    }, [apiCall, addLog, attackMode, biasKW, stealthy, fetchAnalytics]);

    // ---------------------------------------------------------------------------
    // View Type Handler
    // ---------------------------------------------------------------------------
    const handleViewTypeChange = useCallback((type: 'grid' | 'list') => {
        setViewType(type);
        setItemsPerPage(type === 'grid' ? DEFAULT_ITEMS_PER_PAGE_GRID : DEFAULT_ITEMS_PER_PAGE_LIST);
    }, []);

    // ---------------------------------------------------------------------------
    // Initial Data Fetch
    // ---------------------------------------------------------------------------
    useEffect(() => {
        fetchStatus();
        fetchProfiles();
        fetchAnalytics();
    }, [fetchStatus, fetchProfiles, fetchAnalytics]);

    // ---------------------------------------------------------------------------
    // Computed Values
    // ---------------------------------------------------------------------------
    const totalGenMW = useMemo(() => calculateEnergyMW(readings, 'energy_generated'), [readings]);
    const totalConsMW = useMemo(() => calculateEnergyMW(readings, 'energy_consumed'), [readings]);
    const totalSurpMW = useMemo(() => totalGenMW - totalConsMW, [totalGenMW, totalConsMW]);
    const gridStability = analytics?.health_score ?? 98.2;

    const {
        currentPage,
        totalPages,
        paginatedItems: paginatedMeters,
        goToPage,
        nextPage,
        prevPage,
        totalItems,
        startIndex,
        endIndex
    } = usePagination<Reading>(readings, itemsPerPage, search);

    // ---------------------------------------------------------------------------
    // Render
    // ---------------------------------------------------------------------------
    return (
        <div className="max-w-7xl mx-auto p-6 space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
                <div className="flex flex-col">
                    <h1 className="text-5xl font-black tracking-tighter bg-gradient-to-r from-emerald-400 via-teal-400 to-indigo-500 bg-clip-text text-transparent drop-shadow-sm">
                        GRIDTOKENX
                    </h1>
                    <div className="flex items-center gap-2 mt-1">
                        <div className="h-0.5 w-8 bg-emerald-500/50 rounded-full" />
                        <p className="text-[10px] uppercase font-black tracking-[0.2em] text-slate-500">Real-Time Grid Intelligence</p>
                    </div>
                </div>

                <nav className="grid grid-cols-2 md:grid-cols-3 lg:flex gap-3 w-full lg:w-auto" aria-label="Main navigation">
                    {NAV_LINKS.map((link) => (
                        <NavLink key={link.to} {...link} />
                    ))}
                    <NetworkTargetSelector
                        apiTarget={apiTarget}
                        setApiTarget={setApiTarget}
                        availableTargets={availableTargets}
                        removeTarget={removeTarget}
                        isConnected={isConnected}
                    />
                </nav>
            </header>

            {/* Control Panel */}
            <section className="glass rounded-3xl p-6 flex flex-wrap items-center justify-between gap-6 shadow-2xl border-white/5" aria-label="Simulator controls">
                <div className="flex items-center gap-3">
                    <ControlButton
                        onClick={() => handleControl('start')}
                        disabled={status.running}
                        variant="emerald"
                        icon={Play}
                    />
                    <ControlButton
                        onClick={() => handleControl('pause')}
                        disabled={!status.running || status.paused}
                        variant="amber"
                        icon={Pause}
                    />
                    <ControlButton
                        onClick={() => handleControl('resume')}
                        disabled={!status.paused}
                        variant="blue"
                        icon={Play}
                    />
                    <ControlButton
                        onClick={() => handleControl('stop')}
                        disabled={!status.running}
                        variant="rose"
                        icon={Square}
                    />
                    <ControlButton
                        onClick={() => handleControl('restart')}
                        variant="indigo"
                        icon={RotateCcw}
                    />
                </div>

                {/* Mode Selector */}
                <div className="flex items-center gap-4 bg-slate-900/50 p-2 rounded-2xl border border-white/5">
                    <button
                        onClick={() => toggleMode('random')}
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-xl transition-all cursor-pointer",
                            status.mode === 'random' ? "bg-emerald-500/10 text-emerald-400" : "hover:bg-white/5 text-slate-500"
                        )}
                        aria-pressed={status.mode === 'random'}
                    >
                        <Zap className="w-4 h-4" />
                        <span className="text-xs font-black uppercase tracking-widest leading-none">Random</span>
                    </button>
                    <div className="h-6 w-px bg-white/10" />
                    <button
                        onClick={() => toggleMode('playback', activeProfile || profiles[0])}
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-xl transition-all cursor-pointer",
                            status.mode === 'playback' ? "bg-blue-500/10 text-blue-400" : "hover:bg-white/5 text-slate-500"
                        )}
                        aria-pressed={status.mode === 'playback'}
                    >
                        <History className="w-4 h-4" />
                        <span className="text-xs font-black uppercase tracking-widest leading-none">Playback</span>
                    </button>
                </div>

                {/* Profile Selector */}
                {status.mode === 'playback' && (
                    <div className="flex items-center gap-4 bg-slate-900/50 p-2 rounded-2xl border border-white/5 animate-in slide-in-from-left-4 duration-300">
                        <div className="flex items-center gap-3 px-4 py-2">
                            <Database className="w-4 h-4 text-slate-500" />
                            <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">Profile</span>
                        </div>
                        <div className="h-8 w-px bg-white/10" />
                        <select
                            value={activeProfile}
                            onChange={(e) => toggleMode('playback', e.target.value)}
                            className="bg-transparent outline-none font-bold text-sm text-blue-400 px-2 cursor-pointer"
                            aria-label="Select profile"
                        >
                            <option value="" disabled className="bg-slate-900 text-slate-500 text-sm">Select Profile</option>
                            {profiles.map(p => (
                                <option key={p} value={p} className="bg-slate-900 text-white text-sm">{p}</option>
                            ))}
                        </select>
                        <button
                            onClick={fetchProfiles}
                            className="p-2 hover:bg-white/5 rounded-xl transition-colors"
                            title="Refresh profiles"
                            aria-label="Refresh profiles"
                        >
                            <RotateCcw className="w-3 h-3 text-slate-500" />
                        </button>
                    </div>
                )}

                {/* Meters Control */}
                <div className="flex items-center gap-4 bg-slate-900/50 p-2 rounded-2xl border border-white/5">
                    <div className="flex items-center gap-3 px-4 py-2">
                        <Settings className="w-4 h-4 text-slate-500" />
                        <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">Meters</span>
                    </div>
                    <div className="h-8 w-px bg-white/10" />
                    <div className="flex items-center gap-2 pl-2 pr-4">
                        <input
                            type="number"
                            value={meterCount}
                            onChange={(e) => setMeterCount(parseInt(e.target.value) || 0)}
                            className="bg-transparent w-12 text-center outline-none font-bold text-sm"
                            placeholder="0"
                            min="0"
                            aria-label="Number of meters"
                        />
                        <button
                            onClick={updateMeters}
                            className="p-1 px-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors text-emerald-400 font-bold text-[10px] uppercase"
                        >
                            Sync
                        </button>
                    </div>
                    <div className="h-8 w-px bg-white/10" />
                    <div className="flex items-center gap-1">
                        <Link to="/map" className="p-2 hover:bg-emerald-500/10 rounded-xl transition-colors text-slate-400 hover:text-emerald-400" title="Map View" aria-label="Map view">
                            <MapIcon className="w-5 h-5" />
                        </Link>
                        <Link to="/topology" className="p-2 hover:bg-indigo-500/10 rounded-xl transition-colors text-slate-400 hover:text-indigo-400" title="3D Topology View" aria-label="3D topology view">
                            <Box className="w-5 h-5" />
                        </Link>
                    </div>
                    <div className="h-8 w-px bg-white/10" />
                    <button
                        onClick={() => setIsAddModalOpen(true)}
                        className="p-2 hover:bg-emerald-500/20 rounded-xl transition-colors group mr-2"
                        title="Add New Meter"
                        aria-label="Add new meter"
                    >
                        <Plus className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
                    </button>
                </div>

                {/* Attack Control */}
                <div className="flex items-center gap-6 px-4">
                    <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => handleAttack(!attackStatus.active)}
                                className={cn(
                                    "flex items-center gap-2 px-4 py-2 rounded-xl border transition-all active:scale-95",
                                    attackStatus.active
                                        ? "bg-rose-500/20 border-rose-500/50 text-rose-400 animate-pulse"
                                        : "bg-slate-900/50 border-white/5 text-slate-500 hover:border-rose-500/30 hover:text-rose-400"
                                )}
                                aria-pressed={attackStatus.active}
                            >
                                {attackStatus.active ? <ShieldAlert className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
                                <span className="text-xs font-black uppercase tracking-widest leading-none">
                                    {attackStatus.active ? 'Mitigating Attack' : 'Infect Grid'}
                                </span>
                            </button>
                            <div className="flex items-center gap-1 bg-slate-900/50 px-2 py-1 rounded-lg border border-white/5">
                                <label htmlFor="attackMode" className="sr-only">Attack Mode</label>
                                <select
                                    id="attackMode"
                                    value={attackMode}
                                    onChange={(e) => setAttackMode(e.target.value as AttackMode)}
                                    className="bg-transparent text-[10px] font-bold text-slate-400 outline-none uppercase"
                                >
                                    {ATTACK_MODES.map(mode => (
                                        <option key={mode} value={mode}>{mode}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="flex items-center gap-4 px-1">
                            <div className="flex items-center gap-2">
                                <label htmlFor="biasKW" className="text-[9px] font-bold text-slate-500 uppercase">Bias</label>
                                <input
                                    id="biasKW"
                                    type="number"
                                    value={biasKW}
                                    onChange={(e) => setBiasKW(parseFloat(e.target.value) || 0)}
                                    className="bg-transparent w-8 text-[10px] font-black text-rose-400 outline-none"
                                    step="0.1"
                                />
                                <span className="text-[9px] font-bold text-slate-600">kW</span>
                            </div>
                            <label className="flex items-center gap-1 cursor-pointer group">
                                <input
                                    type="checkbox"
                                    checked={stealthy}
                                    onChange={(e) => setStealthy(e.target.checked)}
                                    className="sr-only"
                                />
                                <div className={cn(
                                    "w-3 h-3 rounded border transition-colors",
                                    stealthy ? "bg-indigo-500 border-indigo-400" : "bg-slate-800 border-white/10 group-hover:border-indigo-500/50"
                                )} />
                                <span className="text-[9px] font-bold text-slate-500 uppercase group-hover:text-indigo-400">Stealth</span>
                            </label>
                        </div>
                    </div>
                    <div className="h-10 w-px bg-white/10" />
                    <div className="flex items-center gap-2">
                        <div className={cn("w-2 h-2 rounded-full", isConnected ? "bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse" : "bg-rose-500")} />
                        <span className="text-xs font-black uppercase tracking-widest text-slate-400">{isConnected ? 'Live' : 'Offline'}</span>
                    </div>
                </div>
            </section>

            {/* Analytics Summary */}
            <section className="grid grid-cols-1 md:grid-cols-4 gap-6 animate-in slide-in-from-bottom-4 duration-500" aria-label="Analytics summary">
                {/* Grid Performance */}
                <div className="glass rounded-3xl p-6 bg-gradient-to-br from-indigo-500/10 to-transparent border-indigo-500/20 col-span-2">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <TrendingUp className="text-indigo-400" />
                            <h2 className="text-sm font-black uppercase tracking-widest text-slate-400">Grid Performance</h2>
                        </div>
                        {analytics && (
                            <div className="flex items-center gap-4">
                                <div className="text-right">
                                    <div className="text-[10px] font-black uppercase tracking-widest text-slate-500">Tech Losses</div>
                                    <div className="text-lg font-black text-rose-400">{(analytics.total_loss_mw * 1000).toFixed(1)} <span className="text-xs">kW</span></div>
                                </div>
                                <div className="w-px h-8 bg-white/10" />
                                <div className="text-right">
                                    <div className="text-[10px] font-black uppercase tracking-widest text-slate-500">Efficiency</div>
                                    <div className="text-lg font-black text-emerald-400">{(100 - analytics.loss_percentage).toFixed(2)} %</div>
                                </div>
                            </div>
                        )}
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-slate-900/40 p-4 rounded-2xl border border-white/5 space-y-1">
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Avg Voltage</span>
                            <div className="text-xl font-black text-blue-400">{analytics?.avg_voltage_pu?.toFixed(3) ?? '0.000'} <span className="text-xs text-slate-500">p.u.</span></div>
                        </div>
                        <div className="bg-slate-900/40 p-4 rounded-2xl border border-white/5 space-y-1">
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Voltage Spread</span>
                            <div className="text-xl font-black text-indigo-400">
                                {analytics?.min_voltage_pu?.toFixed(3) ?? '0.000'} <span className="text-xs text-slate-500">to</span> {analytics?.max_voltage_pu?.toFixed(3) ?? '0.000'}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Cyber Security */}
                <div className={cn(
                    "glass rounded-3xl p-6 border transition-all col-span-1",
                    analytics?.is_under_attack ? "bg-rose-500/10 border-rose-500/50 ring-1 ring-rose-500/20" : "bg-emerald-500/5 border-emerald-500/20"
                )}>
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <ShieldAlert className={analytics?.is_under_attack ? "text-rose-400" : "text-emerald-400"} />
                            <h2 className="text-sm font-black uppercase tracking-widest text-slate-400">Cyber Security</h2>
                        </div>
                        <div className={cn(
                            "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest",
                            analytics?.is_under_attack ? "bg-rose-500/20 text-rose-400" : "bg-emerald-500/20 text-emerald-400"
                        )}>
                            {analytics?.is_under_attack ? 'Under Attack' : 'Secure'}
                        </div>
                    </div>
                    <div className="text-center py-2">
                        <div className={cn("text-5xl font-black mb-1", analytics?.is_under_attack ? "text-rose-400" : "text-white")}>
                            {analytics?.anomaly_score?.toFixed(0) ?? 0}
                        </div>
                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Anomaly Score</div>
                    </div>
                    {analytics?.attack_alerts && analytics.attack_alerts.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-white/5 space-y-1 max-h-24 overflow-y-auto">
                            {analytics.attack_alerts.map((alert: AttackAlert, i: number) => (
                                <div key={`${alert.meter_id}-${i}`} className="flex items-center justify-between text-[8px] font-black uppercase tracking-tighter text-rose-300">
                                    <span>{alert.meter_id}</span>
                                    <span>{alert.type}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Grid Health */}
                <div className={cn(
                    "glass rounded-3xl p-6 border transition-all col-span-1",
                    (analytics?.num_violations && analytics.num_violations > 0) ? "bg-amber-500/10 border-amber-500/50" : "bg-emerald-500/5 border-emerald-500/20"
                )}>
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <AlertTriangle className={analytics?.num_violations && analytics.num_violations > 0 ? "text-amber-400" : "text-emerald-400"} />
                            <h2 className="text-sm font-black uppercase tracking-widest text-slate-400">Grid Health</h2>
                        </div>
                    </div>
                    <div className="text-center py-4">
                        <div className="text-5xl font-black mb-2">{analytics?.num_violations ?? 0}</div>
                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Violations</div>
                    </div>
                </div>
            </section>

            {/* Stats Cards */}
            <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" aria-label="Grid statistics">
                <StatCard title="Grid Generation" value={totalGenMW.toFixed(3)} unit="MW" icon={<Sun className="text-emerald-400" />} color="emerald" />
                <StatCard title="Grid Consumption" value={totalConsMW.toFixed(3)} unit="MW" icon={<Zap className="text-blue-400" />} color="blue" />
                <StatCard title="Net Flow" value={totalSurpMW.toFixed(3)} unit="MW" icon={<Activity className="text-purple-400" />} color="purple" />
                <StatCard title="Stability Score" value={gridStability.toFixed(1)} unit="%" icon={<Shield className="text-rose-400" />} color="rose" />
            </section>

            {/* Main Grid */}
            <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-black uppercase tracking-widest text-slate-400 flex items-center gap-3">
                            <Activity className="w-5 h-5 text-emerald-400" />
                            Live Meters
                        </h2>
                        <div className="flex items-center gap-4">
                            <div className="flex bg-slate-900/50 p-1 rounded-xl border border-white/5" role="group" aria-label="View type">
                                <button
                                    onClick={() => handleViewTypeChange('grid')}
                                    className={cn(
                                        "p-2 rounded-lg transition-all",
                                        viewType === 'grid' ? "bg-emerald-500 text-slate-900 shadow-lg shadow-emerald-500/20" : "text-slate-500 hover:text-white"
                                    )}
                                    aria-pressed={viewType === 'grid'}
                                    aria-label="Grid view"
                                >
                                    <LayoutGrid className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => handleViewTypeChange('list')}
                                    className={cn(
                                        "p-2 rounded-lg transition-all",
                                        viewType === 'list' ? "bg-emerald-500 text-slate-900 shadow-lg shadow-emerald-500/20" : "text-slate-500 hover:text-white"
                                    )}
                                    aria-pressed={viewType === 'list'}
                                    aria-label="List view"
                                >
                                    <ListIcon className="w-4 h-4" />
                                </button>
                            </div>
                            <div className="relative group">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-emerald-400 transition-colors" />
                                <label htmlFor="meterSearch" className="sr-only">Search meters</label>
                                <input
                                    id="meterSearch"
                                    type="search"
                                    placeholder="Search meters..."
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    className="bg-slate-900/50 border border-white/5 rounded-xl py-2 pl-10 pr-4 outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/50 transition-all text-sm w-48 xl:w-64"
                                />
                            </div>
                        </div>
                    </div>

                    <div className={cn(
                        viewType === 'grid' ? "grid grid-cols-1 md:grid-cols-2 gap-4" : "flex flex-col gap-2",
                        "min-h-[400px]"
                    )}>
                        {paginatedMeters.length > 0 ? (
                            paginatedMeters.map(meter => (
                                viewType === 'grid'
                                    ? <MeterCard key={meter.meter_id} reading={meter} />
                                    : <MeterListItem key={meter.meter_id} reading={meter} />
                            ))
                        ) : (
                            <div className="col-span-full py-20 text-center glass rounded-3xl border-dashed">
                                <p className="text-slate-500 font-bold uppercase tracking-widest animate-pulse">Waiting for telemetry...</p>
                            </div>
                        )}
                    </div>

                    <Pagination
                        currentPage={currentPage}
                        totalPages={totalPages}
                        startIndex={startIndex}
                        endIndex={endIndex}
                        totalItems={totalItems}
                        onPageChange={goToPage}
                        onPrevPage={prevPage}
                        onNextPage={nextPage}
                    />
                </div>

                {/* Console */}
                <aside className="space-y-6">
                    <SolarDetection />
                    <h2 className="text-xl font-black uppercase tracking-widest text-slate-400 flex items-center gap-3">
                        <Terminal className="w-5 h-5 text-indigo-400" />
                        Console
                    </h2>
                    <Console logs={logs} onClear={clearLogs} />
                </aside>
            </main>

            <AddMeterModal
                isOpen={isAddModalOpen}
                onClose={() => setIsAddModalOpen(false)}
                onSuccess={(data) => {
                    console.log("Meter added:", data);
                    fetchStatus();
                }}
            />
        </div>
    );
};

export default Dashboard;
