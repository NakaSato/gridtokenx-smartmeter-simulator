"use client";

/**
 * EGAT Transmission Map
 *
 * Mapbox-based visualization of EGAT's 500/230/115 kV transmission network.
 * Uses data from the /api/v1/grid/map endpoint.
 */

import { useRef, useEffect, useMemo, useState } from 'react';
import Map, {
  Source,
  Layer,
  Popup,
  NavigationControl,
  GeolocateControl,
  type MapRef,
} from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MAPBOX_TOKEN } from '@/lib/mapbox';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { useEgatTransmissionData } from './useEgatTransmissionData';
import { useMapStyle } from '@/hooks/useMapStyle';
import { Zap, RefreshCw, Filter, Loader2, Globe, Moon, Satellite } from 'lucide-react';

const REGIONS = ['All', 'North', 'Central', 'Northeast', 'East', 'South'];

const VOLTAGE_COLORS: Record<number, string> = {
  500: '#dc2626',
  230: '#f59e0b',
  115: '#3b82f6',
  69: '#8b5cf6',
};

const VOLTAGE_LABELS: Record<number, string> = {
  500: '500 kV',
  230: '230 kV',
  115: '115 kV',
  69: '69 kV',
};

export function EgatTransmissionMap() {
  const { getApiUrl } = useNetwork();
  const mapRef = useRef<any>(null);
  const [selectedSub, setSelectedSub] = useState<any>(null);
  const [region, setRegion] = useState<string>('All');
  const [voltageFilter, setVoltageFilter] = useState<number[]>([500, 230, 115]);
  const [showFilters, setShowFilters] = useState(false);
  const { mapStyle, toggle, isSatellite } = useMapStyle();

  const { data, loading, error, lastRefresh, refresh } = useEgatTransmissionData(
    getApiUrl,
    region === 'All' ? undefined : region,
  );

  // Build GeoJSON from data
  const substationGeoJSON = useMemo(() => {
    if (!data) return null;
    return {
      type: 'FeatureCollection' as const,
      features: data.substations
        .filter(s => voltageFilter.includes(s.voltage_kv))
        .map(s => ({
          type: 'Feature' as const,
          geometry: {
            type: 'Point' as const,
            coordinates: [s.longitude, s.latitude] as [number, number],
          },
          properties: s,
        })),
    };
  }, [data, voltageFilter]);

  const lineGeoJSON = useMemo(() => {
    if (!data) return null;
    return {
      type: 'FeatureCollection' as const,
      features: data.lines
        .filter(l => voltageFilter.includes(l.voltage_kv))
        .map(l => ({
          type: 'Feature' as const,
          geometry: {
            type: 'LineString' as const,
            coordinates: [
              [
                data.substations.find(s => s.id === l.from)?.longitude || 0,
                data.substations.find(s => s.id === l.from)?.latitude || 0,
              ],
              [
                data.substations.find(s => s.id === l.to)?.longitude || 0,
                data.substations.find(s => s.id === l.to)?.latitude || 0,
              ],
            ],
          },
          properties: l,
        }))
        .filter(f => f.geometry.coordinates[0][0] !== 0 && f.geometry.coordinates[1][0] !== 0),
    };
  }, [data, voltageFilter]);

  const toggleVoltage = (kv: number) => {
    setVoltageFilter(prev =>
      prev.includes(kv) ? prev.filter(v => v !== kv) : [...prev, kv],
    );
  };

  return (
    <div className="h-full w-full relative">
      {/* Loading / Error overlay */}
      {loading && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-950/60">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
        </div>
      )}

      {error && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-50 bg-red-900/90 text-red-200 px-4 py-2 rounded-lg text-sm">
          {error}
          <button onClick={refresh} className="ml-2 underline">Retry</button>
        </div>
      )}

      {/* Filter Panel */}
      <div className="absolute top-4 left-4 z-40 flex flex-col gap-2">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-3 py-2 bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-lg text-xs font-medium text-slate-300 hover:text-white"
        >
          <Filter className="w-3.5 h-3.5" />
          Filters
        </button>

        {showFilters && (
          <div className="bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-xl p-3 shadow-2xl min-w-[220px]">
            {/* Region filter */}
            <div className="mb-3">
              <label className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-1 block">
                Region
              </label>
              <select
                value={region}
                onChange={e => setRegion(e.target.value)}
                className="w-full bg-slate-800 border border-white/10 rounded px-2 py-1 text-xs text-slate-200"
              >
                {REGIONS.map(r => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>

            {/* Voltage filter */}
            <div>
              <label className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-1 block">
                Voltage Level
              </label>
              <div className="flex flex-col gap-1">
                {[500, 230, 115].map(kv => (
                  <button
                    key={kv}
                    onClick={() => toggleVoltage(kv)}
                    className="flex items-center gap-2 px-2 py-1 rounded text-xs font-medium transition-colors"
                    style={{
                      backgroundColor: voltageFilter.includes(kv) ? `${VOLTAGE_COLORS[kv]}22` : 'transparent',
                      color: voltageFilter.includes(kv) ? VOLTAGE_COLORS[kv] : '#64748b',
                    }}
                  >
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: VOLTAGE_COLORS[kv] }}
                    />
                    {VOLTAGE_LABELS[kv]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Stats Panel */}
      {data && (
        <div className="absolute bottom-4 left-4 z-40 bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-xl p-3 shadow-2xl min-w-[200px]">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-xs font-bold text-slate-200">EGAT Transmission</span>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]">
            <span className="text-slate-500">Substations</span>
            <span className="text-slate-200 text-right font-mono">{data.stats.total_substations}</span>
            <span className="text-slate-500">500 kV</span>
            <span className="text-red-400 text-right font-mono">{data.stats.substations_500kv}</span>
            <span className="text-slate-500">230 kV</span>
            <span className="text-amber-400 text-right font-mono">{data.stats.substations_230kv}</span>
            <span className="text-slate-500">115 kV</span>
            <span className="text-blue-400 text-right font-mono">{data.stats.substations_115kv}</span>
            <span className="text-slate-500">Lines</span>
            <span className="text-slate-200 text-right font-mono">{data.stats.total_transmission_lines}</span>
            <span className="text-slate-500">Total km</span>
            <span className="text-slate-200 text-right font-mono">{Math.round(data.stats.total_line_length_km).toLocaleString()}</span>
          </div>
        </div>
      )}

      {/* Refresh button */}
      <div className="absolute bottom-4 right-4 z-40">
        <button
          onClick={refresh}
          className="p-2 bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-lg text-slate-400 hover:text-white transition-colors"
          title="Refresh data"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
        {lastRefresh && (
          <div className="text-[9px] text-slate-600 text-right mt-1">
            {lastRefresh.toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* Map */}
      <div className="relative w-full h-full">
        <button
          onClick={toggle}
          className="absolute top-4 right-20 z-[1000] bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-400 hover:text-white transition-colors"
          title="Toggle satellite view"
        >
          <Globe className="w-3.5 h-3.5 inline mr-1" /> {isSatellite ? <Satellite className="w-3.5 h-3.5 inline" /> : <Moon className="w-3.5 h-3.5 inline" />}
        </button>
        <Map
        ref={mapRef}
        mapboxAccessToken={MAPBOX_TOKEN}
        initialViewState={{
          longitude: 100.5,
          latitude: 13.75,
          zoom: 6,
        }}
        style={{ width: '100%', height: '100%' }}
        mapStyle={mapStyle}
      >
        <NavigationControl position="top-right" />
        <GeolocateControl position="top-right" />

        {/* Transmission lines */}
        {lineGeoJSON && (
          <Source id="egat_lines" type="geojson" data={lineGeoJSON as any}>
            <Layer
              id="egat_lines_layer"
              type="line"
              paint={{
                'line-color': ['get', 'line_color'],
                'line-width': ['get', 'line_weight'],
                'line-opacity': 0.8,
              }}
              layout={{
                'line-cap': 'round',
                'line-join': 'round',
              }}
            />
            {/* Glow effect */}
            <Layer
              id="egat_lines_glow"
              type="line"
              paint={{
                'line-color': ['get', 'line_color'],
                'line-width': ['+', ['get', 'line_weight'], 4],
                'line-opacity': 0.15,
                'line-blur': 4,
              }}
            />
          </Source>
        )}

        {/* Substations */}
        {substationGeoJSON && (
          <Source id="egat_subs" type="geojson" data={substationGeoJSON as any}>
            {/* Glow layer */}
            <Layer
              id="egat_sub_glow"
              type="circle"
              paint={{
                'circle-radius': ['+', ['get', 'marker_size'], 6],
                'circle-color': ['get', 'marker_color'],
                'circle-opacity': 0.15,
                'circle-blur': 1,
              }}
            />
            {/* Main marker */}
            <Layer
              id="egat_sub_markers"
              type="circle"
              paint={{
                'circle-radius': ['get', 'marker_size'],
                'circle-color': ['get', 'marker_color'],
                'circle-stroke-width': 2,
                'circle-stroke-color': '#ffffff',
                'circle-opacity': 0.9,
              }}
              onClick={(e: any) => {
                if (e.features && e.features.length > 0) {
                  setSelectedSub(e.features[0].properties);
                }
              }}
            />
            {/* Labels */}
            <Layer
              id="egat_sub_labels"
              type="symbol"
              layout={{
                'text-field': ['get', 'name'],
                'text-size': 9,
                'text-offset': [0, 1.8],
                'text-anchor': 'top',
                'text-allow-overlap': false,
                'text-ignore-placement': false,
              }}
              paint={{
                'text-color': '#e2e8f0',
                'text-halo-color': '#0f172a',
                'text-halo-width': 1.5,
              }}
            />
          </Source>
        )}
      </Map>
      </div>

      {/* Substation Popup */}
      {selectedSub && (
        <div
          className="absolute z-50 bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-xl p-4 shadow-2xl text-xs max-w-[280px]"
          style={{
            top: '20%',
            left: '50%',
            transform: 'translateX(-50%)',
          }}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: selectedSub.marker_color }}
              />
              <span className="font-bold text-slate-100">{selectedSub.name}</span>
            </div>
            <button
              onClick={() => setSelectedSub(null)}
              className="text-slate-500 hover:text-white"
            >
              ✕
            </button>
          </div>
          <div className="text-slate-400 mb-1">{selectedSub.name_th}</div>
          <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[10px]">
            <span className="text-slate-500">Voltage</span>
            <span className="text-slate-200 text-right font-mono">{selectedSub.voltage_kv} kV</span>
            <span className="text-slate-500">Capacity</span>
            <span className="text-slate-200 text-right font-mono">{selectedSub.capacity_mva} MVA</span>
            <span className="text-slate-500">Type</span>
            <span className="text-slate-200 text-right">{selectedSub.type}</span>
            <span className="text-slate-500">Province</span>
            <span className="text-slate-200 text-right">{selectedSub.province}</span>
            <span className="text-slate-500">Region</span>
            <span className="text-slate-200 text-right">{selectedSub.region}</span>
          </div>
        </div>
      )}
    </div>
  );
}
