"use client";

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
    ChevronLeft,
    Zap,
    Leaf,
    TrendingUp,
    MapPin,
    Upload,
    Search,
    Filter,
    BarChart3,
    Database,
    AlertCircle,
    CheckCircle2,
    XCircle,
    RefreshCw,
} from 'lucide-react';
import { StatCard } from '@/components/ui/StatCard';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { useApi } from '@/hooks/useApi';
import type { PowerPlant, PowerPlantStats, BatchImportResponse, NearbyPlant } from '@/lib/types';

const PowerPlantsDashboard = () => {
    const { getApiUrl } = useNetwork();
    const { apiCall, isLoading, error } = useApi(getApiUrl, () => {});

    // State
    const [stats, setStats] = useState<PowerPlantStats | null>(null);
    const [plants, setPlants] = useState<PowerPlant[]>([]);
    const [nearbyPlants, setNearbyPlants] = useState<NearbyPlant[]>([]);
    const [totalPlants, setTotalPlants] = useState(0);
    const [page, setPage] = useState(0);
    const [filterType, setFilterType] = useState<string>('');
    const [renewableOnly, setRenewableOnly] = useState(false);
    const [showImport, setShowImport] = useState(false);
    const [showNearby, setShowNearby] = useState(false);
    const [nearbyLat, setNearbyLat] = useState(13.75);
    const [nearbyLon, setNearbyLon] = useState(100.5);
    const [nearbyRadius, setNearbyRadius] = useState(100);
    const [importing, setImporting] = useState(false);
    const [importResult, setImportResult] = useState<BatchImportResponse | null>(null);

    const limit = 20;

    // Fetch stats
    const fetchStats = useCallback(async () => {
        try {
            const res = await fetch(getApiUrl('/api/v1/power-plants/stats'));
            if (res.ok) {
                const data = await res.json();
                setStats(data);
            }
        } catch (err) {
            console.error('Failed to fetch stats:', err);
        }
    }, [getApiUrl]);

    // Fetch plants list
    const fetchPlants = useCallback(async () => {
        try {
            const params = new URLSearchParams({
                limit: limit.toString(),
                offset: (page * limit).toString(),
                status: 'operating',
            });

            if (filterType) params.append('plant_type', filterType);
            if (renewableOnly) params.append('renewable_only', 'true');

            const res = await fetch(getApiUrl(`/api/v1/power-plants?${params}`));
            if (res.ok) {
                const data = await res.json();
                setPlants(data.plants);
                setTotalPlants(data.total);
            }
        } catch (err) {
            console.error('Failed to fetch plants:', err);
        }
    }, [getApiUrl, page, filterType, renewableOnly]);

    // Initial load
    useEffect(() => {
        fetchStats();
        fetchPlants();
    }, [fetchStats, fetchPlants]);

    // Handle file import
    const handleFileImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setImporting(true);
        setImportResult(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const res = await fetch(getApiUrl('/api/v1/power-plants/import'), {
                method: 'POST',
                body: formData,
            });

            if (res.ok) {
                const result: BatchImportResponse = await res.json();
                setImportResult(result);
                // Refresh data
                await fetchStats();
                await fetchPlants();
            } else {
                const err = await res.json();
                setImportResult({ created: 0, errors: 1, error_details: [err.detail || 'Import failed'] });
            }
        } catch (err) {
            setImportResult({ created: 0, errors: 1, error_details: [String(err)] });
        } finally {
            setImporting(false);
        }
    };

    // Handle nearby search
    const handleNearbySearch = async () => {
        try {
            const params = new URLSearchParams({
                lat: nearbyLat.toString(),
                lon: nearbyLon.toString(),
                radius_km: nearbyRadius.toString(),
                status: 'operating',
            });

            const res = await fetch(getApiUrl(`/api/v1/power-plants/search/nearby?${params}`));
            if (res.ok) {
                const data = await res.json();
                setNearbyPlants(data.plants);
                setShowNearby(true);
            }
        } catch (err) {
            console.error('Nearby search failed:', err);
        }
    };


    // Get plant type color
    const getPlantTypeColor = (type: string) => {
        const colors: Record<string, string> = {
            solar: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
            wind: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
            hydropower: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
            'oil/gas': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
            coal: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
            bioenergy: 'bg-green-500/20 text-green-400 border-green-500/30',
        };
        return colors[type] || 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30';
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200">
            <div className="max-w-7xl mx-auto p-6 space-y-8 animate-in fade-in duration-500">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3">
                            <Link href="/dashboard" className="p-2 rounded-lg bg-slate-900/50 hover:bg-slate-800 transition-colors">
                                <ChevronLeft className="w-6 h-6" />
                            </Link>
                            <h1 className="text-4xl font-black tracking-tighter text-white uppercase">Thailand Power Plants</h1>
                        </div>
                        <p className="text-slate-400 font-medium pl-14">Real-world generation assets with PostGIS spatial tracking</p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => setShowImport(!showImport)}
                            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-semibold transition-colors flex items-center gap-2"
                        >
                            <Upload className="w-4 h-4" />
                            Import GeoJSON
                        </button>
                        <button
                            onClick={() => { fetchStats(); fetchPlants(); }}
                            className="p-2 bg-slate-900/50 hover:bg-slate-800 rounded-lg transition-colors"
                        >
                            <RefreshCw className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Import Section */}
                {showImport && (
                    <div className="glass rounded-2xl p-6 space-y-4 animate-in fade-in slide-in-from-top-4 duration-300">
                        <h3 className="text-xl font-black text-white uppercase tracking-wider flex items-center gap-2">
                            <Database className="w-5 h-5" />
                            Import Power Plants from GeoJSON
                        </h3>
                        <div className="flex items-center gap-4">
                            <label className="flex-1 flex items-center justify-center px-6 py-8 border-2 border-dashed border-slate-600 rounded-xl cursor-pointer hover:border-indigo-500 transition-colors">
                                <input
                                    type="file"
                                    accept=".geojson,.json"
                                    onChange={handleFileImport}
                                    className="hidden"
                                    disabled={importing}
                                />
                                <div className="text-center">
                                    <Upload className="w-8 h-8 mx-auto mb-2 text-slate-400" />
                                    <p className="text-sm text-slate-400">
                                        {importing ? 'Uploading...' : 'Click to upload GeoJSON file'}
                                    </p>
                                </div>
                            </label>
                        </div>
                        {importResult && (
                            <div className="space-y-2">
                                {importResult.created > 0 && (
                                    <div className="flex items-center gap-2 text-emerald-400">
                                        <CheckCircle2 className="w-5 h-5" />
                                        <span className="font-semibold">{importResult.created} plants imported successfully</span>
                                    </div>
                                )}
                                {importResult.errors > 0 && (
                                    <div className="space-y-1">
                                        <div className="flex items-center gap-2 text-rose-400">
                                            <XCircle className="w-5 h-5" />
                                            <span className="font-semibold">{importResult.errors} errors</span>
                                        </div>
                                        {importResult.error_details.slice(0, 5).map((err, i) => (
                                            <p key={i} className="text-xs text-rose-300 ml-7">{err}</p>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* Stats Cards */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <StatCard
                            title="Total Plants"
                            value={stats.total.count}
                            unit="plants"
                            icon={<Zap className="w-6 h-6" />}
                            status="info"
                        />
                        <StatCard
                            title="Total Capacity"
                            value={stats.total.capacity_mw.toFixed(0)}
                            unit="MW"
                            icon={<TrendingUp className="w-6 h-6" />}
                            status="success"
                        />
                        <StatCard
                            title="Renewable Share"
                            value={stats.renewable.percentage.toFixed(1)}
                            unit="%"
                            icon={<Leaf className="w-6 h-6" />}
                            status="success"
                        />
                        <StatCard
                            title="Renewable Capacity"
                            value={stats.renewable.capacity_mw.toFixed(0)}
                            unit="MW"
                            icon={<BarChart3 className="w-6 h-6" />}
                            status="info"
                        />
                    </div>
                )}

                {/* Capacity by Type */}
                {stats && Object.keys(stats.by_type).length > 0 && (
                    <div className="glass rounded-2xl p-6 space-y-4">
                        <h3 className="text-xl font-black text-white uppercase tracking-wider">Capacity by Plant Type</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {Object.entries(stats.by_type).map(([type, data]) => (
                                <div key={type} className={`p-4 rounded-xl border ${getPlantTypeColor(type)}`}>
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="font-bold capitalize">{type}</span>
                                        <span className="text-xs opacity-70">{data.plant_count} plants</span>
                                    </div>
                                    <div className="text-2xl font-black">{data.total_capacity_mw.toLocaleString()} MW</div>
                                    <div className="text-xs opacity-60 mt-1">Avg: {data.avg_capacity_mw.toFixed(1)} MW</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Nearby Search */}
                <div className="glass rounded-2xl p-6 space-y-4">
                    <h3 className="text-xl font-black text-white uppercase tracking-wider flex items-center gap-2">
                        <MapPin className="w-5 h-5" />
                        Nearby Plant Search
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <label className="block text-xs text-slate-400 mb-1">Latitude</label>
                            <input
                                type="number"
                                value={nearbyLat}
                                onChange={(e) => setNearbyLat(parseFloat(e.target.value))}
                                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                                step="0.01"
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-slate-400 mb-1">Longitude</label>
                            <input
                                type="number"
                                value={nearbyLon}
                                onChange={(e) => setNearbyLon(parseFloat(e.target.value))}
                                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                                step="0.01"
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-slate-400 mb-1">Radius (km)</label>
                            <input
                                type="number"
                                value={nearbyRadius}
                                onChange={(e) => setNearbyRadius(parseInt(e.target.value))}
                                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                                min="1"
                                max="500"
                            />
                        </div>
                        <div className="flex items-end">
                            <button
                                onClick={handleNearbySearch}
                                className="w-full px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
                            >
                                <Search className="w-4 h-4" />
                                Search
                            </button>
                        </div>
                    </div>

                    {showNearby && nearbyPlants.length > 0 && (
                        <div className="space-y-2 mt-4">
                            <p className="text-sm text-slate-400">Found {nearbyPlants.length} plants</p>
                            <div className="max-h-64 overflow-y-auto space-y-2">
                                {nearbyPlants.map((plant) => (
                                    <div key={plant.plant_id} className="p-3 bg-slate-900/50 rounded-lg flex justify-between items-center">
                                        <div>
                                            <div className="font-semibold text-white">{plant.name}</div>
                                            <div className="text-xs text-slate-400">
                                                {plant.plant_type} • {plant.capacity_mw} MW • {plant.operator}
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-cyan-400 font-bold">{plant.distance_km.toFixed(1)} km</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Filters */}
                <div className="glass rounded-2xl p-4 flex flex-wrap gap-4 items-center">
                    <Filter className="w-5 h-5 text-slate-400" />
                    <select
                        value={filterType}
                        onChange={(e) => { setFilterType(e.target.value); setPage(0); }}
                        className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm"
                    >
                        <option value="">All Types</option>
                        <option value="solar">Solar</option>
                        <option value="wind">Wind</option>
                        <option value="hydropower">Hydropower</option>
                        <option value="oil/gas">Oil/Gas</option>
                        <option value="coal">Coal</option>
                        <option value="bioenergy">Bioenergy</option>
                    </select>
                    <label className="flex items-center gap-2 text-sm">
                        <input
                            type="checkbox"
                            checked={renewableOnly}
                            onChange={(e) => { setRenewableOnly(e.target.checked); setPage(0); }}
                            className="rounded"
                        />
                        <span className="text-slate-300">Renewable Only</span>
                    </label>
                    <div className="ml-auto text-sm text-slate-400">
                        {totalPlants} plants total
                    </div>
                </div>

                {/* Plants List */}
                <div className="glass rounded-2xl p-6 space-y-4">
                    <h3 className="text-xl font-black text-white uppercase tracking-wider">Power Plants</h3>

                    {plants.length === 0 ? (
                        <div className="text-center py-12 text-slate-500">
                            <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                            <p>No plants found</p>
                            <p className="text-sm mt-2">Import GeoJSON data or adjust filters</p>
                        </div>
                    ) : (
                        <>
                            <div className="space-y-2">
                                {plants.map((plant) => (
                                    <div key={plant.plant_id} className="p-4 bg-slate-900/50 rounded-xl hover:bg-slate-900 transition-colors">
                                        <div className="flex justify-between items-start">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <h4 className="font-bold text-white text-lg">{plant.name}</h4>
                                                    <span className={`px-2 py-1 rounded-md text-xs font-semibold border ${getPlantTypeColor(plant.plant_type)}`}>
                                                        {plant.plant_type}
                                                    </span>
                                                    {plant.is_renewable && (
                                                        <span className="px-2 py-1 rounded-md text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                                                            <Leaf className="w-3 h-3" />
                                                            Renewable
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                                                    <div>
                                                        <span className="text-slate-500">Capacity</span>
                                                        <div className="text-white font-semibold">{plant.capacity_mw} MW</div>
                                                    </div>
                                                    <div>
                                                        <span className="text-slate-500">Operator</span>
                                                        <div className="text-white font-semibold">{plant.operator}</div>
                                                    </div>
                                                    <div>
                                                        <span className="text-slate-500">Location</span>
                                                        <div className="text-white font-semibold">
                                                            {plant.latitude?.toFixed(4)}, {plant.longitude?.toFixed(4)}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <span className="text-slate-500">Status</span>
                                                        <div className="text-emerald-400 font-semibold capitalize">{plant.status}</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Pagination */}
                            <div className="flex justify-between items-center pt-4 border-t border-slate-800">
                                <button
                                    onClick={() => setPage(p => Math.max(0, p - 1))}
                                    disabled={page === 0}
                                    className="px-4 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
                                >
                                    Previous
                                </button>
                                <span className="text-sm text-slate-400">
                                    Page {page + 1} • Showing {plants.length} of {totalPlants}
                                </span>
                                <button
                                    onClick={() => setPage(p => p + 1)}
                                    disabled={page * limit + plants.length >= totalPlants}
                                    className="px-4 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
                                >
                                    Next
                                </button>
                            </div>
                        </>
                    )}
                </div>

                {/* Error Display */}
                {error && (
                    <div className="glass rounded-2xl p-6 border border-rose-500/30">
                        <div className="flex items-center gap-3 text-rose-400">
                            <AlertCircle className="w-5 h-5" />
                            <span className="font-semibold">{typeof error === 'string' ? error : error?.message || 'Unknown error'}</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PowerPlantsDashboard;
