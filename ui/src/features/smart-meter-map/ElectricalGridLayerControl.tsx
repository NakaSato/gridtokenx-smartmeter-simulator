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
            {/* Main Toggle Button */}
            <button
                onClick={onToggleVisible}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg shadow-lg transition-all ${
                    visible
                        ? 'bg-yellow-500 text-black hover:bg-yellow-600'
                        : 'bg-gray-800 text-white hover:bg-gray-700'
                }`}
                title="Toggle Electrical Grid Layer"
            >
                <Layers className="w-4 h-4" />
                <span className="text-sm font-semibold">Grid</span>
            </button>

            {/* Filter Button (only show when visible) */}
            {visible && (
                <button
                    onClick={() => setShowFilters(!showFilters)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg shadow-lg transition-all ${
                        showFilters
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-800 text-white hover:bg-gray-700'
                    }`}
                    title="Filter Electrical Grid"
                >
                    <Filter className="w-4 h-4" />
                    <span className="text-sm">Filter</span>
                </button>
            )}

            {/* Filter Panel */}
            {showFilters && visible && (
                <div className="absolute top-16 right-4 z-[1000] w-72 bg-gray-800 bg-opacity-95 rounded-lg shadow-xl p-4 max-h-[80vh] overflow-y-auto">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-white font-bold flex items-center">
                            <Filter className="w-4 h-4 mr-2" />
                            Electrical Grid Filters
                        </h3>
                        <button
                            onClick={() => setShowFilters(false)}
                            className="text-gray-400 hover:text-white"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>

                    {/* Operators */}
                    <div className="mb-4">
                        <h4 className="text-xs text-gray-400 font-semibold mb-2 uppercase">
                            Operators
                        </h4>
                        <div className="space-y-2">
                            {(['EGAT', 'MEA', 'PEA'] as const).map(operator => {
                                const colors = {
                                    EGAT: '#EF4444',
                                    MEA: '#3B82F6',
                                    PEA: '#10B981'
                                };

                                return (
                                    <label
                                        key={operator}
                                        className="flex items-center justify-between p-2 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600"
                                    >
                                        <div className="flex items-center">
                                            <input
                                                type="checkbox"
                                                checked={filters.operators.includes(operator)}
                                                onChange={() => toggleOperator(operator)}
                                                className="w-4 h-4 rounded focus:ring-yellow-500"
                                            />
                                            <span className="ml-2 text-white text-sm">
                                                {operator}
                                            </span>
                                        </div>
                                        <div
                                            className="w-3 h-3 rounded-full"
                                            style={{ backgroundColor: colors[operator] }}
                                        />
                                    </label>
                                );
                            })}
                        </div>
                    </div>

                    {/* Infrastructure Types */}
                    <div>
                        <h4 className="text-xs text-gray-400 font-semibold mb-2 uppercase">
                            Types
                        </h4>
                        <div className="space-y-2">
                            {[
                                { id: 'transmission_substation', label: 'Transmission Substation' },
                                { id: 'distribution_substation', label: 'Distribution Substation' },
                                { id: 'transmission_tower', label: 'Transmission Tower' },
                                { id: 'distribution_pole', label: 'Distribution Pole' },
                                { id: 'power_plant', label: 'Power Plant' },
                                { id: 'solar_farm', label: 'Solar Farm' },
                                { id: 'battery_storage', label: 'Battery Storage' },
                                { id: 'ev_charging_station', label: 'EV Charging' }
                            ].map(type => (
                                <label
                                    key={type.id}
                                    className="flex items-center p-2 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600"
                                >
                                    <input
                                        type="checkbox"
                                        checked={filters.types.includes(type.id)}
                                        onChange={() => toggleType(type.id)}
                                        className="w-4 h-4 rounded focus:ring-yellow-500"
                                    />
                                    <span className="ml-2 text-white text-sm">
                                        {type.label}
                                    </span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Reset Button */}
                    <div className="mt-4 pt-4 border-t border-gray-700">
                        <button
                            onClick={() => {
                                setFilters(DEFAULT_FILTERS);
                                onFilterChange?.(DEFAULT_FILTERS);
                            }}
                            className="w-full px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-500 text-sm"
                        >
                            Reset Filters
                        </button>
                    </div>
                </div>
            )}
        </>
    );
};
