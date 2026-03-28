import { useState } from 'react';
import { Sun, Cloud, Moon, CloudRain, Zap, Play, Pause, Wind } from 'lucide-react';

interface SimulationControlProps {
    currentWeather: string;
    currentStress: number;
    isPaused: boolean;
    onUpdateWeather: (mode: string) => void;
    onUpdateStress: (multiplier: number) => void;
    onTogglePause: () => void;
}

export const SimulationControl = ({
    currentWeather,
    currentStress,
    isPaused,
    onUpdateWeather,
    onUpdateStress,
    onTogglePause
}: SimulationControlProps) => {
    const [isExpanded, setIsExpanded] = useState(true);

    const weatherModes = [
        { id: 'Sunny', icon: Sun, label: 'Sunny', color: 'text-amber-400', bg: 'bg-amber-400/20' },
        { id: 'Cloudy', icon: Cloud, label: 'Cloudy', color: 'text-slate-400', bg: 'bg-slate-400/20' },
        { id: 'Eclipse', icon: Moon, label: 'Eclipse', color: 'text-indigo-400', bg: 'bg-indigo-400/20' },
        { id: 'Rainy', icon: CloudRain, label: 'Rainy', color: 'text-blue-400', bg: 'bg-blue-400/20' }
    ];

    return (
        <div className="absolute top-[104px] right-6 z-[1000] pointer-events-none">
            <div className={`pointer-events-auto glass rounded-3xl backdrop-blur-2xl border border-white/10 shadow-2xl transition-all duration-500 ease-in-out overflow-hidden ${isExpanded ? 'w-80' : 'w-14 h-14'}`}>
                {!isExpanded ? (
                    <button 
                        onClick={() => setIsExpanded(true)}
                        className="w-full h-full flex items-center justify-center text-indigo-400 hover:text-white transition-colors"
                    >
                        <Wind className="w-6 h-6" />
                    </button>
                ) : (
                    <div className="p-5 space-y-6">
                        {/* Header */}
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <div className="p-2 bg-indigo-500/20 rounded-xl">
                                    <Wind className="w-5 h-5 text-indigo-400" />
                                </div>
                                <h3 className="font-black text-white text-sm tracking-tight uppercase">Sim Dynamics</h3>
                            </div>
                            <button 
                                onClick={() => setIsExpanded(false)}
                                className="text-slate-500 hover:text-white transition-colors text-xs font-bold"
                            >
                                Minimize
                            </button>
                        </div>

                        {/* Weather Selection */}
                        <div className="space-y-3">
                            <div className="flex items-center justify-between px-1">
                                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Weather Engine</span>
                                <span className="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full">{currentWeather}</span>
                            </div>
                            <div className="grid grid-cols-4 gap-2">
                                {weatherModes.map((mode) => (
                                    <button
                                        key={mode.id}
                                        onClick={() => onUpdateWeather(mode.id)}
                                        className={`group relative flex flex-col items-center gap-2 p-3 rounded-2xl transition-all duration-300 ${
                                            currentWeather === mode.id 
                                                ? `${mode.bg} ring-1 ring-white/20 shadow-lg scale-105` 
                                                : 'bg-white/5 hover:bg-white/10 grayscale opacity-60 hover:grayscale-0 hover:opacity-100'
                                        }`}
                                    >
                                        <mode.icon className={`w-5 h-5 ${currentWeather === mode.id ? mode.color : 'text-slate-400 group-hover:text-white'}`} />
                                        <span className="text-[9px] font-black uppercase text-center text-slate-300">{mode.id}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Grid Stress Controller */}
                        <div className="space-y-3">
                            <div className="flex items-center justify-between px-1">
                                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Grid Stress</span>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                    currentStress > 1.5 ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
                                }`}>
                                    {currentStress.toFixed(1)}x LOAD
                                </span>
                            </div>
                            <div className="px-1 pt-2">
                                <input 
                                    type="range"
                                    min="1.0"
                                    max="2.0"
                                    step="0.1"
                                    value={currentStress}
                                    onChange={(e) => onUpdateStress(parseFloat(e.target.value))}
                                    className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                                />
                                <div className="flex justify-between mt-2 font-bold text-[8px] text-slate-600 uppercase">
                                    <span>Nominal</span>
                                    <span>Critical</span>
                                </div>
                            </div>
                        </div>

                        {/* Simulation Playback & Play/Pause */}
                        <div className="flex gap-2">
                            <button
                                onClick={onTogglePause}
                                className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl font-black text-[10px] uppercase tracking-widest shadow-lg transition-all active:scale-95 ${
                                    isPaused 
                                        ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-500/20' 
                                        : 'bg-rose-600/20 border border-rose-500/30 text-rose-400 hover:bg-rose-500/20'
                                }`}
                            >
                                {isPaused ? <Play className="w-4 h-4 fill-current" /> : <Pause className="w-4 h-4 fill-current" />}
                                {isPaused ? 'Resume Sim' : 'Pause Sim'}
                            </button>
                            
                            <div className="flex items-center justify-center p-3 aspect-square rounded-2xl bg-white/5 border border-white/10 text-slate-400">
                                <Zap className={`w-4 h-4 ${!isPaused ? 'text-amber-400 animate-pulse' : ''}`} />
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
