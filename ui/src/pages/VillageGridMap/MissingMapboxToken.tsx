import { Zap } from 'lucide-react';
import { Link } from 'react-router-dom';

export const MissingMapboxToken = () => {
    return (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm">
            <div className="p-8 glass rounded-3xl border-white/10 max-w-md text-center">
                <Zap className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <h2 className="text-lg font-black text-white mb-2">Mapbox Token Required</h2>
                <p className="text-xs text-slate-400 leading-relaxed mb-6">
                    Set <code className="bg-white/10 px-1.5 py-0.5 rounded text-indigo-300">VITE_MAPBOX_ACCESS_TOKEN</code> in ui/.env
                </p>
                <Link to="/dashboard" className="px-6 py-3 bg-indigo-500 text-white text-xs font-black rounded-xl hover:bg-indigo-400 transition-all inline-block">
                    Back to Dashboard
                </Link>
            </div>
        </div>
    );
};
