"use client";

/**
 * Microgrid geospatial + electrical boundary definition.
 *
 * The meters are in Surat Thani (~9.509°N, 99.988°E).
 * Defines:
 * - Geographic boundary polygon
 * - Point of Common Coupling (PCC)
 * - Feeder network from real meter coordinates
 * - Grid-tied / islanded mode tracking
 */

import { useMemo, createContext, useContext, useState, useCallback, type ReactNode } from 'react';

// ── Point of Common Coupling ─────────────────────────────────────────────
// Where the microgrid connects to the main grid (substation side)

export interface PCCStatus {
    mode: 'grid-tied' | 'islanded' | 'transitioning';
    power_kw: number;        // positive = importing, negative = exporting
    voltage_pu: number;      // per-unit voltage at PCC
    frequency_hz: number;
    last_sync: number;       // timestamp
}

export const PCC: { lat: number; lon: number; label: string } = {
    lat: 9.528326082141575,
    lon: 99.99007762999207,
    label: 'PCC — Main Grid Connection',
};

// ── Boundary Polygon ─────────────────────────────────────────────────────
// Rectangle around the meters with ~150m padding

export const MICROGRID_BOUNDARY = {
    type: 'Polygon' as const,
    coordinates: [[
        [99.9887, 9.5270], // SW
        [99.9922, 9.5270], // SE
        [99.9922, 9.5298], // NE
        [99.9887, 9.5298], // NW
        [99.9887, 9.5270], // close ring
    ]] as [number, number][][],
};

export const MICROGRID_CENTER = { lat: 9.528326082141575, lon: 99.99007762999207 };
export const MICROGRID_LABEL = 'Surat Thani';

// ── Feeder Network ───────────────────────────────────────────────────────
// Electrical connectivity from real meter coordinates
// Creates a spanning tree rooted at PCC

export function buildFeederNetwork(meters: { id: string; lon: number; lat: number }[]): {
    boundary: GeoJSON.Polygon;
    feeders: GeoJSON.FeatureCollection;
} {
    if (meters.length === 0) {
        return {
            boundary: MICROGRID_BOUNDARY,
            feeders: { type: 'FeatureCollection', features: [] },
        };
    }

    // Compute convex hull from all meter coordinates + PCC
    const points = [
        [PCC.lon, PCC.lat],
        ...meters.map(m => [m.lon, m.lat]),
    ];

    // Simple bounding box with 100m padding as boundary
    const lons = points.map(p => p[0]);
    const lats = points.map(p => p[1]);
    const pad = 0.001; // ~100m
    const minLon = Math.min(...lons) - pad;
    const maxLon = Math.max(...lons) + pad;
    const minLat = Math.min(...lats) - pad;
    const maxLat = Math.max(...lats) + pad;

    const boundary: GeoJSON.Polygon = {
        type: 'Polygon',
        coordinates: [[
            [minLon, minLat],
            [maxLon, minLat],
            [maxLon, maxLat],
            [minLon, maxLat],
            [minLon, minLat],
        ]],
    };

    // Build spanning tree feeders (nearest-neighbor from PCC)
    const visited = new Set<string>();
    const feederLines: GeoJSON.Feature<GeoJSON.LineString>[] = [];
    const unvisited = new Map(meters.map(m => [m.id, m]));

    // Start from PCC, connect to nearest meter
    let current: { lon: number; lat: number; id: string } = {
        lon: PCC.lon,
        lat: PCC.lat,
        id: 'PCC',
    };
    visited.add('PCC');

    while (unvisited.size > 0) {
        let nearestId = '';
        let nearestDist = Infinity;
        let nearestMeter: { id: string; lon: number; lat: number } | null = null;

        for (const [id, m] of unvisited) {
            const d = (m.lon - current.lon) ** 2 + (m.lat - current.lat) ** 2;
            if (d < nearestDist) {
                nearestDist = d;
                nearestId = id;
                nearestMeter = m;
            }
        }

        if (nearestMeter) {
            feederLines.push({
                type: 'Feature',
                geometry: {
                    type: 'LineString',
                    coordinates: [
                        [current.lon, current.lat],
                        [nearestMeter.lon, nearestMeter.lat],
                    ],
                },
                properties: { from: current.id, to: nearestMeter.id },
            });
            visited.add(nearestId);
            unvisited.delete(nearestId);
            current = nearestMeter;
        } else {
            break;
        }
    }

    // Add a few cross-links for mesh redundancy (connect ends back to PCC area)
    if (feederLines.length >= 3) {
        const last = feederLines[feederLines.length - 1];
        const lastCoords = last.geometry.coordinates[1];
        feederLines.push({
            type: 'Feature',
            geometry: {
                type: 'LineString',
                coordinates: [
                    [lastCoords[0], lastCoords[1]],
                    [PCC.lon, PCC.lat],
                ],
            },
            properties: { from: last.properties!.to, to: 'PCC', cross_link: true },
        });
    }

    return {
        boundary,
        feeders: { type: 'FeatureCollection', features: feederLines },
    };
}

// ── Electrical Boundary State ────────────────────────────────────────────

export interface ElectricalBoundary {
    pcc: PCCStatus;
    totalGen_kw: number;
    totalCons_kw: number;
    netFlow_kw: number;       // positive = import from grid
    selfSufficiency_pct: number;
    islandCapable: boolean;
}

export function simulateElectricalBoundary(
    meters: { gen_kwh: number; cons_kwh: number }[],
    pccStatus: PCCStatus
): ElectricalBoundary {
    const totalGen = meters.reduce((s, m) => s + m.gen_kwh, 0);
    const totalCons = meters.reduce((s, m) => s + m.cons_kwh, 0);
    const netLoad = totalCons - totalGen;

    let pccPower = 0;
    if (pccStatus.mode === 'grid-tied') {
        pccPower = netLoad > 0 ? netLoad : 0; // import deficit, export = 0 (islanded for export)
    } else {
        pccPower = 0; // islanded
    }

    return {
        pcc: pccStatus,
        totalGen_kw: totalGen,
        totalCons_kw: totalCons,
        netFlow_kw: pccPower,
        selfSufficiency_pct: totalCons > 0 ? (totalGen / totalCons) * 100 : 0,
        islandCapable: totalGen >= totalCons * 0.8, // can cover 80% of load
    };
}

// ── Spatial Utilities ────────────────────────────────────────────────────

export function isInsideBoundary(lon: number, lat: number, polygon = MICROGRID_BOUNDARY): boolean {
    const coords = polygon.coordinates[0];
    let inside = false;
    for (let i = 0, j = coords.length - 1; i < coords.length; j = i++) {
        const [xi, yi] = coords[i];
        const [xj, yj] = coords[j];
        if (((yi > lat) !== (yj > lat)) && (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi)) {
            inside = !inside;
        }
    }
    return inside;
}

export function haversineDistanceKm(lon1: number, lat1: number, lon2: number, lat2: number): number {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ── React Context ────────────────────────────────────────────────────────

interface MicroGridContextValue {
    boundary: GeoJSON.Polygon;
    center: { lat: number; lon: number };
    label: string;
    pcc: typeof PCC;
    isInside: (lon: number, lat: number) => boolean;
    distanceFromCenterKm: (lon: number, lat: number) => number;
    toggleMode: () => void;
}

const MicroGridContext = createContext<MicroGridContextValue | undefined>(undefined);

export function MicroGridProvider({ children }: { children: ReactNode }) {
    const [mode, setMode] = useState<'grid-tied' | 'islanded'>('grid-tied');

    const toggleMode = useCallback(() => {
        setMode(prev => prev === 'grid-tied' ? 'islanded' : 'grid-tied');
    }, []);

    const value = useMemo<MicroGridContextValue>(() => ({
        boundary: MICROGRID_BOUNDARY,
        center: MICROGRID_CENTER,
        label: MICROGRID_LABEL,
        pcc: PCC,
        isInside: (lon, lat) => isInsideBoundary(lon, lat),
        distanceFromCenterKm: (lon, lat) => haversineDistanceKm(lon, lat, MICROGRID_CENTER.lon, MICROGRID_CENTER.lat),
        toggleMode,
    }), [toggleMode]);

    return <MicroGridContext.Provider value={value}>{children}</MicroGridContext.Provider>;
}

export function useMicroGrid() {
    const ctx = useContext(MicroGridContext);
    if (!ctx) throw new Error('useMicroGrid must be used within MicroGridProvider');
    return ctx;
}

export function filterMetersInBoundary<T extends { lon: number; lat: number }>(meters: T[]): T[] {
    return meters.filter(m => isInsideBoundary(m.lon, m.lat));
}
