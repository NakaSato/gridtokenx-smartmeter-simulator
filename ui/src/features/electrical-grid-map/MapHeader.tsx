/**
 * Map Header Component
 */

import { Zap, Filter, Layers, Maximize, RefreshCw } from 'lucide-react';
import type { ElectricalGridStats } from './types';

interface MapHeaderProps {
  stats: ElectricalGridStats;
  totalInfrastructure: number;
  filteredCount: number;
  onToggleFilters: () => void;
  onToggleLegend: () => void;
  onFitToBounds: () => void;
  onRefresh?: () => void;
  lastRefresh?: Date | null;
}

export const MapHeader = ({
  stats,
  totalInfrastructure,
  filteredCount,
  onToggleFilters,
  onToggleLegend,
  onFitToBounds,
  onRefresh,
  lastRefresh
}: MapHeaderProps) => {
  const formatTime = (date: Date | null) => {
    if (!date) return '—';
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div className="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-gray-900/90 to-transparent p-4">
      <div className="flex items-center justify-between">
        {/* Title */}
        <div className="flex items-center space-x-3">
          <div className="bg-yellow-500 p-2 rounded-lg">
            <Zap className="w-6 h-6 text-black" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Thai Electrical Grid Map</h1>
            <div className="flex items-center gap-2">
              <p className="text-xs text-gray-400">
                EGAT • MEA • PEA Infrastructure
              </p>
              <span className="text-[10px] text-gray-500">
                Updated: {formatTime(lastRefresh)}
              </span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2">
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="flex items-center space-x-2 px-3 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
              title="Refresh data"
            >
              <RefreshCw className="w-4 h-4" />
              <span className="text-sm">Refresh</span>
            </button>
          )}

          <button
            onClick={onFitToBounds}
            className="flex items-center space-x-2 px-3 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
            title="Fit to infrastructure"
          >
            <Maximize className="w-4 h-4" />
            <span className="text-sm">Fit</span>
          </button>

          <button
            onClick={onToggleLegend}
            className="flex items-center space-x-2 px-3 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
            title="Toggle legend"
          >
            <Layers className="w-4 h-4" />
            <span className="text-sm">Legend</span>
          </button>

          <button
            onClick={onToggleFilters}
            className="flex items-center space-x-2 px-3 py-2 bg-yellow-500 text-black rounded-lg hover:bg-yellow-600 transition-colors"
            title="Toggle filters"
          >
            <Filter className="w-4 h-4" />
            <span className="text-sm font-semibold">Filters</span>
            {filteredCount < totalInfrastructure && (
              <span className="ml-1 px-2 py-0.5 bg-black bg-opacity-20 rounded-full text-xs">
                {filteredCount}/{totalInfrastructure}
              </span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
