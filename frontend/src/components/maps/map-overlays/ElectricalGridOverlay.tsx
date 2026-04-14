"use client";

/**
 * Electrical Grid Overlay Component
 * 
 * Adds electrical infrastructure layers to the existing map
 * Shows EGAT, MEA, and PEA infrastructure
 */

import { useState, useEffect } from 'react';
import { CircleMarker, Tooltip } from 'react-leaflet';
import { Zap } from 'lucide-react';
import { useNetwork } from '@/components/providers/NetworkProvider';
import type { ElectricalInfrastructure } from '@/components/maps/electrical-grid/types';

interface ElectricalGridOverlayProps {
    visible: boolean;
    operators?: ('EGAT' | 'MEA' | 'PEA')[];
    types?: string[];
    onInfrastructureClick?: (item: ElectricalInfrastructure) => void;
}

// Infrastructure colors by operator
const OPERATOR_COLORS = {
    EGAT: '#EF4444',  // Red
    MEA: '#3B82F6',   // Blue
    PEA: '#10B981'    // Green
};

// Infrastructure sizes by zoom level
const getInfrastructureSize = (zoom: number, type: string) => {
    const baseSizes: Record<string, number> = {
        transmission_substation: 12,
        distribution_substation: 8,
        transmission_tower: 6,
        distribution_pole: 4,
        power_plant: 15,
        solar_farm: 10,
        battery_storage: 8,
        ev_charging_station: 6
    };
    
    const baseSize = baseSizes[type] || 6;
    const zoomMultiplier = Math.max(1, zoom / 10);
    
    return baseSize * zoomMultiplier;
};

export const ElectricalGridOverlay = ({
    visible,
    operators = ['EGAT', 'MEA', 'PEA'],
    types = [],
    onInfrastructureClick
}: ElectricalGridOverlayProps) => {
    const { getApiUrl } = useNetwork();
    const [infrastructure, setInfrastructure] = useState<ElectricalInfrastructure[]>([]);
    const [selectedItem, setSelectedItem] = useState<ElectricalInfrastructure | null>(null);
    const [popupPosition, setPopupPosition] = useState<[number, number] | null>(null);

    useEffect(() => {
        if (!visible) return;

        // Fetch electrical infrastructure
        const fetchInfrastructure = async () => {
            try {
                const response = await fetch(getApiUrl('/api/v1/grid/substations?limit=1000'));
                if (!response.ok) throw new Error('Failed to fetch infrastructure');
                
                const data = await response.json();
                setInfrastructure(data.infrastructure || []);
            } catch (error) {
                console.error('Error fetching electrical infrastructure:', error);
                // Use empty array on error
                setInfrastructure([]);
            }
        };

        fetchInfrastructure();
    }, [visible]);

    const handleMarkerClick = (item: ElectricalInfrastructure, lat: number, lng: number) => {
        setSelectedItem(item);
        setPopupPosition([lat, lng]);
        onInfrastructureClick?.(item);
    };

    const handleClosePopup = () => {
        setSelectedItem(null);
        setPopupPosition(null);
    };

    if (!visible || infrastructure.length === 0) {
        return null;
    }

    return (
        <>
            {infrastructure
                .filter(item => operators.includes(item.operator))
                .filter(item => types.length === 0 || types.includes(item.type))
                .map((item) => {
                    const color = OPERATOR_COLORS[item.operator as keyof typeof OPERATOR_COLORS];
                    const radius = getInfrastructureSize(10, item.type);

                    return (
                        <CircleMarker
                            key={item.id}
                            center={[item.latitude, item.longitude] as [number, number]}
                            radius={radius}
                            pathOptions={{
                                color: color,
                                fillColor: color,
                                fillOpacity: 0.7,
                                weight: 2
                            }}
                            eventHandlers={{
                                click: (e) => {
                                    handleMarkerClick(item, item.latitude, item.longitude);
                                }
                            }}
                        />
                    );
                })}

            {/* Popup for selected infrastructure */}
            {selectedItem && popupPosition && (
                <Tooltip position={popupPosition as any} permanent direction="top">
                    <div className="p-2 min-w-[200px]">
                        {/* Header */}
                        <div className="flex items-center space-x-2 mb-2">
                            <Zap
                                className="w-5 h-5"
                                style={{
                                    color: OPERATOR_COLORS[
                                        selectedItem.operator as keyof typeof OPERATOR_COLORS
                                    ]
                                }}
                            />
                            <span
                                className="font-bold text-sm"
                                style={{
                                    color: OPERATOR_COLORS[
                                        selectedItem.operator as keyof typeof OPERATOR_COLORS
                                    ]
                                }}
                            >
                                {selectedItem.operator}
                            </span>
                        </div>

                        {/* Name */}
                        <h3 className="font-bold text-gray-900 mb-1">
                            {selectedItem.name_en || selectedItem.id}
                        </h3>
                        {selectedItem.name_th && (
                            <p className="text-sm text-gray-600 mb-2">{selectedItem.name_th}</p>
                        )}

                        {/* Details */}
                        <div className="space-y-1 text-sm text-gray-700">
                            {/* Type */}
                            <div className="flex justify-between">
                                <span className="text-gray-500">Type:</span>
                                <span className="capitalize">
                                    {selectedItem.type?.replace(/_/g, ' ')}
                                </span>
                            </div>

                            {/* Voltage */}
                            {selectedItem.voltage_kv && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Voltage:</span>
                                    <span className="font-semibold">
                                        {selectedItem.voltage_kv} kV
                                    </span>
                                </div>
                            )}

                            {/* Location */}
                            {selectedItem.province && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Province:</span>
                                    <span>{selectedItem.province}</span>
                                </div>
                            )}

                            {/* Status */}
                            {selectedItem.status && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Status:</span>
                                    <span
                                        className={`px-2 py-0.5 rounded-full text-xs ${
                                            selectedItem.status === 'operational'
                                                ? 'bg-green-100 text-green-700'
                                                : selectedItem.status === 'under_construction'
                                                ? 'bg-yellow-100 text-yellow-700'
                                                : 'bg-gray-100 text-gray-700'
                                        }`}
                                    >
                                        {selectedItem.status.replace(/_/g, ' ')}
                                    </span>
                                </div>
                            )}

                            {/* Reference */}
                            {selectedItem.ref && (
                                <div className="text-xs text-gray-500 mt-2 pt-2 border-t">
                                    Ref: {selectedItem.ref}
                                </div>
                            )}
                        </div>
                    </div>
                </Tooltip>
            )}
        </>
    );
};
