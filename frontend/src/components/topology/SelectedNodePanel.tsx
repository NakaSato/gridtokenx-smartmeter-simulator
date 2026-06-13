import { X } from 'lucide-react';
import type { SelectedNodeData } from '@/lib/topology/types';

interface SelectedNodePanelProps {
    node: SelectedNodeData | null;
    onClose: () => void;
}

export function SelectedNodePanel({ node, onClose }: SelectedNodePanelProps) {
    if (!node) return null;
    return (
        <div className="absolute bottom-6 right-6 z-20 hmi-panel w-72">
            <div className="hmi-panel-hd">
                <div>
                    <div className="hmi-lbl mb-1">{node.kind}</div>
                    <div className="text-sm font-semibold text-[var(--txt-val)] break-all">{node.busName || node.label}</div>
                </div>
                <button type="button" onClick={onClose} className="hmi-btn p-1.5" aria-label="Close node panel"><X className="w-4 h-4" /></button>
            </div>
            <div className="hmi-panel-bd grid grid-cols-2 gap-3">
                <div>
                    <div className="hmi-lbl">Voltage</div>
                    <div className="mono text-sm font-semibold text-[var(--txt-val)]">{(node.voltageV ?? 0).toFixed(1)} V</div>
                    {node.voltagePu !== undefined && <div className="mono text-[9px] text-[var(--lbl-dim)]">{node.voltagePu.toFixed(3)} pu</div>}
                </div>
                <div>
                    <div className="hmi-lbl">Load</div>
                    <div className="mono text-sm font-semibold text-[var(--txt-val)]">{(node.loadKw ?? 0).toFixed(2)} kW</div>
                </div>
                <div>
                    <div className="hmi-lbl">Meters</div>
                    <div className="mono text-sm font-semibold text-[var(--txt-val)]">{node.meterCount ?? 0}</div>
                </div>
                <div>
                    <div className="hmi-lbl">Generation</div>
                    <div className="mono text-sm font-semibold text-[var(--gen)]">{(node.generationKw ?? 0).toFixed(2)} kW</div>
                </div>
                <div>
                    <div className="hmi-lbl">Consumption</div>
                    <div className="mono text-sm font-semibold text-[var(--cons)]">{(node.consumptionKw ?? 0).toFixed(2)} kW</div>
                </div>
            </div>
        </div>
    );
}
