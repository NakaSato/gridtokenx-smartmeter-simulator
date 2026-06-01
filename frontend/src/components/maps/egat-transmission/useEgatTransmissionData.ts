/**
 * EGAT Transmission Grid Data Hook
 *
 * Fetches EGAT transmission network data from the /api/v1/grid/map endpoint
 * and returns GeoJSON features for map rendering
 */

import { useState, useEffect, useRef, useCallback } from 'react';

export interface EgatSubstation {
  id: string;
  name: string;
  name_th: string;
  voltage_kv: number;
  type: string;
  province: string;
  region: string;
  capacity_mva: number;
  latitude: number;
  longitude: number;
  marker_color: string;
  marker_size: number;
}

export interface EgatLine {
  id: string;
  from: string;
  to: string;
  voltage_kv: number;
  length_km: number;
  circuit: number;
  conductor: string;
  line_color: string;
  line_weight: number;
}

export interface EgatGridStats {
  total_substations: number;
  substations_500kv: number;
  substations_230kv: number;
  substations_115kv: number;
  total_transmission_lines: number;
  total_line_length_km: number;
  line_length_500kv_km: number;
  line_length_230kv_km: number;
  line_length_115kv_km: number;
  total_capacity_500kv_mva: number;
  total_capacity_230kv_mva: number;
  total_capacity_115kv_mva: number;
  regions_covered: string[];
  provinces_covered: string[];
}

export interface EgatMapData {
  substations: EgatSubstation[];
  lines: EgatLine[];
  stats: EgatGridStats;
}

export function useEgatTransmissionData(
  getApiUrl: (path: string) => string,
  region?: string,
) {
  const [data, setData] = useState<EgatMapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      let url = '/api/v1/grid/map?format=geojson&layers=egat';
      if (region) {
        url += `&region=${encodeURIComponent(region)}`;
      }

      const response = await fetch(getApiUrl(url));

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const geojson = await response.json();

      // Parse GeoJSON features into substations and lines
      const substations: EgatSubstation[] = [];
      const lines: EgatLine[] = [];

      for (const feature of geojson.features || []) {
        const props = feature.properties;
        const layer = props.layer;

        if (layer === 'egat_substation' && feature.geometry.type === 'Point') {
          substations.push({
            id: props.id,
            name: props.name,
            name_th: props.name_th,
            voltage_kv: props.voltage_kv,
            type: props.type,
            province: props.province,
            region: props.region,
            capacity_mva: props.capacity_mva,
            latitude: feature.geometry?.coordinates?.[1] || 0,
            longitude: feature.geometry?.coordinates?.[0] || 0,
            marker_color: props.marker_color,
            marker_size: props.marker_size,
          });
        } else if (layer === 'egat_line' && feature.geometry.type === 'LineString') {
          const coords = feature.geometry.coordinates;
          lines.push({
            id: props.id,
            from: props.from,
            to: props.to,
            voltage_kv: props.voltage_kv,
            length_km: props.length_km,
            circuit: props.circuit,
            conductor: props.conductor,
            line_color: props.line_color,
            line_weight: props.line_weight,
          });
        } else if (layer === 'egat_plant' && feature.geometry.type === 'Point') {
          // Add plants to substations for simplicity or handle separately
          // For now, let's just make sure they exist in the data
          substations.push({
            id: props.id,
            name: props.name,
            name_th: props.name_th || props.name,
            voltage_kv: 0, // Plants don't have a single voltage in this view
            type: 'power_plant',
            province: props.province || '',
            region: props.region || '',
            capacity_mva: props.capacity_mw || 0,
            latitude: feature.geometry?.coordinates?.[1] || 0,
            longitude: feature.geometry?.coordinates?.[0] || 0,
            marker_color: props.marker_color || '#10b981',
            marker_size: 8,
          });
        }
      }

      // Fetch statistics separately
      let stats: EgatGridStats | null = null;
      try {
        const statsRes = await fetch(getApiUrl('/api/v1/grid/egat/statistics'));
        if (statsRes.ok) {
          stats = await statsRes.json();
        }
      } catch {
        // Stats optional
      }

      if (!stats) {
        // Compute stats from data
        stats = {
          total_substations: substations.length,
          substations_500kv: substations.filter(s => s.voltage_kv === 500).length,
          substations_230kv: substations.filter(s => s.voltage_kv === 230).length,
          substations_115kv: substations.filter(s => s.voltage_kv === 115).length,
          total_transmission_lines: lines.length,
          total_line_length_km: lines.reduce((sum, l) => sum + l.length_km, 0),
          line_length_500kv_km: lines.filter(l => l.voltage_kv === 500).reduce((sum, l) => sum + l.length_km, 0),
          line_length_230kv_km: lines.filter(l => l.voltage_kv === 230).reduce((sum, l) => sum + l.length_km, 0),
          line_length_115kv_km: lines.filter(l => l.voltage_kv === 115).reduce((sum, l) => sum + l.length_km, 0),
          total_capacity_500kv_mva: substations.filter(s => s.voltage_kv === 500).reduce((sum, s) => sum + s.capacity_mva, 0),
          total_capacity_230kv_mva: substations.filter(s => s.voltage_kv === 230).reduce((sum, s) => sum + s.capacity_mva, 0),
          total_capacity_115kv_mva: substations.filter(s => s.voltage_kv === 115).reduce((sum, s) => sum + s.capacity_mva, 0),
          regions_covered: [...new Set(substations.map(s => s.region))],
          provinces_covered: [...new Set(substations.map(s => s.province))],
        };
      }

      setData({ substations, lines, stats });
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Error fetching EGAT transmission data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load EGAT data');
    } finally {
      setLoading(false);
    }
  }, [getApiUrl, region]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, lastRefresh, refresh: fetchData };
}
