type LineLayer = any;
type CircleLayer = any;

export const createLineLayer = (): LineLayer => ({
    id: 'grid-lines',
    type: 'line',
    source: 'grid-lines',
    paint: {
        'line-color': '#6366f1',
        'line-width': 2,
        'line-opacity': 0.6
    }
});

export const createGlowLayer = (animationTime: number): LineLayer => {
    const pulseFactor = (Math.sin(animationTime * 4) + 1) / 2;
    return {
    id: 'grid-glow',
    type: 'line',
    source: 'grid-lines',
    paint: {
        'line-color': '#6366f1',
        'line-width': 8,
        'line-blur': 6,
        'line-opacity': 0.15 + (pulseFactor * 0.15)
    }
};
}

export const createHouseLayer = (): CircleLayer => ({
    id: 'house-points',
    type: 'circle',
    source: 'house-points',
    paint: {
        'circle-radius': 8,
        'circle-color': [
            'match',
            ['get', 'phase'],
            'A', '#f97316',
            'B', '#3b82f6',
            'C', '#22c55e',
            '#94a3b8'
        ],
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff',
        'circle-opacity': 0.9,
        'circle-pitch-alignment': 'viewport'
    }
});

export const createHouseGlowLayer = (animationTime: number): CircleLayer => {
    const pulseFactor = (Math.sin(animationTime * 4) + 1) / 2;
    return {
    id: 'house-glow',
    type: 'circle',
    source: 'house-points',
    paint: {
        'circle-radius': 16,
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
