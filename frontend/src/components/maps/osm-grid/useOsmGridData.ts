/**
 * OSM Real Power Grid Data Hook
 *
 * Fetches real power grid topology from OpenStreetMap via
 * GET /api/v1/grid/osm with HTTP ETag caching.
 *
 * First request: full response (200 + ETag)
 * Subsequent requests with matching ETag: 304 Not Modified (0 bytes)
 *
 * Usage:
 *   const { data, loading, error, refresh } = useOsmGridData(getApiUrl, 'korat');
 *   // data.geojson → FeatureCollection for map rendering
 *   // data.summary → { buses, lines, loads, total_load_mw }
 *   // data.bus_status → voltage status per bus
 */

import { useState, useEffect, useRef, useCallback } from 'react';

export interface OsmSubstation {
  osm_id: string;
  name: string;
  type: 'substation';
  voltage_kv: number;
  category: string;
  coordinates: [number, number]; // [lon, lat]
}

export interface OsmPowerLine {
  name: string;
  type: 'power_line';
  length_km: number;
  voltage_kv: number;
  cable_type: string;
  coordinates: [number, number][]; // [[lon, lat], ...]
}

export interface OsmBusStatus {
  bus_idx: number;
  name: string;
  voltage_kv: number;
  vm_pu: number;
  va_degree: number;
  status: 'ok' | 'alert';
}

export interface OsmGridSummary {
  buses: number;
  lines: number;
  loads: number;
  external_grids: number;
  total_load_mw: number;
  total_loss_mw: number;
}

export interface OsmFeaturedLine {
  osm_id: number;
  name: string;
  voltage: number;
  operator: string;
  num_points: number;
  bounds: { north: number; south: number; east: number; west: number };
  coordinates?: [number, number][]; // Only present if include_way=true
}

export interface OsmGridData {
  source: string;
  area: string;
  summary: OsmGridSummary;
  bus_status: OsmBusStatus[];
  substations: OsmSubstation[];
  lines: OsmPowerLine[];
  featured_line: OsmFeaturedLine | null;
  etag: string;
}

export function useOsmGridData(
  getApiUrl: (path: string) => string,
  area: string = 'korat',
  autoRefresh: boolean = true,
) {
  const [data, setData] = useState<OsmGridData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  // ETag for conditional requests
  const etagRef = useRef<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const url = `/api/v1/grid/osm?area=${encodeURIComponent(area)}`;
      const headers: Record<string, string> = {};

      // Send ETag if we have one (conditional request)
      if (etagRef.current) {
        headers['If-None-Match'] = etagRef.current;
      }

      const response = await fetch(getApiUrl(url), { headers });

      // 304 Not Modified — data unchanged, use cached
      if (response.status === 304) {
        setLastRefresh(new Date());
        return; // Keep existing data
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const json = await response.json();

      // Store ETag for next request
      const newEtag = response.headers.get('etag') || '';
      etagRef.current = newEtag.replace(/^"|"$/g, ''); // Strip quotes

      // Parse GeoJSON features into typed objects
      const substations: OsmSubstation[] = [];
      const lines: OsmPowerLine[] = [];

      for (const feature of json.geojson?.features || []) {
        const props = feature.properties;
        const geom = feature.geometry;

        if (props.type === 'substation' && geom.type === 'Point') {
          substations.push({
            osm_id: props.osm_id,
            name: props.name,
            type: 'substation',
            voltage_kv: props.voltage_kv,
            category: props.category,
            coordinates: geom.coordinates,
          });
        } else if (props.type === 'power_line' && geom.type === 'LineString') {
          lines.push({
            name: props.name,
            type: 'power_line',
            length_km: props.length_km,
            voltage_kv: props.voltage_kv,
            cable_type: props.cable_type,
            coordinates: geom.coordinates,
          });
        }
      }

      setData({
        source: json.source,
        area: json.area,
        summary: json.summary,
        bus_status: json.bus_status || [],
        substations,
        lines,
        featured_line: json.featured_line || null,
        etag: etagRef.current,
      });

      setLastRefresh(new Date());
    } catch (err) {
      console.error('Error fetching OSM grid data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load OSM grid data');
    } finally {
      setLoading(false);
    }
  }, [getApiUrl, area]);

  useEffect(() => {
    if (autoRefresh) {
      fetchData();
    }
  }, [fetchData, autoRefresh]);

  return { data, loading, error, lastRefresh, refresh: fetchData };
}
