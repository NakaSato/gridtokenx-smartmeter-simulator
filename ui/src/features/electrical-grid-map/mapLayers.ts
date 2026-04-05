/**
 * Electrical Grid Map Layers
 * 
 * Mapbox GL layers for visualizing electrical infrastructure
 */

import type { LineLayer, CircleLayer, SymbolLayer } from 'react-map-gl';
import type { InfrastructureType } from './types';

// Base styles for infrastructure markers
export const getSubstationCircleLayer = (operator: 'EGAT' | 'MEA' | 'PEA'): CircleLayer => ({
  id: `${operator.toLowerCase()}-substations`,
  type: 'circle',
  paint: {
    'circle-radius': [
      'interpolate', ['linear'], ['zoom'],
      6, 4,
      8, 8,
      12, 12,
      16, 20
    ],
    'circle-color': operator === 'EGAT' ? '#EF4444' : operator === 'MEA' ? '#3B82F6' : '#10B981',
    'circle-stroke-width': 2,
    'circle-stroke-color': '#ffffff',
    'circle-opacity': 0.8
  }
});

export const getPoleCircleLayer = (operator: 'EGAT' | 'MEA' | 'PEA'): CircleLayer => ({
  id: `${operator.toLowerCase()}-poles`,
  type: 'circle',
  paint: {
    'circle-radius': [
      'interpolate', ['linear'], ['zoom'],
      10, 2,
      12, 4,
      14, 6,
      18, 10
    ],
    'circle-color': operator === 'EGAT' ? '#F59E0B' : operator === 'MEA' ? '#60A5FA' : '#34D399',
    'circle-stroke-width': 1,
    'circle-stroke-color': '#ffffff',
    'circle-opacity': 0.7
  }
});

export const getPowerPlantSymbolLayer: SymbolLayer = {
  id: 'power-plants',
  type: 'symbol',
  layout: {
    'icon-image': 'power-plant-15',
    'icon-size': 1.2,
    'text-field': ['get', 'name_en'],
    'text-font': ['Noto Sans Regular'],
    'text-offset': [0, 1.5],
    'text-anchor': 'top',
    'text-size': 12,
    'text-allow-overlap': false
  },
  paint: {
    'text-color': '#8B5CF6',
    'text-halo-color': '#ffffff',
    'text-halo-width': 2
  }
};

export const getTransmissionLineLayer: LineLayer = {
  id: 'transmission-lines',
  type: 'line',
  layout: {
    'line-cap': 'round',
    'line-join': 'round'
  },
  paint: {
    'line-width': [
      'interpolate', ['linear'], ['zoom'],
      6, 1,
      10, 3,
      14, 6
    ],
    'line-color': [
      'match',
      ['get', 'voltage'],
      '500kV', '#DC2626',
      '230kV', '#EA580C',
      '115kV', '#CA8A04',
      '#999999'
    ],
    'line-opacity': 0.7,
    'line-dasharray': [2, 2]
  }
};

// Glow effect layers for emphasis
export const getSubstationGlowLayer = (operator: 'EGAT' | 'MEA' | 'PEA'): CircleLayer => ({
  id: `${operator.toLowerCase()}-substations-glow`,
  type: 'circle',
  paint: {
    'circle-radius': [
      'interpolate', ['linear'], ['zoom'],
      6, 8,
      8, 16,
      12, 24,
      16, 40
    ],
    'circle-color': operator === 'EGAT' ? '#EF4444' : operator === 'MEA' ? '#3B82F6' : '#10B981',
    'circle-opacity': [
      'interpolate', ['linear'], ['zoom'],
      6, 0.1,
      10, 0.2,
      14, 0.3
    ],
    'circle-blur': 0.5
  }
});

// Voltage-based coloring
export const getVoltageColor = (voltageKv: number): string => {
  if (voltageKv >= 500) return '#DC2626';  // Red
  if (voltageKv >= 230) return '#EA580C';  // Orange
  if (voltageKv >= 115) return '#CA8A04';  // Yellow
  if (voltageKv >= 22) return '#16A34A';   // Green
  return '#6B7280';                         // Gray
};

// Operator info map
export const OPERATOR_INFO: Record<string, { name: string; color: string }> = {
  EGAT: { name: 'Electricity Generating Authority of Thailand', color: '#EF4444' },
  MEA: { name: 'Metropolitan Electricity Authority', color: '#3B82F6' },
  PEA: { name: 'Provincial Electricity Authority', color: '#10B981' }
};

// Create dynamic layer based on infrastructure type
export const createInfrastructureLayer = (
  type: InfrastructureType,
  operator: 'EGAT' | 'MEA' | 'PEA',
  sourceId: string
): CircleLayer | SymbolLayer => {
  const baseLayer: any = {
    id: `${operator.toLowerCase()}-${type}`,
    type: 'circle',
    source: sourceId,
    'source-layer': 'infrastructure'
  };

  // Customize based on type
  if (type.includes('substation')) {
    baseLayer.paint = {
      'circle-radius': [
        'interpolate', ['linear'], ['zoom'],
        6, 4,
        8, 8,
        12, 12
      ],
      'circle-color': getOperatorColor(operator),
      'circle-stroke-width': 2,
      'circle-stroke-color': '#ffffff',
      'circle-opacity': 0.8
    };
  } else if (type.includes('pole') || type.includes('tower')) {
    baseLayer.paint = {
      'circle-radius': [
        'interpolate', ['linear'], ['zoom'],
        10, 2,
        12, 4,
        14, 6
      ],
      'circle-color': getOperatorColor(operator, true),
      'circle-opacity': 0.7
    };
  }

  return baseLayer;
};

// Helper functions
export const getOperatorColor = (operator: 'EGAT' | 'MEA' | 'PEA', isLighter = false): string => {
  const colors = {
    EGAT: isLighter ? '#F87171' : '#EF4444',
    MEA: isLighter ? '#60A5FA' : '#3B82F6',
    PEA: isLighter ? '#34D399' : '#10B981'
  };
  return colors[operator];
};

export const getTypeIcon = (type: InfrastructureType): string => {
  const icons: Record<InfrastructureType, string> = {
    transmission_substation: 'substation',
    distribution_substation: 'substation',
    transmission_tower: 'tower',
    distribution_pole: 'pole',
    power_plant: 'plant',
    solar_farm: 'solar',
    battery_storage: 'battery',
    ev_charging_station: 'ev'
  };
  return icons[type] || 'marker';
};

export const getMinZoom = (type: InfrastructureType): number => {
  const zooms: Record<InfrastructureType, number> = {
    transmission_substation: 6,
    distribution_substation: 8,
    transmission_tower: 10,
    distribution_pole: 12,
    power_plant: 6,
    solar_farm: 8,
    battery_storage: 8,
    ev_charging_station: 10
  };
  return zooms[type] || 10;
};

// Filter expression for Mapbox
export const createFilterExpression = (
  operators: ('EGAT' | 'MEA' | 'PEA')[],
  types: InfrastructureType[]
): any[] => {
  const filter: any[] = ['all'];
  
  if (operators.length > 0) {
    filter.push(['in', 'operator', ...operators]);
  }
  
  if (types.length > 0) {
    filter.push(['in', 'type', ...types]);
  }
  
  return filter;
};
