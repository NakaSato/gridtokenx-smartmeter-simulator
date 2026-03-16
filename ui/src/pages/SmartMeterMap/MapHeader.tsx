import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Layers, Zap, MapPin, Activity } from 'lucide-react';

interface MapHeaderProps {
    metersCount: number;
    isConnected: boolean;
    showZones: boolean;
    onToggleZones: () => void;
    onRefresh: () => void;
}

export const MapHeader = ({
    metersCount,
    isConnected,
    showZones,
    onToggleZones,
    onRefresh
}: MapHeaderProps) => {
    const navigate = useNavigate();

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
                    onClick={() => navigate('/grid-map')}
                    className="group glass px-4 py-2.5 rounded-xl flex items-center gap-2 text-sm font-bold text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/25 border border-indigo-500/30 hover:border-indigo-500/50 transition-all duration-300 shadow-lg hover:shadow-indigo-500/20 hover:scale-105 active:scale-95"
                >
                    <Zap className="w-4 h-4 group-hover:fill-indigo-400/20 transition-all" />
                    <span className="hidden sm:inline">Advanced View</span>
                </button>
                
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
