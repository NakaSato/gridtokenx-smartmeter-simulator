import { RotateCcw } from 'lucide-react';

interface GraphZoomControlsProps {
    scale: number;
    onReset: () => void;
    onZoom: (level: number) => void;
}

export function GraphZoomControls({ scale, onReset, onZoom }: GraphZoomControlsProps) {
    return (
        <div className="absolute top-24 left-6 z-10 flex items-center gap-2">
            <button
                type="button"
                onClick={onReset}
                className="hmi-btn p-3"
                aria-label="Reset graph view"
                title="Reset graph view"
            >
                <RotateCcw className="w-5 h-5" />
            </button>
            <div className="flex items-center bg-[var(--panel)] border border-[var(--line)] overflow-hidden">
                <button
                    type="button"
                    onClick={() => onZoom(scale - 0.1)}
                    className="px-3 py-2 text-sm font-semibold text-[var(--txt)] hover:bg-[var(--hover)]"
                    aria-label="Zoom out"
                >
                    -
                </button>
                <div className="mono w-14 text-center text-xs text-[var(--lbl)]">{Math.round(scale * 100)}%</div>
                <button
                    type="button"
                    onClick={() => onZoom(scale + 0.1)}
                    className="px-3 py-2 text-sm font-semibold text-[var(--txt)] hover:bg-[var(--hover)]"
                    aria-label="Zoom in"
                >
                    +
                </button>
            </div>
        </div>
    );
}
