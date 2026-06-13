import type { GraphTooltipState } from '@/lib/topology/types';

export function GraphTooltip({ tooltip }: { tooltip: GraphTooltipState | null }) {
    if (!tooltip) return null;
    return (
        <div
            className="mono pointer-events-none fixed z-50 max-w-xs whitespace-pre-line border border-[var(--line)] bg-[var(--panel)] px-3 py-2 text-[11px] text-[var(--txt)]"
            style={{ left: tooltip.x + 14, top: tooltip.y + 14 }}
        >
            {tooltip.text}
        </div>
    );
}
