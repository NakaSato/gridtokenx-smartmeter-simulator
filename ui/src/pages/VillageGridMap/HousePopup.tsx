import { Home, Zap } from 'lucide-react';
import type { VillageHouse } from './types';

interface HousePopupProps {
    house: VillageHouse;
    x: number;
    y: number;
    onClose: () => void;
}

export const HousePopup = ({ house, x, y, onClose }: HousePopupProps) => {
    const isProducer = house.generation > house.consumption;
    const isProsumer = house.generation > 0 && house.generation < house.consumption;
    const netEnergy = house.generation - house.consumption;

    return (
        <div
            className="glass p-4 rounded-2xl border border-white/10 shadow-2xl backdrop-blur-xl bg-slate-900/95 min-w-[280px]"
            style={{ position: 'absolute', left: x + 20, top: y - 20 }}
        >
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                    <div className={`p-2 rounded-xl ${isProducer ? 'bg-emerald-500/20' : isProsumer ? 'bg-amber-500/20' : 'bg-blue-500/20'}`}>
                        <Home className={`w-4 h-4 ${isProducer ? 'text-emerald-400' : isProsumer ? 'text-amber-400' : 'text-blue-400'}`} />
                    </div>
                    <div>
                        <h3 className="text-sm font-black text-white">{house.name}</h3>
                        <p className="text-[10px] text-slate-400">Phase {house.phase}</p>
                    </div>
                </div>
                <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
                    <span className="text-lg">×</span>
                </button>
            </div>

            <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2">
                    <div className="bg-slate-800/50 rounded-lg p-2">
                        <p className="text-[9px] text-slate-500 uppercase font-bold">Generation</p>
                        <p className="text-sm font-black text-emerald-400">{house.generation.toFixed(2)} <span className="text-xs">kWh</span></p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-2">
                        <p className="text-[9px] text-slate-500 uppercase font-bold">Consumption</p>
                        <p className="text-sm font-black text-rose-400">{house.consumption.toFixed(2)} <span className="text-xs">kWh</span></p>
                    </div>
                </div>

                <div className="flex items-center justify-between bg-slate-800/50 rounded-lg p-2">
                    <span className="text-[9px] text-slate-500 uppercase font-bold">Net Energy</span>
                    <span className={`text-sm font-black ${netEnergy > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {netEnergy.toFixed(2)} <span className="text-xs">kWh</span>
                    </span>
                </div>

                <div className="flex items-center justify-between bg-slate-800/50 rounded-lg p-2">
                    <span className="text-[9px] text-slate-500 uppercase font-bold">Voltage</span>
                    <span className="text-sm font-black text-blue-400">{((house.voltage / 230) * 100).toFixed(1)}% <span className="text-xs">pu</span></span>
                </div>

                {house.nodal_price && (
                    <div className="flex items-center gap-2 bg-amber-500/10 rounded-lg p-2 border border-amber-500/20">
                        <Zap className="w-3.5 h-3.5 text-amber-400" />
                        <span className="text-[9px] text-slate-400 font-bold">Nodal Price:</span>
                        <span className="text-xs font-black text-amber-400">{(house.nodal_price * 1000).toFixed(1)} ฿/kWh</span>
                    </div>
                )}
            </div>
        </div>
    );
};
