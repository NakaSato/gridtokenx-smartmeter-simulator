export function GraphLegend() {
    return (
        <div className="absolute bottom-6 left-6 z-10 glass p-4 rounded-xl space-y-2.5">
            <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Node Type</div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 rounded bg-amber-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Transformer</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-indigo-400" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Feeder (MV)</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-sky-400" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Service Bus</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-sky-400 ring-2 ring-emerald-400" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Has Solar (PV)</span></div>
            <div className="h-px bg-white/10 w-full" />
            <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Voltage State</div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-green-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Nominal</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-blue-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Under Voltage</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-red-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Over Voltage</span></div>
            <div className="h-px bg-white/10 w-full" />
            <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Line Loading</div>
            <div className="flex items-center gap-3"><div className="w-4 h-1 bg-amber-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Loaded (&gt;40%)</span></div>
            <div className="flex items-center gap-3"><div className="w-4 h-1 bg-red-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Congested (&gt;80%)</span></div>
        </div>
    );
}
