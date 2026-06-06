import type { GraphTooltipState } from '@/lib/topology/types';

export function GraphTooltip({ tooltip }: { tooltip: GraphTooltipState | null }) {
    if (!tooltip) return null;
    return (
        <div
            className="pointer-events-none fixed z-50 max-w-xs whitespace-pre-line rounded-lg border border-white/10 bg-slate-900/95 px-3 py-2 text-[11px] font-bold text-slate-200 shadow-xl backdrop-blur-md"
            style={{ left: tooltip.x + 14, top: tooltip.y + 14 }}
        >
            {tooltip.text}
        </div>
    );
}
