export function GraphLegend() {
    return (
        <div className="absolute bottom-6 left-6 z-10 hmi-panel p-4 space-y-2.5">
            <div className="hmi-lbl">Node Type</div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 bg-[var(--warn)]" /><span className="hmi-lbl">Transformer</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 bg-[var(--info)]" /><span className="hmi-lbl">Feeder (MV)</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 bg-[var(--lbl)]" /><span className="hmi-lbl">Service Bus</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 bg-[var(--lbl)] ring-1 ring-[var(--ok)]" /><span className="hmi-lbl">Has Solar (PV)</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 bg-[var(--info)] ring-1 ring-[var(--warn)]" /><span className="hmi-lbl">BESS (Storage)</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 bg-[var(--warn)] ring-1 ring-[var(--lbl)]" /><span className="hmi-lbl">EV Charger</span></div>
            <div className="h-px bg-[var(--line)] w-full" />
            <div className="hmi-lbl">Voltage State</div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 bg-[var(--ok)]" /><span className="hmi-lbl">Nominal</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 bg-[var(--info)]" /><span className="hmi-lbl">Under Voltage</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 bg-[var(--alarm)]" /><span className="hmi-lbl">Over Voltage</span></div>
            <div className="h-px bg-[var(--line)] w-full" />
            <div className="hmi-lbl">Line Loading</div>
            <div className="flex items-center gap-3"><div className="w-4 h-1 bg-[var(--warn)]" /><span className="hmi-lbl">Loaded (&gt;40%)</span></div>
            <div className="flex items-center gap-3"><div className="w-4 h-1 bg-[var(--alarm)]" /><span className="hmi-lbl">Congested (&gt;80%)</span></div>
        </div>
    );
}
