import type { LineLayer, CircleLayer } from 'react-map-gl';

export const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || '';

// Generate animated pulse factor
export const getPulseFactor = (animationTime: number) => {
    return (Math.sin(animationTime * 4) + 1) / 2;
};

// Mapbox line layer configuration
export const createLineLayer = (): LineLayer => ({
    id: 'grid-lines',
    type: 'line',
    source: 'grid-lines',
    paint: {
        'line-color': [
            'match',
            ['get', 'phase'],
            'A', '#f97316',
            'B', '#3b82f6',
            'C', '#22c55e',
            '#94a3b8'
        ],
        'line-width': [
            'match',
            ['get', 'style_type'],
            'feeder', 4,
            'service_drop', 1.5,
            2
        ],
        'line-opacity': [
            'match',
            ['get', 'style_type'],
            'feeder', 0.8,
            'service_drop', 0.5,
            0.6
        ],
        'line-dasharray': [
            'match',
            ['get', 'style_type'],
            'service_drop', ['literal', [2, 2]],
            ['literal', [1, 0]]
        ]
    }
});

// Glow effect layer
export const createGlowLayer = (animationTime: number): LineLayer => {
    const pulseFactor = (Math.sin(animationTime * 4) + 1) / 2;
    return {
    id: 'grid-glow',
    type: 'line',
    source: 'grid-lines',
    paint: {
        'line-color': [
            'match',
            ['get', 'phase'],
            'A', '#f97316',
            'B', '#3b82f6',
            'C', '#22c55e',
            '#94a3b8'
        ],
        'line-width': 8,
        'line-blur': 6,
        'line-opacity': 0.15 + (pulseFactor * 0.15)
    }
};
}

// House circle layer
export const createHouseLayer = (): CircleLayer => ({
    id: 'house-points',
    type: 'circle',
    source: 'house-points',
    paint: {
        'circle-radius': [
            'case',
            ['>', ['get', 'generation'], ['get', 'consumption']], 10,
            8
        ],
        'circle-color': [
            'match',
            ['get', 'phase'],
            'A', '#f97316',
            'B', '#3b82f6',
            'C', '#22c55e',
            '#94a3b8'
        ],
        'circle-stroke-width': 3,
        'circle-stroke-color': '#ffffff',
        'circle-opacity': 0.9,
        'circle-pitch-alignment': 'viewport'
    }
});

// House glow layer
export const createHouseGlowLayer = (animationTime: number): CircleLayer => {
    const pulseFactor = (Math.sin(animationTime * 4) + 1) / 2;
    return {
    id: 'house-glow',
    type: 'circle',
    source: 'house-points',
    paint: {
        'circle-radius': [
            'case',
            ['>', ['get', 'generation'], ['get', 'consumption']], 18,
            14
        ],
        'circle-color': [
            'match',
            ['get', 'phase'],
            'A', '#f97316',
            'B', '#3b82f6',
            'C', '#22c55e',
            '#94a3b8'
        ],
        'circle-blur': 0.8,
        'circle-opacity': 0.3 + (pulseFactor * 0.2),
        'circle-pitch-alignment': 'viewport'
    }
};
}

// Trade pulse layer
export const createPulseLayer = (): LineLayer => ({
    id: 'trade-pulses',
    type: 'line',
    source: 'trade-pulses',
    paint: {
        'line-color': ['match', ['get', 'type'], 'buy', '#3b82f6', '#22c55e'],
        'line-width': 3,
        'line-opacity': 0.8,
        'line-dasharray': [2, 4],
    },
    layout: {
        'line-cap': 'round',
        'line-join': 'round'
    }
});
