/**
 * Map Legend Component
 */

import { X } from 'lucide-react';
import { INFRASTRUCTURE_LAYERS, OPERATOR_INFO } from './types';
import type { InfrastructureLayer } from './types';

interface MapLegendProps {
  visible: boolean;
  onClose: () => void;
}

export const MapLegend = ({ visible, onClose }: MapLegendProps) => {
  if (!visible) return null;

  return (
    <div className="absolute bottom-20 right-4 z-10 w-64 bg-gray-800 bg-opacity-95 rounded-lg shadow-xl p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-white font-bold">Legend</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-white">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Operators */}
      <div className="mb-4">
        <h4 className="text-xs text-gray-400 font-semibold mb-2 uppercase">Operators</h4>
        <div className="space-y-1">
          {Object.entries(OPERATOR_INFO).map(([operator, info]) => (
            <div key={operator} className="flex items-center text-sm">
              <div
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: info.color }}
              />
              <span className="text-white">{operator}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Infrastructure Types */}
      <div>
        <h4 className="text-xs text-gray-400 font-semibold mb-2 uppercase">Infrastructure</h4>
        <div className="space-y-1">
          {INFRASTRUCTURE_LAYERS.map(layer => (
            <div key={layer.id} className="flex items-center text-sm">
              <div
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: layer.color }}
              />
              <span className="text-gray-300 capitalize">
                {layer.type.replace(/_/g, ' ')}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Voltage Colors */}
      <div className="mt-4 pt-4 border-t border-gray-700">
        <h4 className="text-xs text-gray-400 font-semibold mb-2 uppercase">Voltage Levels</h4>
        <div className="space-y-1">
          <div className="flex items-center text-sm">
            <div className="w-3 h-3 rounded-full mr-2 bg-red-600" />
            <span className="text-gray-300">500 kV</span>
          </div>
          <div className="flex items-center text-sm">
            <div className="w-3 h-3 rounded-full mr-2 bg-orange-600" />
            <span className="text-gray-300">230 kV</span>
          </div>
          <div className="flex items-center text-sm">
            <div className="w-3 h-3 rounded-full mr-2 bg-yellow-600" />
            <span className="text-gray-300">115 kV</span>
          </div>
          <div className="flex items-center text-sm">
            <div className="w-3 h-3 rounded-full mr-2 bg-green-600" />
            <span className="text-gray-300">22 kV</span>
          </div>
          <div className="flex items-center text-sm">
            <div className="w-3 h-3 rounded-full mr-2 bg-cyan-600" />
            <span className="text-gray-300">33 kV</span>
          </div>
        </div>
      </div>
    </div>
  );
};
