/**
 * Electrical Grid Map Layers
 *
 * Mapbox GL layers for visualizing electrical infrastructure
 */

import type mapboxgl from 'mapbox-gl';
type LineLayer = any;
type CircleLayer = any;

export const getSubstationCircleLayer = (operator: 'EGAT' | 'MEA' | 'PEA'): CircleLayer => ({
  id: `${operator.toLowerCase()}-substations`,
  type: 'circle',
  paint: {
    'circle-radius': [
      'interpolate', ['linear'], ['zoom'],
      6, 4, 8, 8, 12, 12, 16, 20
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
      10, 2, 12, 4, 14, 6, 18, 10
    ],
    'circle-color': operator === 'EGAT' ? '#F59E0B' : operator === 'MEA' ? '#60A5FA' : '#34D399',
    'circle-stroke-width': 1,
    'circle-stroke-color': '#ffffff',
    'circle-opacity': 0.7
  }
});

export const getSubstationGlowLayer = (operator: 'EGAT' | 'MEA' | 'PEA'): CircleLayer => ({
  id: `${operator.toLowerCase()}-substations-glow`,
  type: 'circle',
  paint: {
    'circle-radius': [
      'interpolate', ['linear'], ['zoom'],
      6, 8, 8, 16, 12, 24, 16, 40
    ],
    'circle-color': operator === 'EGAT' ? '#EF4444' : operator === 'MEA' ? '#3B82F6' : '#10B981',
    'circle-opacity': [
      'interpolate', ['linear'], ['zoom'],
      6, 0.1, 10, 0.2, 14, 0.3
    ],
    'circle-blur': 0.5
  }
});

// Voltage-based coloring
export const getVoltageColor = (voltageKv: number): string => {
  if (voltageKv >= 500) return '#DC2626';
  if (voltageKv >= 230) return '#EA580C';
  if (voltageKv >= 115) return '#CA8A04';
  if (voltageKv >= 22) return '#16A34A';
  return '#6B7280';
};
