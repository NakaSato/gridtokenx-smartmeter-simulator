import { useState, useEffect, useCallback, useMemo } from 'react';
import {
    Activity,
    Zap,
    Sun,
    Terminal,
    Search,
    ChevronDown,
    LayoutGrid,
    List as ListIcon,
    Coins
} from 'lucide-react';

import { MeterCard } from '../features/meter/components/MeterCard';
import { SimulationControl } from '../features/simulator/components/SimulationControl';
import { MeterListItem } from '../features/meter/components/MeterListItem';
import { StatCard } from '../components/ui/StatCard';
import { SolarDetection } from '../features/monitoring/components/SolarDetection';
import AddMeterModal from '../features/meter/components/AddMeterModal';
import { PriceComparisonDisplay } from '../features/meter/components/PriceCard';

import { usePrices } from '../features/meter/hooks/usePrices';
import { useNetwork } from '../context/NetworkContext';
import { useLogs } from '../features/console/hooks/useLogs';
import { useWebSocket } from '../hooks/useWebSocket';
import { useApi } from '../hooks/useApi';
import { usePagination } from '../hooks/usePagination';

import { DashboardHeader } from '../features/dashboard/components/DashboardHeader';
import { GridControls } from '../features/dashboard/components/GridControls';
import { Console } from '../features/dashboard/components/Console';
import { Pagination } from '../features/dashboard/components/Pagination';

import { 
    STATUS_REFRESH_DELAY_MS, 
    DEFAULT_METER_COUNT, 
    DEFAULT_ITEMS_PER_PAGE_GRID, 
    DEFAULT_ITEMS_PER_PAGE_LIST 
} from '../constants/index';
import { calculateEnergyMW, cn } from '../utils/common';

import type { Reading, GridHealth, AttackAlert, PriceCompareResponse, SimulatorStatus, AttackStatus, AttackMode, AttackConfig, WsMessage } from '../types/index';

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
        health: {},
        weather_mode: 'Sunny',
        grid_stress: 1.0
    });
    const [meterCount, setMeterCount] = useState(DEFAULT_METER_COUNT);
    const [search, setSearch] = useState('');
    const [meterTypeFilter, setMeterTypeFilter] = useState<string>('all');
    const [statusFilter, setStatusFilter] = useState<string>('all');
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
    // Context & Hooks
    // ---------------------------------------------------------------------------
    const { apiTarget, setApiTarget, availableTargets, removeTarget, getApiUrl, getWsUrl } = useNetwork();
    const { logs, addLog, clearLogs } = useLogs();
    const { apiCall, isLoading } = useApi(getApiUrl, addLog);
    const { comparePrices, isLoading: priceLoading, error: priceError } = usePrices(getApiUrl);

    // Price Comparison State
    const [priceComparison, setPriceComparison] = useState<PriceCompareResponse | null>(null);
    const [energyKwh, setEnergyKwh] = useState<number>(100);

    // ---------------------------------------------------------------------------
    // WebSocket Message Handler
    // ---------------------------------------------------------------------------
    const handleWsMessage = useCallback((data: unknown) => {
        const msg = data as WsMessage;
        
        interface ReadingPayload {
            meter_serial: string;
            kwh_amount: number;
            voltage: number;
            current: number;
        }

        interface AlertPayload {
            meter_id: string;
            message: string;
            severity: string;
        }

        if (msg.tag === 'READING_RECEIVED' && msg.data) {
            const payload = msg.data as ReadingPayload;
            const reading: Reading = {
                meter_id: payload.meter_serial,
                meter_type: 'unknown',
                location: 'Grid',
                energy_generated: payload.kwh_amount,
                energy_consumed: 0,
                surplus_energy: 0,
                deficit_energy: 0,
                battery_level: 0,
                temperature: 25,
                weather_condition: 'Sunny',
                rec_eligible: false,
                carbon_offset: 0,
                voltage_pu: payload.voltage,
                current_a: payload.current,
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
        } else if (msg.tag === 'GRID_LOAD_UPDATE' && msg.data) {
            const payload = msg.data as GridHealth;
            setAnalytics(payload);
            addLog(`Grid Load Updated: ${payload.total_consumption?.toFixed(2)} MW`, 'info');
        } else if (msg.tag === 'METER_ALERT' && msg.data) {
            const payload = msg.data as AlertPayload;
            addLog(`METER ALERT: ${payload.meter_id} - ${payload.message} (${payload.severity})`, 'warning');
        }
        else if ((msg.type === 'meter_readings' || Array.isArray(msg)) && msg.readings) {
            const newReadings = msg.readings;
            setReadings(newReadings);
        } else if (msg.type === 'meter_reading' && msg.reading) {
            const r = msg.reading;
            setReadings(prev => {
                const idx = prev.findIndex(item => item.meter_id === r.meter_id);
                if (idx >= 0) {
                    const updated = [...prev];
                    updated[idx] = r;
                    return updated;
                }
                return [...prev, r];
            });
        } else if (msg.type === 'grid_status' && msg.data) {
            const payload = msg.data as GridHealth;
            setAnalytics(payload);
            addLog(`Grid estimation converged: ${payload.num_violations || 0} violations`, 'info');
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

    const updateWeather = useCallback(async (mode: string) => {
        const res = await apiCall<{ success: boolean; weather_mode: string }>(
            '/control/weather', 
            { method: 'POST', body: JSON.stringify({ mode }) },
            `Weather updated to ${mode}`
        );
        if (res?.success) {
            setStatus(prev => ({ ...prev, weather_mode: res.weather_mode }));
        }
    }, [apiCall]);

    const updateStress = useCallback(async (multiplier: number) => {
        const res = await apiCall<{ success: boolean; grid_stress: number }>(
            '/control/stress', 
            { method: 'POST', body: JSON.stringify({ multiplier }) },
            `Grid stress updated to ${multiplier}x`
        );
        if (res?.success) {
            setStatus(prev => ({ ...prev, grid_stress: res.grid_stress }));
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

    const handlePriceCompare = useCallback(async () => {
        addLog(`Comparing prices for ${energyKwh} kWh...`, 'info');
        const result = await comparePrices({
            energy_kwh: energyKwh,
            utility_provider: 'PEA',
            tariff_category: '1.1.2',
            billing_month: 3,
            billing_year: 2026,
            wheeling_cost: 1.76,
        });
        if (result) {
            setPriceComparison(result);
            const savingsAmount = result.analysis.buyer_savings_baht;
            addLog(`Price comparison complete: P2P ${savingsAmount < 0 ? 'costs' : 'saves'} ${Math.abs(savingsAmount).toFixed(2)} Baht`, 'success');
        }
    }, [comparePrices, energyKwh, addLog]);

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

    const handleViewTypeChange = useCallback((type: 'grid' | 'list') => {
        setViewType(type);
        setItemsPerPage(type === 'grid' ? DEFAULT_ITEMS_PER_PAGE_GRID : DEFAULT_ITEMS_PER_PAGE_LIST);
    }, []);

    useEffect(() => {
        const init = async () => {
            await fetchStatus();
            await fetchProfiles();
            await fetchAnalytics();
        };
        init();
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
    } = usePagination<Reading>(readings, itemsPerPage, search, meterTypeFilter, statusFilter);

    // ---------------------------------------------------------------------------
    // Render
    // ---------------------------------------------------------------------------
    return (
        <div className="max-w-7xl mx-auto p-6 space-y-8 animate-in fade-in duration-500">
            <DashboardHeader 
                apiTarget={apiTarget}
                setApiTarget={setApiTarget}
                availableTargets={availableTargets}
                removeTarget={removeTarget}
                isConnected={isConnected}
            />

            <GridControls 
                status={status}
                handleControl={handleControl}
                toggleMode={toggleMode}
                profiles={profiles}
                activeProfile={activeProfile}
                fetchProfiles={fetchProfiles}
                meterCount={meterCount}
                setMeterCount={setMeterCount}
                updateMeters={updateMeters}
                setIsAddModalOpen={setIsAddModalOpen}
                handleAttack={handleAttack}
                attackStatus={attackStatus}
                attackMode={attackMode}
                setAttackMode={setAttackMode}
                biasKW={biasKW}
                setBiasKW={setBiasKW}
                stealthy={stealthy}
                setStealthy={setStealthy}
                isConnected={isConnected}
            />

            {/* Analytics Summary */}
            <section className="grid grid-cols-1 md:grid-cols-4 gap-6 animate-in slide-in-from-bottom-4 duration-500" aria-label="Analytics summary">
                {/* Grid Performance */}
                <div className="glass rounded-3xl p-6 bg-gradient-to-br from-indigo-500/10 to-transparent border-indigo-500/20 col-span-2">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <Activity className="text-indigo-400" />
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
                            <Activity className={analytics?.is_under_attack ? "text-rose-400" : "text-emerald-400"} />
                            <h2 className="text-sm font-black uppercase tracking-widest text-slate-400">Cyber Security</h2>
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
                            <Activity className={analytics?.num_violations && analytics.num_violations > 0 ? "text-amber-400" : "text-emerald-400"} />
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
                <StatCard title="Stability Score" value={gridStability.toFixed(1)} unit="%" icon={<Activity className="text-rose-400" />} color="rose" />
            </section>

            {/* Price Comparison Section */}
            <section className="space-y-6" aria-label="Price comparison">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-black uppercase tracking-widest text-slate-400 flex items-center gap-3">
                        <Activity className="w-5 h-5 text-emerald-400" />
                        P2P Price Comparison
                    </h2>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 bg-slate-900/50 px-4 py-2 rounded-xl border border-white/5">
                            <label htmlFor="energyKwh" className="text-sm font-bold text-slate-400">Energy:</label>
                            <input
                                id="energyKwh"
                                type="number"
                                value={energyKwh}
                                onChange={(e) => setEnergyKwh(Number(e.target.value) || 0)}
                                className="bg-transparent w-20 text-right outline-none font-bold text-emerald-400"
                                min="1"
                            />
                            <span className="text-sm font-bold text-slate-500">kWh</span>
                        </div>
                        <button
                            onClick={handlePriceCompare}
                            disabled={priceLoading}
                            className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-500 text-slate-900 font-bold rounded-xl transition-all active:scale-95 disabled:scale-100 disabled:cursor-not-allowed"
                        >
                            {priceLoading ? 'Comparing...' : 'Compare Prices'}
                        </button>
                    </div>
                </div>

                {priceError && (
                    <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-rose-400 text-sm font-bold">
                        {priceError}
                    </div>
                )}

                {priceComparison ? (
                    <PriceComparisonDisplay data={priceComparison} energyKwh={energyKwh} />
                ) : (
                    <div className="p-12 text-center rounded-2xl border border-dashed border-slate-500/20 bg-slate-500/5">
                        <Coins className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                        <div className="text-slate-400 font-bold mb-2">Compare Utility vs P2P Pricing</div>
                        <div className="text-slate-500 text-sm">Click "Compare Prices" to see potential savings with P2P energy trading</div>
                    </div>
                )}
            </section>

            {/* Main Grid */}
            <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-black uppercase tracking-widest text-slate-400 flex items-center gap-3">
                            <Activity className="w-5 h-5 text-emerald-400" />
                            Live Meters
                        </h2>
                        <div className="flex items-center gap-3">
                            {/* Type Filter */}
                            <div className="relative">
                                <label htmlFor="typeFilter" className="sr-only">Filter by type</label>
                                <select
                                    id="typeFilter"
                                    value={meterTypeFilter}
                                    onChange={(e) => setMeterTypeFilter(e.target.value)}
                                    className="appearance-none bg-slate-900/50 border border-white/5 rounded-xl py-2 pl-4 pr-10 outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/50 transition-all text-sm font-medium text-slate-300 cursor-pointer hover:border-white/10"
                                >
                                    <option value="all">All Types</option>
                                    <option value="solar_prosumer">Solar Prosumer</option>
                                    <option value="grid_consumer">Grid Consumer</option>
                                    <option value="hybrid_prosumer">Hybrid Prosumer</option>
                                    <option value="battery_storage">Battery Storage</option>
                                    <option value="ev_charger">EV Charger</option>
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
                            </div>

                            {/* Status Filter */}
                            <div className="relative">
                                <label htmlFor="statusFilter" className="sr-only">Filter by status</label>
                                <select
                                    id="statusFilter"
                                    value={statusFilter}
                                    onChange={(e) => setStatusFilter(e.target.value)}
                                    className="appearance-none bg-slate-900/50 border border-white/5 rounded-xl py-2 pl-4 pr-10 outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/50 transition-all text-sm font-medium text-slate-300 cursor-pointer hover:border-white/10"
                                >
                                    <option value="all">All Status</option>
                                    <option value="producing">Producing</option>
                                    <option value="consuming">Consuming</option>
                                    <option value="battery">Has Battery</option>
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
                            </div>

                            {/* View Toggle */}
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
                onSuccess={() => {
                    fetchStatus();
                }}
            />
            <SimulationControl 
                weatherMode={status.weather_mode}
                gridStress={status.grid_stress}
                onUpdateWeather={updateWeather}
                onUpdateStress={updateStress}
                isLoading={isLoading}
            />
        </div>
    );
};

export default Dashboard;
