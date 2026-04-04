import { useState, useEffect, useCallback } from 'react';
import type { VillageHouse, MapStats } from './types';

interface UseVillageDataProps {
    getApiUrl: (path: string) => string;
    getWsUrl: (path: string) => string;
}

export const useVillageData = ({ getApiUrl, getWsUrl }: UseVillageDataProps) => {
    const [houses, setHouses] = useState<VillageHouse[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [stats, setStats] = useState<MapStats>({
        totalGeneration: 0,
        totalConsumption: 0,
        avgVoltage: 230,
        phaseBalance: { A: 0, B: 0, C: 0 },
        selfSufficiency: 0,
        carbonOffset: 0
    });

    // Fetch meter data from grid/geojson endpoint
    const fetchMeters = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            
            const gridRes = await fetch(getApiUrl('/api/v1/grid/export?format=geojson'));
            const gridData = await gridRes.json();

            if (gridData.features) {
                // Extract bus features (meters)
                const busFeatures = gridData.features.filter((f: any) => 
                    f.properties.element_type === 'bus' && f.properties.meter_id
                );
                
                const mappedHouses = busFeatures.map((f: any, idx: number) => {
                    const props = f.properties;
                    const coords = f.geometry.coordinates;
                    return {
                        id: props.meter_id || `bus-${props.id}`,
                        name: props.name || `House ${idx + 1}`,
                        latitude: coords[1] || 13.7563,
                        longitude: coords[0] || 100.6610,
                        phase: props.phase || ['A', 'B', 'C'][idx % 3] as 'A' | 'B' | 'C',
                        generation: 0,
                        consumption: 0,
                        voltage: props.vm_pu ? props.vm_pu * 230 : 230
                    };
                });
                setHouses(mappedHouses);
                setLoading(false);

                // Return line features for the line layer
                return gridData.features.filter((f: any) => f.properties.element_type === 'line');
            }
        } catch (err) {
            console.error('Failed to fetch grid topology:', err);
            setError(err instanceof Error ? err.message : 'Failed to load grid data');
            setLoading(false);
        }
        return [];
    }, [getApiUrl]);

    // WebSocket for real-time updates
    useEffect(() => {
        const wsUrl = getWsUrl('/ws');
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'meter_readings' && message.readings) {
                    const readings = message.readings;

                    setHouses(prev => prev.map(house => {
                        const reading = readings.find((r: any) => r.meter_id === house.id);
                        if (reading) {
                            return {
                                ...house,
                                generation: reading.energy_generated || 0,
                                consumption: reading.energy_consumed || 0,
                                voltage: reading.voltage || 230,
                                nodal_price: reading.nodal_price || 0.50
                            };
                        }
                        return house;
                    }));

                    const totalGen = readings.reduce((sum: number, r: any) => sum + (r.energy_generated || 0), 0);
                    const totalCons = readings.reduce((sum: number, r: any) => sum + (r.energy_consumed || 0), 0);
                    const avgVolt = readings.reduce((sum: number, r: any) => sum + (r.voltage || 230), 0) / readings.length;
                    const phaseBalance: any = { A: 0, B: 0, C: 0 };
                    readings.forEach((r: any) => {
                        const phase = r.phase || 'A';
                        phaseBalance[phase] = (phaseBalance[phase] || 0) + 1;
                    });

                    setStats({
                        totalGeneration: totalGen,
                        totalConsumption: totalCons,
                        avgVoltage: avgVolt,
                        phaseBalance,
                        selfSufficiency: (totalGen / (totalCons || 1)) * 100,
                        carbonOffset: totalGen * 0.431 / 1000
                    });
                }
            } catch (e) {
                console.error('WS error:', e);
            }
        };

        return () => ws.close();
    }, [getWsUrl]);

    return {
        houses,
        stats,
        fetchMeters,
        loading,
        error
    };
};
