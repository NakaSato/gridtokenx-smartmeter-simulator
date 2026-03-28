import { Link } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Layers, Zap, MapPin, Activity } from 'lucide-react';

interface MapHeaderProps {
    metersCount: number;
    isConnected: boolean;
    showZones: boolean;
    onToggleZones: () => void;
    onRefresh: () => void;
    carbonIntensity?: number;
    showHeatmap: boolean;
    onToggleHeatmap: () => void;
    heatmapMode: 'voltage' | 'congestion';
    onToggleHeatmapMode: () => void;
}

export const MapHeader = ({
    metersCount,
    isConnected,
    showZones,
    onToggleZones,
    onRefresh,
    carbonIntensity = 250,
    showHeatmap,
    onToggleHeatmap,
    heatmapMode,
    onToggleHeatmapMode
}: MapHeaderProps) => {
    
    // Carbon Status Logic
    const getCarbonStatus = (intensity: number) => {
        if (intensity < 150) return { label: 'CLEAN', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' };
        if (intensity < 350) return { label: 'MIXED', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' };
        return { label: 'DIRTY', color: 'bg-rose-500/10 text-rose-400 border-rose-500/20' };
    };

    const carbonStatus = getCarbonStatus(carbonIntensity);

    return (
        <div className="absolute top-0 left-0 right-0 z-[1000] p-4 flex justify-between items-start pointer-events-none">
            {/* Left Section - Title & Status */}
            <div className="pointer-events-auto flex items-center gap-3">
                <Link 
                    to="/dashboard" 
                    className="group glass p-3 rounded-xl hover:bg-white/15 transition-all duration-300 text-slate-300 hover:text-white hover:scale-105 active:scale-95 shadow-lg hover:shadow-emerald-500/20"
                >
                    <ArrowLeft className="w-5 h-5 group-hover:-translate-x-0.5 transition-transform" />
                </Link>
                
                <div className="glass px-5 py-3 rounded-2xl backdrop-blur-xl shadow-2xl border border-white/10">
                    <div className="flex items-center gap-2 mb-1.5">
                        <div className="p-1.5 bg-gradient-to-br from-emerald-500/20 to-emerald-600/20 rounded-lg">
                            <Activity className="w-4 h-4 text-emerald-400" />
                        </div>
                        <h1 className="text-lg font-black text-white tracking-tight">
                            Village Smart Meter Map
                        </h1>
                    </div>
                    
                    <div className="flex items-center gap-2.5 text-xs">
                        <div className="flex items-center gap-2 px-2.5 py-1 bg-emerald-500/10 rounded-full border border-emerald-500/20">
                            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.6)]' : 'bg-rose-500 animate-pulse shadow-[0_0_8px_rgba(244,63,94,0.6)]'}`} />
                            <span className={`font-bold ${isConnected ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {isConnected ? 'LIVE' : 'OFFLINE'}
                            </span>
                        </div>
                        
                        <div className={`flex items-center gap-2 px-2.5 py-1 rounded-full border transition-all duration-500 ${carbonStatus.color}`}>
                            <div className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                            <span className="font-black tracking-tighter">{carbonStatus.label} GRID</span>
                            <span className="opacity-40 font-bold ml-1">{Math.round(carbonIntensity)} g/kWh</span>
                        </div>

                        <span className="text-slate-400 font-semibold">{metersCount} houses</span>
                        <span className="text-slate-600">•</span>
                        <div className="flex items-center gap-1 text-slate-400">
                            <MapPin className="w-3 h-3" />
                            <span className="font-medium">Bangkok</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right Section - Actions */}
            <div className="pointer-events-auto flex gap-2">
                <button
                    onClick={onToggleHeatmap}
                    className={`group glass px-4 py-2.5 rounded-xl flex items-center gap-2 text-sm font-bold transition-all duration-300 shadow-lg hover:scale-105 active:scale-95 ${
                        showHeatmap 
                            ? 'bg-rose-500/25 text-rose-300 border-rose-500/60 shadow-rose-500/20' 
                            : 'text-slate-400 border-white/10 hover:border-white/30 hover:text-white'
                    }`}
                >
                    <Activity className={`w-4 h-4 ${showHeatmap ? 'animate-pulse text-rose-400' : ''}`} />
                    <span className="hidden sm:inline">{showHeatmap ? 'Hide Heatmap' : 'Show Heatmap'}</span>
                </button>

                {showHeatmap && (
                    <button
                        onClick={onToggleHeatmapMode}
                        className="group glass px-4 py-2.5 rounded-xl flex items-center gap-2 text-sm font-bold text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/25 border border-indigo-500/30 hover:border-indigo-500/50 transition-all duration-300 shadow-lg hover:shadow-indigo-500/20 hover:scale-105 active:scale-95 animate-in slide-in-from-right-4"
                    >
                        <Zap className="w-4 h-4" />
                        <span className="hidden sm:inline">Mode: {heatmapMode === 'voltage' ? 'Voltage' : 'Congestion'}</span>
                    </button>
                )}
                
                <button
                    onClick={onToggleZones}
                    className={`group glass px-4 py-2.5 rounded-xl flex items-center gap-2 text-sm font-bold transition-all duration-300 shadow-lg hover:scale-105 active:scale-95 ${
                        showZones 
                            ? 'bg-indigo-500/25 text-indigo-300 border-indigo-500/60 shadow-indigo-500/20' 
                            : 'text-slate-400 border-white/10 hover:border-white/30 hover:text-white'
                    }`}
                >
                    <Layers className={`w-4 h-4 ${showZones ? 'animate-pulse' : ''}`} />
                    <span className="hidden sm:inline">{showZones ? 'Hide Zone' : 'Show Zone'}</span>
                </button>
                
                <button
                    onClick={onRefresh}
                    className="group glass px-4 py-2.5 rounded-xl flex items-center gap-2 text-sm font-bold text-slate-400 hover:text-white hover:bg-white/15 border border-white/10 hover:border-white/30 transition-all duration-300 shadow-lg hover:shadow-white/10 hover:scale-105 active:scale-95"
                >
                    <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
                    <span className="hidden sm:inline">Refresh</span>
                </button>
            </div>
        </div>
    );
};
