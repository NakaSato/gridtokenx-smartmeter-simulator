"use client";

import { useState, useMemo } from 'react';
import { Activity, Zap, Sun, Search, ChevronDown, LayoutGrid, List as ListIcon } from 'lucide-react';

import { MeterCard } from '@/components/meters/components/MeterCard';
import { SimulationControl } from '@/components/simulator/components/SimulationControl';
import { MeterListItem } from '@/components/meters/components/MeterListItem';
import { StatCard } from '@/components/ui/StatCard';
import AddMeterModal from '@/components/meters/components/AddMeterModal';

import { usePrices } from '@/components/meters/hooks/usePrices';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { useSimulator } from '@/components/providers/SimulatorProvider';
import { usePagination } from '@/hooks/usePagination';

import { DashboardHeader } from '@/components/dashboard/components/DashboardHeader';
import { GridControls } from '@/components/dashboard/components/GridControls';
import { Console } from '@/components/dashboard/components/Console';
import { Pagination } from '@/components/dashboard/components/Pagination';

import { DEFAULT_METER_COUNT, DEFAULT_ITEMS_PER_PAGE_GRID } from '@/lib/constants';
import { calculateEnergyMW, cn } from '@/lib/common';
import type { Reading, AttackMode } from '@/lib/types';

const Dashboard = () => {
    const {
        status, readings, analytics, attackStatus, isConnected, logs, isLoading,
        handleControl, updateEnvironment, handleAttack, addLog, clearLogs
    } = useSimulator();

    const { getApiUrl } = useNetwork();
    const { comparePrices, isLoading: priceLoading, error: priceError } = usePrices(getApiUrl);

    const [meterCount, setMeterCount] = useState(DEFAULT_METER_COUNT);
    const [search, setSearch] = useState('');
    const [meterTypeFilter, setMeterTypeFilter] = useState('all');
    const [statusFilter, setStatusFilter] = useState('all');
    const [attackMode, setAttackMode] = useState<AttackMode>('bias');
    const [biasKW, setBiasKW] = useState(5.0);
    const [stealthy, setStealthy] = useState(false);
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [viewType, setViewType] = useState<'grid' | 'list'>('grid');
    const [itemsPerPage, setItemsPerPage] = useState(DEFAULT_ITEMS_PER_PAGE_GRID);
    const [energyKwh, setEnergyKwh] = useState(100);
    const [priceComparison, setPriceComparison] = useState<any>(null);

    const totalGenMW = useMemo(() => calculateEnergyMW(readings, 'energy_generated'), [readings]);
    const totalConsMW = useMemo(() => calculateEnergyMW(readings, 'energy_consumed'), [readings]);
    const totalSurpMW = useMemo(() => totalGenMW - totalConsMW, [totalGenMW, totalConsMW]);

    const {
        currentPage, totalPages, paginatedItems: paginatedMeters, goToPage, nextPage, prevPage,
        totalItems, startIndex, endIndex
    } = usePagination<Reading>(readings, itemsPerPage, search, meterTypeFilter, statusFilter);

    return (
        <div className="max-w-7xl mx-auto p-6 space-y-8 animate-in fade-in duration-500">
            <DashboardHeader />
            <GridControls
                status={status} handleControl={handleControl} toggleMode={() => { }}
                profiles={[]} activeProfile="" fetchProfiles={() => { }}
                meterCount={meterCount} setMeterCount={setMeterCount} updateMeters={() => { }}
                setIsAddModalOpen={setIsAddModalOpen} handleAttack={(active) => handleAttack(active, attackMode, biasKW)}
                attackStatus={attackStatus} attackMode={attackMode} setAttackMode={setAttackMode}
                biasKW={biasKW} setBiasKW={setBiasKW} stealthy={stealthy} setStealthy={setStealthy} isConnected={isConnected}
            />

            <section className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard title="Grid Generation" value={totalGenMW.toFixed(3)} unit="MW" icon={<Sun className="text-emerald-400" />} color="emerald" />
                <StatCard title="Grid Consumption" value={totalConsMW.toFixed(3)} unit="MW" icon={<Zap className="text-blue-400" />} color="blue" />
                <StatCard title="Net Flow" value={totalSurpMW.toFixed(3)} unit="MW" icon={<Activity className="text-purple-400" />} color="purple" />
                <StatCard title="Stability Score" value={(analytics?.health_score ?? 98.2).toFixed(1)} unit="%" icon={<Activity className="text-rose-400" />} color="rose" />
            </section>

            <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                    <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                        <h2 className="text-xl font-black uppercase tracking-widest text-slate-400 flex items-center gap-3">
                            <Activity className="w-5 h-5 text-emerald-400" /> Live Meters
                        </h2>
                        <div className="flex flex-wrap items-center gap-3">
                            <div className="relative">
                                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                                <input
                                    type="text"
                                    placeholder="Search meters..."
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    className="pl-9 pr-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-emerald-500/50 w-full md:w-48 transition-all"
                                />
                            </div>

                            <div className="relative">
                                <select
                                    value={meterTypeFilter}
                                    onChange={(e) => setMeterTypeFilter(e.target.value)}
                                    className="appearance-none pl-4 pr-10 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-emerald-500/50 transition-all"
                                >
                                    <option value="all">All Types</option>
                                    <option value="Residential">Residential</option>
                                    <option value="Solar_Prosumer">Solar Prosumer</option>
                                    <option value="Commercial">Commercial</option>
                                </select>
                                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                            </div>

                            <div className="flex bg-slate-800/50 border border-slate-700/50 rounded-lg p-1">
                                <button
                                    onClick={() => setViewType('grid')}
                                    className={cn("p-1.5 rounded-md transition-all", viewType === 'grid' ? "bg-slate-700 text-emerald-400 shadow-sm" : "text-slate-400 hover:text-slate-200")}
                                >
                                    <LayoutGrid className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => setViewType('list')}
                                    className={cn("p-1.5 rounded-md transition-all", viewType === 'list' ? "bg-slate-700 text-emerald-400 shadow-sm" : "text-slate-400 hover:text-slate-200")}
                                >
                                    <ListIcon className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </div>
                    <div className={cn(viewType === 'grid' ? "grid grid-cols-1 md:grid-cols-2 gap-4" : "flex flex-col gap-2", "min-h-[400px]")}>
                        {paginatedMeters.map(meter => (
                            viewType === 'grid' ? <MeterCard key={meter.meter_id} reading={meter} /> : <MeterListItem key={meter.meter_id} reading={meter} />
                        ))}
                        {paginatedMeters.length === 0 && (
                            <div className="col-span-full flex flex-col items-center justify-center p-12 text-slate-500 border border-dashed border-slate-700/50 rounded-2xl bg-slate-800/20">
                                <Activity className="w-12 h-12 mb-4 opacity-20" />
                                <h3 className="text-lg font-bold text-slate-400 mb-1">No Meters Found</h3>
                                <p className="text-sm opacity-60">
                                    {readings.length === 0
                                        ? "Start the backend simulator to begin receiving telemetry."
                                        : "No meters match your search criteria."}
                                </p>
                            </div>
                        )}
                    </div>
                    <Pagination currentPage={currentPage} totalPages={totalPages} startIndex={startIndex} endIndex={endIndex} totalItems={totalItems} onPageChange={goToPage} onPrevPage={prevPage} onNextPage={nextPage} />
                </div>
                <aside className="space-y-6">
                    <Console logs={logs} onClear={clearLogs} />
                </aside>
            </main>

            <SimulationControl
                weatherMode={status.weather_mode} gridStress={status.grid_stress}
                onUpdateWeather={(mode) => updateEnvironment({ weather: mode })}
                onUpdateStress={(multiplier) => updateEnvironment({ grid_stress: multiplier })}
                isLoading={isLoading}
            />
            <AddMeterModal isOpen={isAddModalOpen} onClose={() => setIsAddModalOpen(false)} onSuccess={() => { }} />
        </div>
    );
};

export default Dashboard;
