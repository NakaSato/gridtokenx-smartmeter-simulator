import { Marker, Popup } from 'react-leaflet';
import { Home } from 'lucide-react';
import type { MeterData } from './types';
import { createCustomIcon, getMeterColor, getMeterSize } from './utils';

interface MeterMarkerProps {
    meter: MeterData;
}

export const MeterMarker = ({ meter }: MeterMarkerProps) => {
    const pos = [meter.latitude, meter.longitude] as [number, number];
    const color = getMeterColor(meter.meter_type, meter.generation, meter.consumption);
    const size = getMeterSize(meter.generation, meter.consumption);
    const netEnergy = meter.generation - meter.consumption;
    const voltagePercent = ((meter.voltage / 230) * 100).toFixed(1);

    return (
        <Marker key={meter.meter_id} position={pos} icon={createCustomIcon(color, size)}>
            <Popup className="glass-popup">
                <div className="p-3 space-y-3 min-w-[200px]">
                    <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
                        <Home className="w-4 h-4 text-slate-600" />
                        <div>
                            <h3 className="font-bold text-slate-900 text-sm">{meter.location_name}</h3>
                            <p className="text-xs text-slate-500">Phase {meter.phase}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                            <div className="text-[10px] uppercase font-bold text-slate-500">Generation</div>
                            <div className="font-black text-emerald-600 text-sm">{meter.generation.toFixed(2)} kWh</div>
                        </div>
                        <div className="space-y-1">
                            <div className="text-[10px] uppercase font-bold text-slate-500">Consumption</div>
                            <div className="font-black text-rose-600 text-sm">{meter.consumption.toFixed(2)} kWh</div>
                        </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-slate-200">
                        <span className="text-[10px] font-bold text-slate-500">Net Energy</span>
                        <span className={`text-xs font-black ${netEnergy > 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                            {netEnergy.toFixed(2)} kWh
                        </span>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                        <span className="text-[10px] font-bold text-slate-500">Voltage</span>
                        <span className="text-xs font-bold text-blue-600">{voltagePercent}% pu</span>
                    </div>
                </div>
            </Popup>
        </Marker>
    );
};
