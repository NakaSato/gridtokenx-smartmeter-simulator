import { useState, useEffect, useMemo } from 'react';
import Map, { Source, Layer, NavigationControl } from 'react-map-gl';
import type { ViewStateChangeEvent, LineLayer, CircleLayer } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { useNetwork } from '../context/NetworkContext';
import type { VillageHouse } from '../features/village-grid-map/types';
import { MAPBOX_TOKEN, createLineLayer, createGlowLayer, createHouseLayer, createHouseGlowLayer } from '../features/village-grid-map/mapLayers';
import { MapHeader } from '../features/village-grid-map/MapHeader';
import { SearchFilterPanel } from '../features/village-grid-map/SearchFilterPanel';
import { HousePopup } from '../features/village-grid-map/HousePopup';
import { MissingMapboxToken } from '../features/village-grid-map/MissingMapboxToken';
import { useVillageData } from '../features/village-grid-map/useVillageData';

const VillageGridMap = () => {
    const { getApiUrl, getWsUrl } = useNetwork();
    const [lines, setLines] = useState<any[]>([]);
    const [hoverInfo, setHoverInfo] = useState<{ house: VillageHouse, x: number, y: number } | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState<'all' | 'producer' | 'consumer'>('all');
    const [viewState, setViewState] = useState({
        longitude: 100.6610,
        latitude: 13.7563,
        zoom: 16.5,
        pitch: 0,
        bearing: 0
    });

    const {
        houses,
        stats,
        fetchMeters,
        loading,
        error
    } = useVillageData({ getApiUrl, getWsUrl });

    // Fetch lines on mount
    useEffect(() => {
        fetchMeters().then(setLines);
    }, [fetchMeters]);

    // Animation
    const [animationTime, setAnimationTime] = useState(0);
    useEffect(() => {
        const animate = (time: number) => {
            setAnimationTime(time / 1000);
            requestAnimationFrame(animate);
        };
        const id = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(id);
    }, []);

    // Mapbox layers
    const lineLayer: LineLayer = useMemo(() => createLineLayer(), []);
    const glowLayer: LineLayer = useMemo(() => createGlowLayer(animationTime), [animationTime]);
    const houseLayer: CircleLayer = useMemo(() => createHouseLayer(), []);
    const houseGlowLayer: CircleLayer = useMemo(() => createHouseGlowLayer(animationTime), [animationTime]);

    // Filter houses
    const filteredHouses = useMemo(() => {
        return houses.filter(h => {
            const matchesSearch = h.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                                 h.name.toLowerCase().includes(searchQuery.toLowerCase());
            const matchesFilter = filterType === 'all' ||
                                 (filterType === 'producer' && h.generation > h.consumption) ||
                                 (filterType === 'consumer' && h.consumption > h.generation);
            return matchesSearch && matchesFilter;
        });
    }, [houses, searchQuery, filterType]);

    const houseSource = useMemo(() => ({
        type: 'FeatureCollection' as const,
        features: filteredHouses.map(h => ({
            type: 'Feature' as const,
            geometry: { type: 'Point' as const, coordinates: [h.longitude, h.latitude] },
            properties: h
        }))
    }), [filteredHouses]);

    const lineSource = useMemo(() => ({
        type: 'FeatureCollection' as const,
        features: lines
    }), [lines]);

    // Show loading state
    if (loading) {
        return (
            <div className="h-screen w-full flex items-center justify-center bg-slate-950">
                <div className="text-center space-y-4">
                    <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
                    <h2 className="text-xl font-bold text-white">Loading Village Grid...</h2>
                    <p className="text-slate-400">Fetching meter data and grid topology</p>
                </div>
            </div>
        );
    }

    // Show error state
    if (error) {
        return (
            <div className="h-screen w-full flex items-center justify-center bg-slate-950">
                <div className="text-center space-y-4 max-w-md p-6">
                    <div className="w-16 h-16 bg-rose-500/20 rounded-full flex items-center justify-center mx-auto">
                        <svg className="w-8 h-8 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h2 className="text-xl font-bold text-white">Failed to Load Grid</h2>
                    <p className="text-slate-400">{error}</p>
                    <button
                        onClick={() => fetchMeters().then(setLines)}
                        className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl transition-colors"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-screen bg-slate-950 overflow-hidden font-sans text-slate-200">
            <MapHeader housesCount={houses.length} stats={stats} />

            <SearchFilterPanel
                searchQuery={searchQuery}
                filterType={filterType}
                onSearchChange={setSearchQuery}
                onFilterChange={setFilterType}
            />

            <div className="flex-1 relative">
                {!MAPBOX_TOKEN && <MissingMapboxToken />}

                <Map
                    {...viewState}
                    onMove={(evt: ViewStateChangeEvent) => setViewState(evt.viewState)}
                    style={{ width: '100%', height: '100%' }}
                    mapStyle="mapbox://styles/mapbox/dark-v11"
                    mapboxAccessToken={MAPBOX_TOKEN}
                    interactiveLayerIds={['house-points']}
                    onMouseMove={(e) => {
                        const features = e.target.queryRenderedFeatures(e.point, { layers: ['house-points'] });
                        if (features.length > 0) {
                            const coords = features[0].geometry?.type === 'Point' && 'coordinates' in features[0].geometry
                                ? features[0].geometry.coordinates
                                : undefined;
                            if (coords) {
                                const house = filteredHouses.find(h =>
                                    h.longitude === coords[0] &&
                                    h.latitude === coords[1]
                                );
                                if (house) {
                                    setHoverInfo({ house, x: e.point.x, y: e.point.y });
                                }
                            }
                        } else {
                            setHoverInfo(null);
                        }
                    }}
                >
                    <Source id="grid-lines" type="geojson" data={lineSource}>
                        <Layer {...glowLayer} />
                        <Layer {...lineLayer} />
                    </Source>

                    <Source id="house-points" type="geojson" data={houseSource}>
                        <Layer {...houseGlowLayer} />
                        <Layer {...houseLayer} />
                    </Source>

                    <NavigationControl position="bottom-right" showCompass={false} />
                </Map>

                {hoverInfo && (
                    <HousePopup
                        house={hoverInfo.house}
                        x={hoverInfo.x}
                        y={hoverInfo.y}
                        onClose={() => setHoverInfo(null)}
                    />
                )}
            </div>
        </div>
    );
};

export default VillageGridMap;
