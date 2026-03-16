import { MapPin, Clock, Shield } from 'lucide-react';

interface MapInfoCardProps {
    metersCount: number;
}

export const MapInfoCard = ({ metersCount }: MapInfoCardProps) => {
    return (
        <div className="absolute bottom-6 left-6 z-[1000] glass p-5 rounded-2xl border-white/10 bg-slate-900/60 backdrop-blur-xl max-w-xs shadow-2xl animate-in fade-in slide-in-from-left-4 duration-500">
            <div className="flex items-start gap-3">
                <div className="p-2.5 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-xl shadow-lg shadow-indigo-500/20">
                    <MapPin className="w-5 h-5 text-indigo-400" />
                </div>
                <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-black text-white mb-1 tracking-tight">Village Microgrid</h4>
                    <p className="text-xs text-slate-400 leading-relaxed mb-3">
                        Real-time monitoring of {metersCount} smart meters in Bangkok village with solar generation and P2P trading.
                    </p>
                    
                    <div className="flex items-center gap-3 pt-3 border-t border-white/10">
                        <div className="flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5 text-slate-500" />
                            <span className="text-[10px] font-bold text-slate-400">Real-time</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <Shield className="w-3.5 h-3.5 text-slate-500" />
                            <span className="text-[10px] font-bold text-slate-400">Signed</span>
                        </div>
                        <div className="flex-1" />
                        <span className="text-[10px] font-black text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20">
                            AMI Enabled
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};
