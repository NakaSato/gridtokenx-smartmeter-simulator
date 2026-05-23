"use client";

/**
 * Electrical Grid Map Component
 * 
 * Interactive map showing Thai electrical infrastructure (EGAT, MEA, PEA)
 */

import { useState, useCallback, useRef } from 'react';
import { usePersistedViewState } from '@/hooks/usePersistedViewState';
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
  ViewStateChangeEvent
} from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Zap, Globe, Moon, Satellite, RefreshCw, Loader2, CircuitBoard, MapPin } from 'lucide-react';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { useMapStyle } from '@/hooks/useMapStyle';
import type {
  ElectricalInfrastructure,
  ElectricalGridFeatureCollection,
  FilterState
} from './types';
import {
  DEFAULT_FILTERS
} from './types';
import {
  getSubstationCircleLayer,
  getPoleCircleLayer,
  getSubstationGlowLayer
} from './mapLayers';
import { FilterPanel } from './FilterPanel';
import { InfrastructurePopup } from './InfrastructurePopup';
import { MapLegend } from './MapLegend';
import { useElectricalGridData } from './useElectricalGridData';

const ElectricalGridMap = () => {
  const { getApiUrl } = useNetwork();
  
  // State
  const [viewState, setViewState] = usePersistedViewState('electrical-grid', {
    longitude: 99.99007762999207,
    latitude: 9.528326082141575,
    zoom: 6
  });
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [popupInfo, setPopupInfo] = useState<{
    longitude: number;
    latitude: number;
    feature: ElectricalInfrastructure;
  } | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [showLegend, setShowLegend] = useState(true);
  const { mapStyle, toggle, isSatellite } = useMapStyle();

  // Data fetching
  const { infrastructure, stats, loading, lastRefresh, refresh: refreshData } = useElectricalGridData(getApiUrl);
  
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
  function searchMatch(item: ElectricalInfrastructure, query: string): boolean {
    const searchStr = query.toLowerCase();
    return Boolean(
      item.name_en?.toLowerCase().includes(searchStr) ||
      item.name_th?.toLowerCase().includes(searchStr) ||
      item.id.toLowerCase().includes(searchStr) ||
      item.province?.toLowerCase().includes(searchStr) ||
      item.district?.toLowerCase().includes(searchStr)
    );
  }

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
  }, [setViewState]);

  // Update filters
  const updateFilters = useCallback((updates: Partial<FilterState>) => {
    setFilters(prev => ({ ...prev, ...updates }));
  }, []);

  // Reset filters
  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
  }, []);

  // Loading state
  if (loading) {
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

  return (
    <div className="h-screen w-screen relative bg-gray-900">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-[1000] bg-gradient-to-b from-black/80 to-transparent p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" />
            <h2 className="text-white font-bold text-lg">Grid Infrastructure</h2>
            <span className="text-gray-400 text-sm">EGAT / MEA / PEA</span>
          </div>
          <div className="flex items-center gap-2">
            {lastRefresh && (
              <span className="text-gray-500 text-xs">
                Updated {lastRefresh.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={refreshData}
              disabled={loading}
              className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white disabled:opacity-50 transition"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            </button>
            <button
              onClick={toggle}
              className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white transition"
            >
              {isSatellite ? <MapPin className="w-4 h-4" /> : <CircuitBoard className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="absolute top-16 right-4 sm:top-20 sm:right-6 z-[1000] w-80 max-h-[80vh] overflow-y-auto">
          <FilterPanel
            filters={filters}
            onUpdateFilters={updateFilters}
            onResetFilters={resetFilters}
            onClose={() => setShowFilters(false)}
            stats={stats}
          />
        </div>
      )}

      {/* Legend */}
      {showLegend && (
        <MapLegend
          visible={showLegend}
          onClose={() => setShowLegend(false)}
        />
      )}

      {/* Map */}
      <div className="relative w-full h-full">
        <button
          onClick={toggle}
          className="absolute top-16 right-4 z-[1000] bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-400 hover:text-white transition-colors"
          title="Toggle satellite view"
        >
          <Globe className="w-3.5 h-3.5 inline mr-1" /> {isSatellite ? <Satellite className="w-3.5 h-3.5 inline" /> : <Moon className="w-3.5 h-3.5 inline" />}
        </button>
        <Map
        ref={mapRef}
        {...viewState}
        onMove={handleViewStateChange}
        onClick={handleMapClick}
        style={{ width: '100%', height: '100%' }}
        mapStyle={mapStyle}
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
        <NavigationControl position="top-right" />
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
            closeButton={true}
            onCloseClick={() => setPopupInfo(null)}
            closeOnClick={false}
            className="electrical-grid-popup"
          >
            <InfrastructurePopup
              infrastructure={popupInfo.feature}
            />
          </Popup>
        )}
      </Map>
      </div>

      {/* Stats Bar */}
      <div className="absolute bottom-4 left-4 bg-gray-800/90 backdrop-blur-sm rounded-lg px-3 py-2 flex items-center gap-3 text-white z-[1000]">
        <div>
          <div className="text-[10px] text-gray-400 font-medium">Total</div>
          <div className="text-sm font-bold">{stats.totalInfrastructure}</div>
        </div>
        <span className="text-gray-700">·</span>
        <div>
          <div className="text-[10px] text-gray-400 font-medium">Filtered</div>
          <div className="text-sm font-bold text-yellow-400">{filteredInfrastructure.length}</div>
        </div>
        <span className="text-gray-700">·</span>
        <div className="flex items-center gap-2">
          <div className="flex items-center">
            <div className="w-2 h-2 rounded-full bg-red-500 mr-1" />
            <span className="text-[10px]">EGAT: {stats.byOperator.EGAT}</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 rounded-full bg-blue-500 mr-1" />
            <span className="text-[10px]">MEA: {stats.byOperator.MEA}</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 rounded-full bg-green-500 mr-1" />
            <span className="text-[10px]">PEA: {stats.byOperator.PEA}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ElectricalGridMap;
