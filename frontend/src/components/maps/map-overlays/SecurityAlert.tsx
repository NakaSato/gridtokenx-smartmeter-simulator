import { AlertTriangle, ShieldAlert, Activity } from 'lucide-react';

interface SecurityAlertProps {
    isUnderAttack: boolean;
    anomalyScore: number;
    compromisedCount: number;
}

export const SecurityAlert = ({ isUnderAttack, anomalyScore, compromisedCount }: SecurityAlertProps) => {
    if (!isUnderAttack && compromisedCount === 0) return null;

    return (
        <div className="absolute top-24 left-1/2 -translate-x-1/2 z-[1100] animate-in fade-in slide-in-from-top-4 duration-500">
            <div className={`
                glass-premium px-6 py-3 rounded-2xl border-2 flex items-center gap-4 shadow-2xl
                ${isUnderAttack 
                    ? 'border-rose-500/50 bg-rose-950/40 animate-pulse' 
                    : 'border-amber-500/50 bg-amber-950/40'}
            `}>
                <div className={`p-2 rounded-xl ${isUnderAttack ? 'bg-rose-500/20' : 'bg-amber-500/20'}`}>
                    {isUnderAttack ? (
                        <ShieldAlert className="w-5 h-5 text-rose-400" />
                    ) : (
                        <AlertTriangle className="w-5 h-5 text-amber-400" />
                    )}
                </div>

                <div className="flex flex-col">
                    <span className={`text-xs font-black tracking-widest uppercase ${isUnderAttack ? 'text-rose-400' : 'text-amber-400'}`}>
                        {isUnderAttack ? 'Cyber Attack Detected' : 'Anomalous Activity'}
                    </span>
                    <div className="flex items-center gap-2">
                        <span className="text-white font-bold text-sm">
                            {compromisedCount} node{compromisedCount !== 1 ? 's' : ''} compromised
                        </span>
                        <div className="w-1 h-1 rounded-full bg-white/20" />
                        <div className="flex items-center gap-1">
                            <Activity className="w-3 h-3 text-slate-400" />
                            <span className="text-[10px] font-bold text-slate-400">
                                Score: {(anomalyScore * 100).toFixed(1)}%
                            </span>
                        </div>
                    </div>
                </div>

                {isUnderAttack && (
                    <div className="ml-4 px-3 py-1 rounded-lg bg-rose-500/20 border border-rose-500/30">
                        <span className="text-[10px] font-black text-rose-400 animate-pulse">VPP SUSPENDED</span>
                    </div>
                )}
            </div>
        </div>
    );
};
