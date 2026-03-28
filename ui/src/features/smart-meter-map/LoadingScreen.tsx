import { Zap } from 'lucide-react';

export const LoadingScreen = () => {
    return (
        <div className="h-screen w-full flex items-center justify-center bg-slate-950 text-white">
            <div className="text-center">
                <Zap className="w-12 h-12 text-amber-500 mx-auto mb-4 animate-pulse" />
                <h2 className="text-xl font-black mb-2">Loading Village Map</h2>
                <p className="text-slate-400 text-sm">Fetching meter data...</p>
            </div>
        </div>
    );
};
