"use client";

import { useState, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Activity, Search, ChevronDown, LayoutGrid, List as ListIcon, ArrowUpDown } from 'lucide-react';

import { MeterCard } from '@/components/meters/components/MeterCard';
import { MeterListItem } from '@/components/meters/components/MeterListItem';
import AddMeterModal from '@/components/meters/components/AddMeterModal';
import EditMeterModal from '@/components/meters/components/EditMeterModal';
import MetadataProfileModal from '@/components/meters/components/MetadataProfileModal';

import { useSimulator } from '@/components/providers/SimulatorProvider';
import { usePagination } from '@/hooks/usePagination';
import { useSimulatorApi } from '@/hooks/useSimulatorApi';

import { GridControls } from '@/components/dashboard/components/GridControls';
import { FleetCarbon } from '@/components/dashboard/components/FleetCarbon';
import { SecurityPanel } from '@/components/dashboard/components/SecurityPanel';
import { Pagination } from '@/components/dashboard/components/Pagination';

import { DEFAULT_METER_COUNT, DEFAULT_ITEMS_PER_PAGE_GRID } from '@/lib/constants';
import { calculateEnergyMW, cn } from '@/lib/common';
import type { Reading, AttackMode } from '@/lib/types';

const Dashboard = () => {
    const {
        status, readings, analytics, attackStatus, isConnected, isLoading,
        handleControl, updateEnvironment, updateMeterCount, deleteMeter, handleAttack, fetchInitialMeters
    } = useSimulator();

    const api = useSimulatorApi();
    const router = useRouter();

    const openMeterPage = useCallback(
        (meterId: string) => router.push(`/meter/${encodeURIComponent(meterId)}`),
        [router],
    );

    const [meterCount, setMeterCount] = useState(DEFAULT_METER_COUNT);
    const [genMin, setGenMin] = useState(5);
    const [genMax, setGenMax] = useState(30);
    const [search, setSearch] = useState('');
    const [meterTypeFilter, setMeterTypeFilter] = useState('all');
    const [statusFilter, setStatusFilter] = useState('all');
    const [sortKey, setSortKey] = useState('default');
    const [attackMode, setAttackMode] = useState<AttackMode>('bias');
    const [biasKW, setBiasKW] = useState(5.0);
    const [stealthy, setStealthy] = useState(false);
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    
    // Edit & Meta Modal State
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isMetaModalOpen, setIsMetaModalOpen] = useState(false);
    const [selectedMeter, setSelectedMeter] = useState<Reading | null>(null);

    const [viewType, setViewType] = useState<'grid' | 'list'>('grid');
    const itemsPerPage = DEFAULT_ITEMS_PER_PAGE_GRID;

    const handleEditMeter = useCallback(async (meter: Reading) => {
        try {
            const fullMeter = await api.getMeter(meter.meter_id);
            setSelectedMeter({ ...meter, ...(fullMeter ?? {}) });
        } catch {
            setSelectedMeter(meter);
        }
        setIsEditModalOpen(true);
    }, [api]);

    const handleEditMetadata = useCallback(async (meter: Reading) => {
        try {
            const fullMeter = await api.getMeter(meter.meter_id);
            setSelectedMeter({ ...meter, ...(fullMeter ?? {}) });
        } catch {
            setSelectedMeter(meter);
        }
        setIsMetaModalOpen(true);
    }, [api]);

    const totalGenMW = useMemo(() => calculateEnergyMW(readings, 'energy_generated', true), [readings]);
    const totalConsMW = useMemo(() => calculateEnergyMW(readings, 'energy_consumed', true), [readings]);
    const totalSurpMW = useMemo(() => totalGenMW - totalConsMW, [totalGenMW, totalConsMW]);

    const {
        currentPage, totalPages, paginatedItems: paginatedMeters, goToPage, nextPage, prevPage,
        totalItems, startIndex, endIndex
    } = usePagination<Reading>(readings, itemsPerPage, search, meterTypeFilter, statusFilter, sortKey);

    return (
        <div className="max-w-7xl mx-auto p-8 pt-16 space-y-10">
            <GridControls
                status={status} handleControl={handleControl}
                meterCount={meterCount} setMeterCount={setMeterCount} 
                updateMeters={() => updateMeterCount(meterCount, {gen_min: genMin, gen_max: genMax})}
                genMin={genMin} setGenMin={setGenMin} genMax={genMax} setGenMax={setGenMax}
                handleAttack={(active) => handleAttack(active, attackMode, biasKW)}
                attackStatus={attackStatus} attackMode={attackMode} setAttackMode={setAttackMode}
                biasKW={biasKW} setBiasKW={setBiasKW} stealthy={stealthy} setStealthy={setStealthy} isConnected={isConnected}
                onUpdateWeather={(mode) => updateEnvironment({ weather: mode })}
                onUpdateStress={(multiplier) => updateEnvironment({ grid_stress: multiplier })}
                isLoading={isLoading}
                totalGenMW={totalGenMW}
                totalConsMW={totalConsMW}
                totalSurpMW={totalSurpMW}
                stabilityScore={analytics?.health_score ?? null}
            />

            <FleetCarbon />

            <SecurityPanel />

            <main>
                <div className="space-y-8">
                    <div className="flex flex-col gap-6 bg-[var(--panel)] p-6 border border-[var(--line)]">
                        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                            <h2 className="hmi-title text-[13px] flex items-center gap-3">
                                <Activity className="w-5 h-5 text-[var(--lbl)]" /> METERS
                            </h2>
                            <div className="flex flex-wrap items-center gap-3">
                                <div className="relative">
                                    <Search className="w-4 h-4 text-[var(--lbl)] absolute left-3 top-1/2 -translate-y-1/2" />
                                    <input
                                        type="text"
                                        placeholder="Search meters..."
                                        value={search}
                                        onChange={(e) => setSearch(e.target.value)}
                                        className="hmi-input pl-9 pr-4 w-full md:w-48"
                                    />
                                </div>

                                <div className="relative">
                                    <select
                                        value={meterTypeFilter}
                                        onChange={(e) => setMeterTypeFilter(e.target.value)}
                                        className="hmi-input appearance-none pr-10"
                                    >
                                        <option value="all">All Types</option>
                                        <option value="Residential">Residential</option>
                                        <option value="Solar_Prosumer">Solar Prosumer</option>
                                        <option value="Commercial">Commercial</option>
                                    </select>
                                    <ChevronDown className="w-4 h-4 text-[var(--lbl)] absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                                </div>

                                <div className="relative">
                                    <select
                                        value={statusFilter}
                                        onChange={(e) => setStatusFilter(e.target.value)}
                                        className="hmi-input appearance-none pr-10"
                                    >
                                        <option value="all">All Status</option>
                                        <option value="producing">Producing</option>
                                        <option value="consuming">Consuming</option>
                                        <option value="battery">Has Battery</option>
                                        <option value="compromised">Compromised</option>
                                        <option value="shed">Shedded</option>
                                    </select>
                                    <ChevronDown className="w-4 h-4 text-[var(--lbl)] absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                                </div>

                                <div className="relative">
                                    <ArrowUpDown className="w-4 h-4 text-[var(--lbl)] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none z-10" />
                                    <select
                                        value={sortKey}
                                        onChange={(e) => setSortKey(e.target.value)}
                                        className="hmi-input appearance-none pl-9 pr-10"
                                    >
                                        <option value="default">Default Order</option>
                                        <option value="name">Name (A–Z)</option>
                                        <option value="balance_desc">Net Flow (High→Low)</option>
                                        <option value="balance_asc">Net Flow (Low→High)</option>
                                        <option value="generation">Generation</option>
                                        <option value="consumption">Consumption</option>
                                        <option value="battery">Battery</option>
                                        <option value="voltage">Voltage (Low→High)</option>
                                    </select>
                                    <ChevronDown className="w-4 h-4 text-[var(--lbl)] absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                                </div>

                                <div className="flex border border-[var(--line-2)]">
                                    <button
                                        onClick={() => setViewType('grid')}
                                        className={cn("hmi-btn px-2 py-2 border-0 border-r border-[var(--line-2)]", viewType === 'grid' && "active")}
                                    >
                                        <LayoutGrid className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => setViewType('list')}
                                        className={cn("hmi-btn px-2 py-2 border-0", viewType === 'list' && "active")}
                                    >
                                        <ListIcon className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div className={cn(viewType === 'grid' ? "grid grid-cols-1 md:grid-cols-2 gap-4" : "flex flex-col gap-2", "min-h-[400px]")}>
                            {paginatedMeters.map(meter => (
                                viewType === 'grid'
                                    ? <MeterCard key={meter.meter_id} reading={meter} onClick={() => openMeterPage(meter.meter_id)} onEdit={handleEditMeter} onMeta={handleEditMetadata} onDelete={deleteMeter} />
                                    : <MeterListItem key={meter.meter_id} reading={meter} onClick={() => openMeterPage(meter.meter_id)} onEdit={handleEditMeter} onMeta={handleEditMetadata} onDelete={deleteMeter} />
                            ))}
                            {paginatedMeters.length === 0 && (
                                <div className="col-span-full flex flex-col items-center justify-center p-12 text-[var(--lbl-dim)] border border-dashed border-[var(--line)] bg-[var(--panel-2)]">
                                    <Activity className="w-12 h-12 mb-4 opacity-20" />
                                    <h3 className="hmi-title text-[13px] text-[var(--lbl)] mb-1">No Meters Found</h3>
                                    <p className="text-sm text-[var(--lbl-dim)]">
                                        {readings.length === 0
                                            ? "Start the backend simulator to begin receiving telemetry."
                                            : "No meters match your search criteria."}
                                    </p>
                                </div>
                            )}
                        </div>
                        <Pagination currentPage={currentPage} totalPages={totalPages} startIndex={startIndex} endIndex={endIndex} totalItems={totalItems} onPageChange={goToPage} onPrevPage={prevPage} onNextPage={nextPage} />
                    </div>
                </div>
            </main>

            <AddMeterModal isOpen={isAddModalOpen} onClose={() => setIsAddModalOpen(false)} onSuccess={() => { }} />
            <EditMeterModal 
                isOpen={isEditModalOpen} 
                onClose={() => { setIsEditModalOpen(false); setSelectedMeter(null); }} 
                onSuccess={() => { fetchInitialMeters(); }}
                meter={selectedMeter}
            />
            <MetadataProfileModal
                isOpen={isMetaModalOpen}
                onClose={() => { setIsMetaModalOpen(false); setSelectedMeter(null); }}
                onSuccess={() => { fetchInitialMeters(); }}
                meter={selectedMeter}
            />
        </div>
    );
};

export default Dashboard;
