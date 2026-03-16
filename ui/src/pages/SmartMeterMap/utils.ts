import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

// Fix Leaflet default icon issue
export const DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

// Custom colored marker icons
export const createCustomIcon = (color: string, size = 12) => L.divIcon({
    className: "custom-marker",
    html: `<div style="background-color: ${color}; width: ${size}px; height: ${size}px; border-radius: 50%; box-shadow: 0 0 10px ${color}, 0 0 20px ${color}; border: 3px solid white;"></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
});

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
