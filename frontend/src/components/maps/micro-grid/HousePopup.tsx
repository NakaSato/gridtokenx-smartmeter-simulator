import { Zap } from 'lucide-react';

interface HousePopupProps {
    house: { id: string; phase: string; gen: number; cons: number; volt: number };
    x: number;
    y: number;
    onClose?: () => void;
}

export const HousePopup = ({ house, x, y }: HousePopupProps) => {
    const net = house.gen - house.cons;
    return (
        <div
            className="absolute z-[1100] pointer-events-none"
            style={{ left: x + 12, top: y - 12 }}
        >
            <div className="glass px-3 py-2 rounded-lg shadow-xl min-w-[180px]">
                <div className="flex items-center gap-2 mb-1">
                    <Zap className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-xs font-bold text-white truncate">{house.id}</span>
                </div>
                <div className="text-[10px] text-slate-400">Phase {house.phase}</div>
                <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5">
                    <span className="text-slate-500">Gen</span>
                    <span className="text-right text-[10px] font-bold text-emerald-400">{house.gen.toFixed(2)} kWh</span>
                    <span className="text-slate-500">Cons</span>
                    <span className="text-right text-[10px] font-bold text-amber-400">{house.cons.toFixed(2)} kWh</span>
                    <span className="text-slate-500">Net</span>
                    <span className={`text-right text-[10px] font-bold ${net > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {net.toFixed(2)} kWh
                    </span>
                    <span className="text-slate-500">Volt</span>
                    <span className="text-right text-[10px] font-bold text-blue-400">{house.volt.toFixed(0)} V</span>
                </div>
            </div>
        </div>
    );
};
