import { Zap } from 'lucide-react';

export function GraphLoadingState({ error }: { error: string | null }) {
    return (
        <div className="absolute inset-0 flex items-center justify-center text-white">
            <div className="text-center px-6">
                <Zap className="w-12 h-12 text-amber-500 mx-auto mb-4 animate-pulse" />
                <h2 className="text-xl font-black mb-2">{error ? 'Network Graph Unavailable' : 'Loading Network Graph'}</h2>
                <p className="text-slate-400 text-sm">{error || 'Building node-link diagram from the simulator topology...'}</p>
            </div>
        </div>
    );
}
