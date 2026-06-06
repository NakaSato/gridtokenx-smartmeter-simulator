import { X } from 'lucide-react';
import type { SelectedNodeData } from '@/lib/topology/types';

interface SelectedNodePanelProps {
    node: SelectedNodeData | null;
    onClose: () => void;
}

export function SelectedNodePanel({ node, onClose }: SelectedNodePanelProps) {
    if (!node) return null;
    return (
        <div className="absolute bottom-6 right-6 z-20 glass px-5 py-4 rounded-xl border border-white/10 bg-slate-900/80 backdrop-blur-xl w-72">
            <div className="flex items-start justify-between gap-4">
                <div>
                    <div className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">{node.kind}</div>
                    <div className="text-sm font-black text-white break-all">{node.busName || node.label}</div>
                </div>
                <button onClick={onClose} className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 transition-all" aria-label="Close node panel"><X className="w-4 h-4" /></button>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
                <div>
                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Voltage</div>
                    <div className="text-sm font-black text-white">{(node.voltageV ?? 0).toFixed(1)} V</div>
                    {node.voltagePu !== undefined && <div className="text-[9px] font-bold text-slate-500">{node.voltagePu.toFixed(3)} pu</div>}
                </div>
                <div>
                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Load</div>
                    <div className="text-sm font-black text-white">{(node.loadKw ?? 0).toFixed(2)} kW</div>
                </div>
                <div>
                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Meters</div>
                    <div className="text-sm font-black text-white">{node.meterCount ?? 0}</div>
                </div>
                <div>
                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Generation</div>
                    <div className="text-sm font-black text-emerald-400">{(node.generationKw ?? 0).toFixed(2)} kW</div>
                </div>
                <div>
                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Consumption</div>
                    <div className="text-sm font-black text-rose-400">{(node.consumptionKw ?? 0).toFixed(2)} kW</div>
                </div>
            </div>
        </div>
    );
}
