/**
 * Electrical Grid Data Hook
 * 
 * Fetches electrical infrastructure data from the API
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { ElectricalInfrastructure, ElectricalGridStats, InfrastructureType } from './types';

export const useElectricalGridData = (
  getApiUrl: (path: string) => string,
  refreshIntervalMs: number = 5000,
) => {
  const [infrastructure, setInfrastructure] = useState<ElectricalInfrastructure[]>([]);
  const [stats, setStats] = useState<ElectricalGridStats>({
    totalInfrastructure: 0,
    byOperator: { EGAT: 0, MEA: 0, PEA: 0 },
    byType: {} as Record<InfrastructureType, number>,
    byVoltage: { '500kV': 0, '230kV': 0, '115kV': 0, '22kV': 0, '33kV': 0 },
    byProvince: {}
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchRef = useRef(false);

  const fetchData = useCallback(async () => {
    try {
      if (!fetchRef.current) setLoading(prev => prev ? true : false);
      setError(null);

      const response = await fetch(getApiUrl('/api/v1/grid/substations'));

      if (!response.ok) {
        if (response.status === 404) {
          console.log('Using mock electrical infrastructure data');
          const mockData = generateMockData();
          setInfrastructure(mockData.infrastructure);
          setStats(mockData.stats);
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const rawItems = data.infrastructure || data.substations || [];
      // Normalize lat/lon field names (backend returns lat/lon, frontend expects latitude/longitude)
      const infraData = rawItems.map((item: any) => ({
        ...item,
        latitude: item.latitude ?? item.lat,
        longitude: item.longitude ?? item.lon,
        // Normalize status
        status: item.status === 'in_service' ? 'operational' : item.status
      }));
      if (infraData.length === 0) {
        console.log('API returned no data, using mock electrical infrastructure data');
        const mockData = generateMockData();
        setInfrastructure(mockData.infrastructure);
        setStats(mockData.stats);
        return;
      }
      setInfrastructure(infraData);
      setStats(data.stats || calculateStats(infraData));
      setLastRefresh(new Date());

    } catch (err) {
      console.error('Error fetching electrical infrastructure:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');

      const mockData = generateMockData();
      setInfrastructure(mockData.infrastructure);
      setStats(mockData.stats);
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

// Calculate statistics from infrastructure data
const calculateStats = (data: ElectricalInfrastructure[]): ElectricalGridStats => {
  const stats: ElectricalGridStats = {
    totalInfrastructure: data.length,
    byOperator: { EGAT: 0, MEA: 0, PEA: 0 },
    byType: {} as Record<InfrastructureType, number>,
    byVoltage: { '500kV': 0, '230kV': 0, '115kV': 0, '22kV': 0, '33kV': 0 },
    byProvince: {}
  };

  data.forEach(item => {
    // Count by operator
    stats.byOperator[item.operator]++;
    
    // Count by type
    stats.byType[item.type] = (stats.byType[item.type] || 0) + 1;
    
    // Count by voltage
    if (item.voltage_kv) {
      const voltageKey = `${item.voltage_kv}kV` as keyof typeof stats.byVoltage;
      if (stats.byVoltage[voltageKey] !== undefined) {
        stats.byVoltage[voltageKey]++;
      }
    }
    
    // Count by province
    if (item.province) {
      stats.byProvince[item.province] = (stats.byProvince[item.province] || 0) + 1;
    }
  });

  return stats;
};

// Generate mock data for development/testing
const generateMockData = (): { infrastructure: ElectricalInfrastructure[]; stats: ElectricalGridStats } => {
  const infrastructure: ElectricalInfrastructure[] = [
    // EGAT Transmission Substations
    {
      id: 'EGAT-WN-001',
      type: 'transmission_substation',
      operator: 'EGAT',
      latitude: 14.3567,
      longitude: 100.6234,
      voltage_kv: 500,
      name_en: 'Wang Noi',
      name_th: 'วังน้อย',
      status: 'operational',
      commissioning_year: 1985,
      province: 'Phra Nakhon Si Ayutthaya',
      ref: 'EGAT-WN-001'
    },
    {
      id: 'EGAT-TL-001',
      type: 'transmission_substation',
      operator: 'EGAT',
      latitude: 14.1234,
      longitude: 100.7890,
      voltage_kv: 230,
      name_en: 'Tha Luang',
      name_th: 'ท่าหลวง',
      status: 'operational',
      commissioning_year: 1990,
      province: 'Lopburi',
      ref: 'EGAT-TL-001'
    },
    {
      id: 'EGAT-BC-001',
      type: 'transmission_substation',
      operator: 'EGAT',
      latitude: 13.6890,
      longitude: 100.6012,
      voltage_kv: 115,
      name_en: 'Bang Chak',
      name_th: 'บางจาก',
      status: 'operational',
      commissioning_year: 1988,
      province: 'Bangkok',
      ref: 'EGAT-BC-001'
    },
    
    // MEA Distribution Substations
    {
      id: 'MEA-BK-001',
      type: 'distribution_substation',
      operator: 'MEA',
      latitude: 13.7563,
      longitude: 100.5018,
      voltage_kv: 115,
      name_en: 'Bangkok Central',
      name_th: 'กรุงเทพฯ กลาง',
      status: 'operational',
      province: 'Bangkok',
      ref: 'MEA-BK-001'
    },
    {
      id: 'MEA-BK-002',
      type: 'distribution_substation',
      operator: 'MEA',
      latitude: 13.8512,
      longitude: 100.5923,
      voltage_kv: 22,
      name_en: 'Bang Rak',
      name_th: 'บางรัก',
      status: 'operational',
      province: 'Bangkok',
      ref: 'MEA-BK-002'
    },
    
    // PEA Distribution Substations
    {
      id: 'PEA-CM-001',
      type: 'distribution_substation',
      operator: 'PEA',
      latitude: 18.7883,
      longitude: 98.9853,
      voltage_kv: 115,
      name_en: 'Chiang Mai',
      name_th: 'เชียงใหม่',
      status: 'operational',
      province: 'Chiang Mai',
      ref: 'PEA-CM-001'
    },
    {
      id: 'PEA-PK-001',
      type: 'distribution_substation',
      operator: 'PEA',
      latitude: 7.8804,
      longitude: 98.3923,
      voltage_kv: 115,
      name_en: 'Phuket',
      name_th: 'ภูเก็ต',
      status: 'operational',
      province: 'Phuket',
      ref: 'PEA-PK-001'
    },
    
    // MEA Distribution Poles (sample)
    ...Array.from({ length: 20 }).map((_, i) => ({
      id: `MEA-POLE-${String(i + 1).padStart(5, '0')}`,
      type: 'distribution_pole' as InfrastructureType,
      operator: 'MEA' as const,
      latitude: 13.7 + (Math.random() * 0.2),
      longitude: 100.5 + (Math.random() * 0.2),
      voltage_kv: 22,
      status: 'operational' as const,
      province: 'Bangkok',
      ref: `MEA-POLE-${String(i + 1).padStart(5, '0')}`
    })),
    
    // EGAT Power Plants
    {
      id: 'EGAT-PP-001',
      type: 'power_plant',
      operator: 'EGAT',
      latitude: 13.5990,
      longitude: 100.5998,
      voltage_kv: 500,
      name_en: 'Bang Pakong Power Plant',
      name_th: 'โรงไฟฟ้าบางปะกง',
      status: 'operational',
      commissioning_year: 1980,
      province: 'Chachoengsao'
    }
  ];

  return {
    infrastructure,
    stats: calculateStats(infrastructure)
  };
};
