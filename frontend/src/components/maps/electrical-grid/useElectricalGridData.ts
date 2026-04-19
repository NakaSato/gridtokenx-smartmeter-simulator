import { useState, useEffect, useRef, useCallback } from 'react';
import type { ElectricalInfrastructure, ElectricalGridStats, InfrastructureType } from './types';

const EMPTY_STATS: ElectricalGridStats = {
  totalInfrastructure: 0,
  byOperator: { EGAT: 0, MEA: 0, PEA: 0 },
  byType: {} as Record<InfrastructureType, number>,
  byVoltage: { '500kV': 0, '230kV': 0, '115kV': 0, '22kV': 0, '33kV': 0 },
  byProvince: {}
};

const calculateStats = (data: ElectricalInfrastructure[]): ElectricalGridStats => {
  const stats: ElectricalGridStats = {
    totalInfrastructure: data.length,
    byOperator: { EGAT: 0, MEA: 0, PEA: 0 },
    byType: {} as Record<InfrastructureType, number>,
    byVoltage: { '500kV': 0, '230kV': 0, '115kV': 0, '22kV': 0, '33kV': 0 },
    byProvince: {}
  };
  data.forEach(item => {
    stats.byOperator[item.operator]++;
    stats.byType[item.type] = (stats.byType[item.type] || 0) + 1;
    if (item.voltage_kv) {
      const key = `${item.voltage_kv}kV` as keyof typeof stats.byVoltage;
      if (stats.byVoltage[key] !== undefined) stats.byVoltage[key]++;
    }
    if (item.province) stats.byProvince[item.province] = (stats.byProvince[item.province] || 0) + 1;
  });
  return stats;
};

export const useElectricalGridData = (
  getApiUrl: (path: string) => string,
  refreshIntervalMs: number = 5000,
) => {
  const [infrastructure, setInfrastructure] = useState<ElectricalInfrastructure[]>([]);
  const [stats, setStats] = useState<ElectricalGridStats>(EMPTY_STATS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const fetchRef = useRef(false);

  const fetchData = useCallback(async () => {
    try {
      if (!fetchRef.current) setLoading(prev => prev ? true : false);
      setError(null);

      const response = await fetch(getApiUrl('/api/v1/grid/substations'));
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      const rawItems = data.infrastructure || data.substations || [];
      const infraData: ElectricalInfrastructure[] = rawItems
        .map((item: any) => ({
          ...item,
          latitude: item.latitude ?? item.lat,
          longitude: item.longitude ?? item.lon,
          status: item.status === 'in_service' ? 'operational' : item.status
        }))
        .filter((item: any) => typeof item.latitude === 'number' && typeof item.longitude === 'number');

      setInfrastructure(infraData);
      setStats(data.stats || calculateStats(infraData));
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
      fetchRef.current = true;
    }
  }, [getApiUrl]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, refreshIntervalMs);
    return () => clearInterval(interval);
  }, [fetchData, refreshIntervalMs]);

  return { infrastructure, stats, loading, error, lastRefresh, refresh: fetchData };
};
