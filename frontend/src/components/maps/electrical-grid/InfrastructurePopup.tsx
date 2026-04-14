/**
 * Infrastructure Popup Component
 */

import { Zap, MapPin, Calendar, Activity } from 'lucide-react';
import type { ElectricalInfrastructure } from './types';
import { OPERATOR_INFO } from './types';
import { getVoltageColor } from './mapLayers';

interface InfrastructurePopupProps {
  infrastructure: ElectricalInfrastructure;
  onSelect: (item: ElectricalInfrastructure) => void;
}

export const InfrastructurePopup = ({
  infrastructure,
  onSelect
}: InfrastructurePopupProps) => {
  const operatorInfo = OPERATOR_INFO[infrastructure.operator];

  return (
    <div className="w-64">
      {/* Header */}
      <div className="mb-3">
        <div className="flex items-center space-x-2 mb-1">
          <Zap className="w-4 h-4" style={{ color: operatorInfo.color }} />
          <span className="text-xs font-semibold" style={{ color: operatorInfo.color }}>
            {infrastructure.operator}
          </span>
        </div>
        <h3 className="text-lg font-bold text-gray-900">
          {infrastructure.name_en || infrastructure.id}
        </h3>
        {infrastructure.name_th && (
          <p className="text-sm text-gray-600">{infrastructure.name_th}</p>
        )}
      </div>

      {/* Details */}
      <div className="space-y-2 text-sm">
        {/* Type */}
        <div className="flex items-center text-gray-700">
          <Activity className="w-4 h-4 mr-2 text-gray-400" />
          <span className="capitalize">{infrastructure.type.replace(/_/g, ' ')}</span>
        </div>

        {/* Voltage */}
        {infrastructure.voltage_kv && (
          <div className="flex items-center text-gray-700">
            <Zap className="w-4 h-4 mr-2" style={{ color: getVoltageColor(infrastructure.voltage_kv) }} />
            <span className="font-semibold">{infrastructure.voltage_kv} kV</span>
          </div>
        )}

        {/* Location */}
        {(infrastructure.province || infrastructure.district) && (
          <div className="flex items-center text-gray-700">
            <MapPin className="w-4 h-4 mr-2 text-gray-400" />
            <span>
              {infrastructure.district && `${infrastructure.district}, `}
              {infrastructure.province}
            </span>
          </div>
        )}

        {/* Commissioning Year */}
        {infrastructure.commissioning_year && (
          <div className="flex items-center text-gray-700">
            <Calendar className="w-4 h-4 mr-2 text-gray-400" />
            <span>Commissioned {infrastructure.commissioning_year}</span>
          </div>
        )}

        {/* Status */}
        {infrastructure.status && (
          <div className="flex items-center">
            <span className="text-gray-500 mr-2">Status:</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
              infrastructure.status === 'operational' ? 'bg-green-100 text-green-700' :
              infrastructure.status === 'under_construction' ? 'bg-yellow-100 text-yellow-700' :
              'bg-gray-100 text-gray-700'
            }`}>
              {infrastructure.status.replace(/_/g, ' ')}
            </span>
          </div>
        )}

        {/* Reference */}
        {infrastructure.ref && (
          <div className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-200">
            Ref: {infrastructure.ref}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="mt-3 pt-3 border-t border-gray-200">
        <button
          onClick={() => onSelect(infrastructure)}
          className="w-full px-3 py-2 bg-yellow-500 text-black rounded-lg hover:bg-yellow-600 text-sm font-semibold"
        >
          View Details
        </button>
      </div>
    </div>
  );
};
