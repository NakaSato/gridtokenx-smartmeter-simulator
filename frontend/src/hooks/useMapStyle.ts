"use client";

import { useState, useCallback } from 'react';

export type MapStyleId = 'dark' | 'satellite';

const MAPBOX_STYLES: Record<MapStyleId, string> = {
    dark: 'mapbox://styles/mapbox/dark-v11',
    satellite: 'mapbox://styles/mapbox/satellite-streets-v12',
};

export function useMapStyle(defaultStyle: MapStyleId = 'dark') {
    const [style, setStyle] = useState<MapStyleId>(defaultStyle);
    const toggle = useCallback(() => {
        setStyle(prev => prev === 'dark' ? 'satellite' : 'dark');
    }, []);
    return { style, mapStyle: MAPBOX_STYLES[style], toggle, isSatellite: style === 'satellite' };
}
