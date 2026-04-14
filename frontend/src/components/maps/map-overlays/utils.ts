import L from 'leaflet';

// Custom colored marker icons with optional label
export const createCustomIcon = (color: string, label?: string, size = 12) => {
    const html = `<div style="position:relative;display:flex;flex-direction:column;align-items:center;gap:2px;">
        <div style="background-color:${color};width:${size}px;height:${size}px;border-radius:50%;box-shadow:0 0 10px ${color},0 0 20px ${color}40;border:2px solid rgba(255,255,255,0.8);"></div>
        ${label ? `<div style="font-size:9px;font-weight:700;color:#fff;text-shadow:0 1px 3px rgba(0,0,0,0.8),0 0 6px rgba(0,0,0,0.6);white-space:nowrap;line-height:1;letter-spacing:0.02em;">${label}</div>` : ''}
    </div>`;
    const iconSize = [Math.max(size + 4, label ? 36 : size), size + (label ? 14 : 0)];
    return L.divIcon({
        className: "custom-marker",
        html,
        iconSize: iconSize as [number, number],
        iconAnchor: [iconSize[0] / 2, iconSize[1] / 2]
    });
};

// Get marker color based on energy status
export const getMeterColor = (type: string, generation: number, consumption: number): string => {
    if (generation > consumption) return '#10b981'; // emerald (producer)
    if (generation > 0 && generation < consumption) return '#f59e0b'; // amber (prosumer)
    if (type.includes('Solar')) return '#f59e0b';
    if (type.includes('Battery')) return '#10b981';
    if (type.includes('Hybrid')) return '#a855f7';
    return '#3b82f6'; // blue (consumer)
};

// Get marker size based on energy status
export const getMeterSize = (generation: number, consumption: number): number => {
    if (generation > consumption) return 16;
    if (generation > 0) return 14;
    return 12;
};
