"use client";

/**
 * OSM Real Power Grid Map
 *
 * Displays real power grid topology from OpenStreetMap using react-map-gl.
 * Shows substations, transmission lines, and grid status from
 * GET /api/v1/grid/osm with ETag-based HTTP caching.
 */

import { useRef, useMemo, useState, useEffect } from 'react';
import { usePersistedViewState } from '@/hooks/usePersistedViewState';
import Map, {
  Source,
  Layer,
  Popup,
  NavigationControl,
  type MapRef,
  type MapLayerMouseEvent,
} from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MAPBOX_TOKEN } from '@/lib/mapbox';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { useOsmGridData, type OsmSubstation } from './useOsmGridData';
import { useMapStyle } from '@/hooks/useMapStyle';
import {
  Zap,
  RefreshCw,
  Loader2,
  MapPin,
  CircuitBoard,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';

const VOLTAGE_COLORS: Record<number, string> = {
  500: '#dc2626',
  230: '#f59e0b',
  115: '#3b82f6',
  69: '#8b5cf6',
  22: '#10b981',
  11: '#06b6d4',
};

function getVoltageColor(kv: number): string {
  return VOLTAGE_COLORS[kv] || '#6b7280';
}

export function OsmGridMap() {
  const { getApiUrl } = useNetwork();
  const mapRef = useRef<MapRef>(null);
  const [selectedSub, setSelectedSub] = useState<OsmSubstation | null>(null);
  const { mapStyle, toggle, isSatellite } = useMapStyle();
  const [viewState, setViewState] = usePersistedViewState('osm-grid', {
    longitude: 101.85,
    latitude: 14.1,
    zoom: 8,
  });

  const { data, loading, error, lastRefresh, refresh } = useOsmGridData(getApiUrl, 'korat');

  // Compute map bounds from data
  const bounds = useMemo(() => {
    if (!data) return null;
    const allCoords = [
      ...data.substations.map(s => s.coordinates),
      ...data.lines.flatMap(l => l.coordinates),
    ];
    if (allCoords.length === 0) return null;

    const lons = allCoords.map(c => c?.[0] || 100.0);
    const lats = allCoords.map(c => c?.[1] || 13.0);
    return {
      west: Math.min(...lons) - 0.1,
      south: Math.min(...lats) - 0.1,
      east: Math.max(...lons) + 0.1,
      north: Math.max(...lats) + 0.1,
    };
  }, [data]);

  // GeoJSON for substations
  const substationGeoJSON = useMemo(() => {
    if (!data) return null;
    return {
      type: 'FeatureCollection' as const,
      features: data.substations.map(s => ({
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: s.coordinates },
        properties: s,
      })),
    };
  }, [data]);

  // GeoJSON for power lines
  const lineGeoJSON = useMemo(() => {
    if (!data) return null;
    return {
      type: 'FeatureCollection' as const,
      features: data.lines.map(l => ({
        type: 'Feature' as const,
        geometry: { type: 'LineString' as const, coordinates: l.coordinates },
        properties: l,
      })),
    };
  }, [data]);

  // Fit bounds on first load
  const hasFittedBounds = useRef(false);
  useEffect(() => {
    if (bounds && mapRef.current && !hasFittedBounds.current) {
      mapRef.current.fitBounds(
        [[bounds.west, bounds.south], [bounds.east, bounds.north]],
        { padding: 60, duration: 1000 },
      );
      hasFittedBounds.current = true;
    }
  }, [bounds]);

  return (
    <div className="relative w-full h-full bg-gray-950">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-black/80 to-transparent p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" />
            <h2 className="text-white font-bold text-lg">OSM Power Grid</h2>
            <span className="text-gray-400 text-sm">Nakhon Ratchasima</span>
          </div>
          <div className="flex items-center gap-2">
            {lastRefresh && (
              <span className="text-gray-500 text-xs">
                Updated {lastRefresh.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={refresh}
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

      {/* Loading / Error overlay */}
      {loading && !data && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-black/60">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-amber-400" />
            <span className="text-white text-sm">Loading OSM grid data…</span>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-20 bg-red-900/90 text-white px-4 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Summary panel */}
      {data && (
        <div className="absolute bottom-4 left-4 z-10 bg-black/80 backdrop-blur-sm rounded-lg p-3 text-white text-xs space-y-1.5 min-w-[180px]">
          <h3 className="font-bold text-amber-400 text-sm mb-2">Grid Summary</h3>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            <span className="text-gray-400">Buses</span>
            <span className="text-right font-mono">{data.summary.buses}</span>
            <span className="text-gray-400">Lines</span>
            <span className="text-right font-mono">{data.summary.lines}</span>
            <span className="text-gray-400">Loads</span>
            <span className="text-right font-mono">{data.summary.loads}</span>
            <span className="text-gray-400">Total Load</span>
            <span className="text-right font-mono">{data.summary.total_load_mw.toFixed(1)} MW</span>
            <span className="text-gray-400">Losses</span>
            <span className="text-right font-mono">{data.summary.total_loss_mw.toFixed(3)} MW</span>
          </div>

          {/* Bus status */}
          <div className="mt-2 pt-2 border-t border-white/10">
            <span className="text-gray-400 text-xs">Bus Status</span>
            {data.bus_status.map(bus => (
              <div key={bus.bus_idx} className="flex items-center gap-1.5 mt-1">
                {bus.status === 'ok' ? (
                  <CheckCircle2 className="w-3 h-3 text-green-400" />
                ) : (
                  <AlertTriangle className="w-3 h-3 text-red-400" />
                )}
                <span className="truncate flex-1">{bus.name.split('(')[0].trim()}</span>
                <span className="font-mono text-amber-300">{bus.vm_pu.toFixed(3)} pu</span>
              </div>
            ))}
          </div>

          {/* Featured line info */}
          {data.featured_line && (
            <div className="mt-2 pt-2 border-t border-white/10 text-gray-400">
              <div className="text-xs text-gray-500">Featured OSM Line</div>
              <div className="text-white text-xs mt-0.5">{data.featured_line.name}</div>
              <div className="text-gray-400">
                {data.featured_line.voltage / 1000}kV · {data.featured_line.operator}
              </div>
            </div>
          )}

          <div className="mt-2 pt-2 border-t border-white/10 text-gray-500 text-[10px]">
            ETag: {data.etag}
          </div>
        </div>
      )}

      {/* Legend */}
      {data && data.substations.length > 0 && (
        <div className="absolute bottom-4 right-4 z-10 bg-black/80 backdrop-blur-sm rounded-lg p-3 text-white text-xs">
          <h3 className="font-bold text-gray-400 text-xs mb-2">Voltage Legend</h3>
          <div className="space-y-1">
            {Object.entries(VOLTAGE_COLORS)
              .filter(([kv]) =>
                data.substations.some(s => s.voltage_kv === Number(kv)) ||
                data.lines.some(l => l.voltage_kv === Number(kv)),
              )
              .map(([kv, color]) => (
                <div key={kv} className="flex items-center gap-2">
                  <div className="w-4 h-1.5 rounded" style={{ backgroundColor: color }} />
                  <span className="text-gray-300">{kv} kV</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Map */}
      <Map
        ref={mapRef}
        mapboxAccessToken={MAPBOX_TOKEN}
        {...viewState}
        onMove={evt => setViewState(evt.viewState)}
        mapStyle={mapStyle}
        style={{ width: '100%', height: '100%' }}
      >
        <NavigationControl position="top-right" />

        {/* Power lines */}
        {lineGeoJSON && (
          <Source id="osm-lines" type="geojson" data={lineGeoJSON}>
            <Layer
              id="osm-lines-layer"
              type="line"
              paint={{
                'line-color': [
                  'match',
                  ['get', 'voltage_kv'],
                  500, '#dc2626',
                  230, '#f59e0b',
                  115, '#3b82f6',
                  '#6b7280',
                ],
                'line-width': 2,
                'line-opacity': 0.8,
              }}
            />
          </Source>
        )}

        {/* Substations */}
        {substationGeoJSON && (
          <Source id="osm-subs" type="geojson" data={substationGeoJSON}>
            <Layer
              id="osm-subs-circles"
              type="circle"
              paint={{
                'circle-radius': ['interpolate', ['linear'], ['get', 'voltage_kv'], 0, 6, 500, 16],
                'circle-color': [
                  'match',
                  ['get', 'voltage_kv'],
                  500, '#dc2626',
                  230, '#f59e0b',
                  115, '#3b82f6',
                  '#6b7280',
                ],
                'circle-stroke-color': '#000',
                'circle-stroke-width': 2,
                'circle-opacity': 0.9,
              }}
              onClick={(e: any) => {
                if (e.features?.[0]) {
                  setSelectedSub(e.features[0].properties as unknown as OsmSubstation);
                }
              }}
            />
            <Layer
              id="osm-subs-labels"
              type="symbol"
              layout={{
                'text-field': ['get', 'name'],
                'text-size': 10,
                'text-offset': [0, 1.8],
                'text-anchor': 'top',
              }}
              paint={{
                'text-color': '#fff',
                'text-halo-color': '#000',
                'text-halo-width': 1,
              }}
            />
          </Source>
        )}
      </Map>

      {/* Substation popup */}
      {selectedSub && selectedSub.coordinates && (
        <Popup
          longitude={selectedSub.coordinates[0]}
          latitude={selectedSub.coordinates[1]}
          onClose={() => setSelectedSub(null)}
          closeButton={false}
          maxWidth="280px"
        >
          <div className="p-1">
            <h3 className="font-bold text-sm">{selectedSub.name}</h3>
            <div className="mt-2 space-y-1 text-xs text-gray-600">
              <div>OSM ID: {selectedSub.osm_id}</div>
              <div>
                Voltage:{' '}
                <span
                  className="font-mono font-bold"
                  style={{ color: getVoltageColor(selectedSub.voltage_kv) }}
                >
                  {selectedSub.voltage_kv} kV
                </span>
              </div>
              <div>Category: {selectedSub.category}</div>
              <div>
                Coordinates: {(selectedSub.coordinates?.[1] ?? 0).toFixed(4)},{' '}
                {(selectedSub.coordinates?.[0] ?? 0).toFixed(4)}
              </div>
            </div>
          </div>
        </Popup>
      )}
    </div>
  );
}
