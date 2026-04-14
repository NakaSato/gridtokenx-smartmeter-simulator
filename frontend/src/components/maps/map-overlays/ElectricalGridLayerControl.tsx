"use client";

/**
 * Electrical Grid Layer Control Component
 * 
 * Toggle and filter controls for electrical infrastructure overlay
 */

import { useState } from 'react';
import { Layers, Filter, X } from 'lucide-react';

interface ElectricalGridLayerControlProps {
    visible: boolean;
    onToggleVisible: () => void;
    onFilterChange?: (filters: ElectricalGridFilters) => void;
}

interface ElectricalGridFilters {
    operators: ('EGAT' | 'MEA' | 'PEA')[];
    types: string[];
}

const DEFAULT_FILTERS: ElectricalGridFilters = {
    operators: ['EGAT', 'MEA', 'PEA'],
    types: [
        'transmission_substation',
        'distribution_substation',
        'transmission_tower',
        'distribution_pole',
        'power_plant',
        'solar_farm',
        'battery_storage',
        'ev_charging_station'
    ]
};

export const ElectricalGridLayerControl = ({
    visible,
    onToggleVisible,
    onFilterChange
}: ElectricalGridLayerControlProps) => {
    const [showFilters, setShowFilters] = useState(false);
    const [filters, setFilters] = useState<ElectricalGridFilters>(DEFAULT_FILTERS);

    const toggleOperator = (operator: 'EGAT' | 'MEA' | 'PEA') => {
        const updated = filters.operators.includes(operator)
            ? filters.operators.filter(o => o !== operator)
            : [...filters.operators, operator];

        if (updated.length === 0) return; // Must have at least one operator

        const newFilters = { ...filters, operators: updated };
        setFilters(newFilters);
        onFilterChange?.(newFilters);
    };

    const toggleType = (type: string) => {
        const updated = filters.types.includes(type)
            ? filters.types.filter(t => t !== type)
            : [...filters.types, type];

        if (updated.length === 0) return; // Must have at least one type

        const newFilters = { ...filters, types: updated };
        setFilters(newFilters);
        onFilterChange?.(newFilters);
    };

    return (
        <>
            {/* Main Toggle Button - Bottom Left */}
            <button
                onClick={onToggleVisible}
                className={`flex items-center space-x-2 px-3 py-2 rounded-xl shadow-2xl backdrop-blur-xl border transition-all ${
                    visible
                        ? 'bg-yellow-500/90 border-yellow-400/50 text-black hover:bg-yellow-500'
                        : 'bg-slate-800/90 border-slate-700/50 text-white hover:bg-slate-700/90'
                }`}
                title="Toggle Electrical Grid Layer"
            >
                <Layers className="w-4 h-4" />
                <span className="text-xs font-bold">{visible ? 'Hide Grid' : 'Show Grid'}</span>
            </button>

            {/* Filter Button - Bottom Left, next to toggle */}
            {visible && (
                <button
                    onClick={() => setShowFilters(!showFilters)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-xl shadow-2xl backdrop-blur-xl border transition-all ${
                        showFilters
                            ? 'bg-indigo-500/90 border-indigo-400/50 text-white'
                            : 'bg-slate-800/90 border-slate-700/50 text-white hover:bg-slate-700/90'
                    }`}
                    title="Filter Electrical Grid"
                >
                    <Filter className="w-4 h-4" />
                    <span className="text-xs font-semibold">Filter</span>
                </button>
            )}

            {/* Filter Panel - Bottom Left */}
            {showFilters && visible && (
                <div className="absolute bottom-16 right-4 sm:bottom-20 sm:right-6 z-[1000] w-72 sm:w-80 bg-slate-800/95 backdrop-blur-xl rounded-xl shadow-2xl border border-slate-700/50 p-4 max-h-[80vh] overflow-y-auto">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-700/50">
                        <h3 className="text-white font-bold flex items-center text-sm">
                            <Filter className="w-4 h-4 mr-2 text-indigo-400" />
                            Electrical Grid Filters
                        </h3>
                        <button
                            onClick={() => setShowFilters(false)}
                            className="text-gray-400 hover:text-white transition-colors p-1 rounded-md hover:bg-slate-700/50"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>

                    {/* Operators */}
                    <div className="mb-4">
                        <h4 className="text-xs text-slate-400 font-semibold mb-2 uppercase tracking-wider">
                            Operators
                        </h4>
                        <div className="space-y-1.5">
                            {(['EGAT', 'MEA', 'PEA'] as const).map(operator => {
                                const colors = {
                                    EGAT: '#EF4444',
                                    MEA: '#3B82F6',
                                    PEA: '#10B981'
                                };
                                const isActive = filters.operators.includes(operator);

                                return (
                                    <label
                                        key={operator}
                                        className={`flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition-all ${
                                            isActive
                                                ? 'bg-slate-700/70 ring-1 ring-slate-600/50'
                                                : 'bg-slate-900/30 hover:bg-slate-700/30'
                                        }`}
                                    >
                                        <div className="flex items-center gap-2.5">
                                            <div className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all ${
                                                isActive ? 'border-indigo-500 bg-indigo-500' : 'border-slate-600'
                                            }`}>
                                                {isActive && (
                                                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                                    </svg>
                                                )}
                                            </div>
                                            <input
                                                type="checkbox"
                                                checked={isActive}
                                                onChange={() => toggleOperator(operator)}
                                                className="sr-only"
                                            />
                                            <span className="text-sm font-semibold text-white">
                                                {operator}
                                            </span>
                                        </div>
                                        <div
                                            className="w-2.5 h-2.5 rounded-full"
                                            style={{ backgroundColor: colors[operator] }}
                                        />
                                    </label>
                                );
                            })}
                        </div>
                    </div>

                    {/* Infrastructure Types */}
                    <div>
                        <h4 className="text-xs text-slate-400 font-semibold mb-2 uppercase tracking-wider">
                            Infrastructure Types
                        </h4>
                        <div className="grid grid-cols-2 gap-1.5">
                            {[
                                { id: 'transmission_substation', label: 'TX Substation', color: '#EF4444' },
                                { id: 'distribution_substation', label: 'DX Substation', color: '#F59E0B' },
                                { id: 'transmission_tower', label: 'TX Tower', color: '#8B5CF6' },
                                { id: 'distribution_pole', label: 'DX Pole', color: '#6B7280' },
                                { id: 'power_plant', label: 'Power Plant', color: '#EC4899' },
                                { id: 'solar_farm', label: 'Solar Farm', color: '#FBBF24' },
                                { id: 'battery_storage', label: 'Battery', color: '#10B981' },
                                { id: 'ev_charging_station', label: 'EV Charge', color: '#3B82F6' }
                            ].map(type => {
                                const isActive = filters.types.includes(type.id);
                                return (
                                    <button
                                        key={type.id}
                                        onClick={() => toggleType(type.id)}
                                        className={`flex items-center gap-2 p-2 rounded-lg text-left transition-all text-xs ${
                                            isActive
                                                ? 'bg-slate-700/70 ring-1 ring-slate-600/50'
                                                : 'bg-slate-900/30 hover:bg-slate-700/30'
                                        }`}
                                    >
                                        <div
                                            className="w-2 h-2 rounded-full flex-shrink-0"
                                            style={{ backgroundColor: type.color }}
                                        />
                                        <span className="text-slate-200 truncate">
                                            {type.label}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Reset Button */}
                    <div className="mt-4 pt-3 border-t border-slate-700/50">
                        <button
                            onClick={() => {
                                setFilters(DEFAULT_FILTERS);
                                onFilterChange?.(DEFAULT_FILTERS);
                            }}
                            className="w-full px-3 py-2 bg-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-600/50 text-xs font-semibold transition-colors"
                        >
                            Reset Filters
                        </button>
                    </div>
                </div>
            )}
        </>
    );
};
