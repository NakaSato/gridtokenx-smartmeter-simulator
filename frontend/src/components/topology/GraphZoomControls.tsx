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
                className="p-3 rounded-xl bg-slate-900/70 hover:bg-slate-800/90 border border-white/10 text-slate-300 transition-all backdrop-blur-xl"
                aria-label="Reset graph view"
                title="Reset graph view"
            >
                <RotateCcw className="w-5 h-5" />
            </button>
            <div className="flex items-center rounded-xl bg-slate-900/70 border border-white/10 backdrop-blur-xl overflow-hidden">
                <button
                    type="button"
                    onClick={() => onZoom(scale - 0.1)}
                    className="px-3 py-2 text-sm font-black text-slate-300 hover:bg-white/10"
                    aria-label="Zoom out"
                >
                    -
                </button>
                <div className="w-14 text-center text-xs font-black text-slate-400">{Math.round(scale * 100)}%</div>
                <button
                    type="button"
                    onClick={() => onZoom(scale + 0.1)}
                    className="px-3 py-2 text-sm font-black text-slate-300 hover:bg-white/10"
                    aria-label="Zoom in"
                >
                    +
                </button>
            </div>
        </div>
    );
}
