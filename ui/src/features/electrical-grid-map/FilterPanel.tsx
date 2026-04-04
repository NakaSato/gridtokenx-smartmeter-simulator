/**
 * Filter Panel Component
 */

import { X, Search, Check } from 'lucide-react';
import type { FilterState, InfrastructureType } from './types';
import { OPERATOR_INFO, INFRASTRUCTURE_LAYERS } from './types';

interface FilterPanelProps {
  filters: FilterState;
  onUpdateFilters: (updates: Partial<FilterState>) => void;
  onResetFilters: () => void;
  onClose: () => void;
  stats: any;
}

export const FilterPanel = ({
  filters,
  onUpdateFilters,
  onResetFilters,
  onClose,
  stats
}: FilterPanelProps) => {
  const toggleOperator = (operator: 'EGAT' | 'MEA' | 'PEA') => {
    const current = filters.operators;
    const updated = current.includes(operator)
      ? current.filter(o => o !== operator)
      : [...current, operator];
    
    if (updated.length > 0) {
      onUpdateFilters({ operators: updated });
    }
  };

  const toggleType = (type: InfrastructureType) => {
    const current = filters.types;
    const updated = current.includes(type)
      ? current.filter(t => t !== type)
      : [...current, type];
    
    if (updated.length > 0) {
      onUpdateFilters({ types: updated });
    }
  };

  return (
    <div className="absolute top-20 right-4 z-20 w-80 bg-gray-800 rounded-lg shadow-xl max-h-[calc(100vh-12rem)] overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <h2 className="text-lg font-bold text-white flex items-center">
          <Search className="w-5 h-5 mr-2" />
          Filters
        </h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={onResetFilters}
            className="text-xs text-yellow-400 hover:text-yellow-300"
          >
            Reset
          </button>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Operators */}
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Operators</h3>
          <div className="space-y-2">
            {(['EGAT', 'MEA', 'PEA'] as const).map(operator => (
              <label
                key={operator}
                className="flex items-center justify-between p-2 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600"
              >
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.operators.includes(operator)}
                    onChange={() => toggleOperator(operator)}
                    className="w-4 h-4 text-yellow-500 rounded focus:ring-yellow-500"
                  />
                  <span className="ml-2 text-white text-sm">{operator}</span>
                </div>
                <div className="flex items-center">
                  <div
                    className="w-3 h-3 rounded-full mr-2"
                    style={{ backgroundColor: OPERATOR_INFO[operator].color }}
                  />
                  <span className="text-xs text-gray-400">
                    {stats?.byOperator?.[operator] || 0}
                  </span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Infrastructure Types */}
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Infrastructure Types</h3>
          <div className="space-y-2">
            {INFRASTRUCTURE_LAYERS.map(layer => (
              <label
                key={layer.id}
                className="flex items-center justify-between p-2 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600"
              >
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.types.includes(layer.type)}
                    onChange={() => toggleType(layer.type)}
                    className="w-4 h-4 rounded focus:ring-yellow-500"
                    style={{ color: layer.color }}
                  />
                  <span className="ml-2 text-white text-sm capitalize">
                    {layer.type.replace(/_/g, ' ')}
                  </span>
                </div>
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: layer.color }}
                />
              </label>
            ))}
          </div>
        </div>

        {/* Search */}
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Search</h3>
          <input
            type="text"
            value={filters.searchQuery}
            onChange={(e) => onUpdateFilters({ searchQuery: e.target.value })}
            placeholder="Search by name, ID, location..."
            className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
          />
        </div>

        {/* Stats */}
        <div className="pt-4 border-t border-gray-700">
          <div className="text-xs text-gray-400">
            <div className="flex justify-between mb-1">
              <span>Showing</span>
              <span className="text-white font-semibold">
                {filters.types.length} of {INFRASTRUCTURE_LAYERS.length} types
              </span>
            </div>
            <div className="flex justify-between">
              <span>Operators</span>
              <span className="text-white font-semibold">
                {filters.operators.length} of 3
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
