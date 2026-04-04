/**
 * Electrical Grid Map Component
 * 
 * Interactive map showing Thai electrical infrastructure (EGAT, MEA, PEA)
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import Map, {
  Source,
  Layer,
  NavigationControl,
  ScaleControl,
  GeolocateControl,
  FullscreenControl,
  Popup
} from 'react-map-gl';
import type {
  ViewStateChangeEvent,
  CircleLayer,
  GeoJSONSource
} from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Zap, Filter, Search, Layers, Info } from 'lucide-react';
import { useNetwork } from '../../context/NetworkContext';
import type {
  ElectricalInfrastructure,
  ElectricalGridFeatureCollection,
  FilterState,
  InfrastructureType
} from './types';
import {
  DEFAULT_FILTERS,
  INFRASTRUCTURE_LAYERS,
  OPERATOR_INFO,
  getSubstationCircleLayer,
  getPoleCircleLayer,
  getSubstationGlowLayer
} from './mapLayers';
import { MapHeader } from './MapHeader';
import { FilterPanel } from './FilterPanel';
import { InfrastructurePopup } from './InfrastructurePopup';
import { MapLegend } from './MapLegend';
import { useElectricalGridData } from './useElectricalGridData';

// Mapbox token (use environment variable or default)
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';

const ElectricalGridMap = () => {
  const { getApiUrl } = useNetwork();
  
  // State
  const [viewState, setViewState] = useState({
    longitude: 100.5,  // Thailand center
    latitude: 13.75,   // Bangkok area
    zoom: 6
  });
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [selectedInfrastructure, setSelectedInfrastructure] = useState<ElectricalInfrastructure | null>(null);
  const [popupInfo, setPopupInfo] = useState<{
    longitude: number;
    latitude: number;
    feature: ElectricalInfrastructure;
  } | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [showLegend, setShowLegend] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data fetching
  const { infrastructure, stats, loading: dataLoading } = useElectricalGridData(getApiUrl);
  
  // Refs
  const mapRef = useRef<any>(null);

  // Filter infrastructure based on current filters
  const filteredInfrastructure = infrastructure.filter(item => {
    if (!filters.operators.includes(item.operator)) return false;
    if (!filters.types.includes(item.type)) return false;
    if (filters.voltageLevels.length > 0 && item.voltage_kv && !filters.voltageLevels.includes(item.voltage_kv)) return false;
    if (filters.provinces.length > 0 && item.province && !filters.provinces.includes(item.province)) return false;
    if (filters.searchQuery && !searchMatch(item, filters.searchQuery)) return false;
    return true;
  });

  // Convert to GeoJSON
  const geoJsonData: ElectricalGridFeatureCollection = {
    type: 'FeatureCollection',
    features: filteredInfrastructure.map(item => ({
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [item.longitude, item.latitude]
      },
      properties: item
    }))
  };

  // Search match helper
  const searchMatch = (item: ElectricalInfrastructure, query: string): boolean => {
    const searchStr = query.toLowerCase();
    return (
      item.name_en?.toLowerCase().includes(searchStr) ||
      item.name_th?.toLowerCase().includes(searchStr) ||
      item.id.toLowerCase().includes(searchStr) ||
      item.province?.toLowerCase().includes(searchStr) ||
      item.district?.toLowerCase().includes(searchStr)
    );
  };

  // Handle map click
  const handleMapClick = useCallback((event: any) => {
    const features = event.features;
    if (features && features.length > 0) {
      const feature = features[0].properties as ElectricalInfrastructure;
      setPopupInfo({
        longitude: event.lngLat.lng,
        latitude: event.lngLat.lat,
        feature
      });
    } else {
      setPopupInfo(null);
    }
  }, []);

  // Handle view change
  const handleViewStateChange = useCallback((event: ViewStateChangeEvent) => {
    setViewState(event.viewState);
  }, []);

  // Toggle layer visibility
  const toggleLayer = useCallback((layerId: string) => {
    // Implementation for toggling individual layers
    console.log('Toggle layer:', layerId);
  }, []);

  // Update filters
  const updateFilters = useCallback((updates: Partial<FilterState>) => {
    setFilters(prev => ({ ...prev, ...updates }));
  }, []);

  // Reset filters
  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
  }, []);

  // Fit bounds to show all infrastructure
  const fitToInfrastructure = useCallback(() => {
    if (mapRef.current && filteredInfrastructure.length > 0) {
      const bounds = filteredInfrastructure.reduce(
        (acc, item) => {
          acc.west = Math.min(acc.west, item.longitude);
          acc.east = Math.max(acc.east, item.longitude);
          acc.south = Math.min(acc.south, item.latitude);
          acc.north = Math.max(acc.north, item.latitude);
          return acc;
        },
        { west: 180, east: -180, south: 90, north: -90 }
      );
      
      mapRef.current.fitBounds(
        [[bounds.west, bounds.south], [bounds.east, bounds.north]],
        { padding: 50, duration: 1000 }
      );
    }
  }, [filteredInfrastructure]);

  // Loading state
  if (dataLoading || loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <Zap className="w-16 h-16 text-yellow-400 mx-auto mb-4 animate-pulse" />
          <h2 className="text-2xl font-bold text-white mb-2">Loading Electrical Grid</h2>
          <p className="text-gray-400">Fetching infrastructure data from EGAT, MEA, and PEA...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-900">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-bold text-red-400 mb-4">Error Loading Map</h2>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-yellow-500 text-black rounded-lg hover:bg-yellow-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen relative bg-gray-900">
      {/* Header */}
      <MapHeader
        stats={stats}
        totalInfrastructure={infrastructure.length}
        filteredCount={filteredInfrastructure.length}
        onToggleFilters={() => setShowFilters(!showFilters)}
        onToggleLegend={() => setShowLegend(!showLegend)}
        onFitToBounds={fitToInfrastructure}
      />

      {/* Filter Panel */}
      {showFilters && (
        <FilterPanel
          filters={filters}
          onUpdateFilters={updateFilters}
          onResetFilters={resetFilters}
          onClose={() => setShowFilters(false)}
          stats={stats}
        />
      )}

      {/* Legend */}
      {showLegend && (
        <MapLegend
          layers={INFRASTRUCTURE_LAYERS}
          visible={showLegend}
          onClose={() => setShowLegend(false)}
        />
      )}

      {/* Map */}
      <Map
        ref={mapRef}
        {...viewState}
        onMove={handleViewStateChange}
        onClick={handleMapClick}
        style={{ width: '100%', height: '100%' }}
        mapStyle="mapbox://styles/mapbox/dark-v11"
        mapboxAccessToken={MAPBOX_TOKEN}
        projection={{ name: 'globe' }}
        interactiveLayerIds={[
          'egat-substations',
          'mea-substations',
          'pea-substations',
          'egat-poles',
          'mea-poles',
          'pea-poles'
        ]}
      >
        {/* Controls */}
        <NavigationControl position="top-right" showCompass={true} />
        <GeolocateControl position="top-right" />
        <FullscreenControl position="top-right" />
        <ScaleControl position="bottom-left" />

        {/* Infrastructure layers */}
        <Source id="electrical-infrastructure" type="geojson" data={geoJsonData}>
          {/* EGAT Substations */}
          <Layer {...getSubstationGlowLayer('EGAT')} />
          <Layer {...getSubstationCircleLayer('EGAT')} />
          
          {/* MEA Substations */}
          <Layer {...getSubstationGlowLayer('MEA')} />
          <Layer {...getSubstationCircleLayer('MEA')} />
          
          {/* PEA Substations */}
          <Layer {...getSubstationGlowLayer('PEA')} />
          <Layer {...getSubstationCircleLayer('PEA')} />
          
          {/* EGAT Poles/Towers */}
          <Layer {...getPoleCircleLayer('EGAT')} />
          
          {/* MEA Poles */}
          <Layer {...getPoleCircleLayer('MEA')} />
          
          {/* PEA Poles */}
          <Layer {...getPoleCircleLayer('PEA')} />
        </Source>

        {/* Popup */}
        {popupInfo && (
          <Popup
            longitude={popupInfo.longitude}
            latitude={popupInfo.latitude}
            anchor="bottom"
            onClose={() => setPopupInfo(null)}
            closeOnClick={false}
            className="electrical-grid-popup"
          >
            <InfrastructurePopup
              infrastructure={popupInfo.feature}
              onSelect={setSelectedInfrastructure}
            />
          </Popup>
        )}
      </Map>

      {/* Stats Bar */}
      <div className="absolute bottom-4 left-4 right-4 bg-gray-800 bg-opacity-90 rounded-lg p-4 flex items-center justify-between text-white">
        <div className="flex items-center space-x-6">
          <div>
            <div className="text-xs text-gray-400">Total Infrastructure</div>
            <div className="text-xl font-bold">{stats.totalInfrastructure}</div>
          </div>
          <div>
            <div className="text-xs text-gray-400">Filtered</div>
            <div className="text-xl font-bold text-yellow-400">{filteredInfrastructure.length}</div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-red-500 mr-2" />
              <span className="text-sm">EGAT: {stats.byOperator.EGAT}</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-blue-500 mr-2" />
              <span className="text-sm">MEA: {stats.byOperator.MEA}</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-green-500 mr-2" />
              <span className="text-sm">PEA: {stats.byOperator.PEA}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ElectricalGridMap;
