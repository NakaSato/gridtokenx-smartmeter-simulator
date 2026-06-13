import { Zap } from 'lucide-react';

export function GraphLoadingState({ error }: { error: string | null }) {
    return (
        <div className="absolute inset-0 flex items-center justify-center text-[var(--txt)]">
            <div className="text-center px-6">
                <Zap className={`w-12 h-12 mx-auto mb-4 ${error ? 'text-[var(--alarm)]' : 'text-[var(--warn)] animate-pulse'}`} />
                <h2 className="text-xl font-semibold mb-2 text-[var(--txt-val)]">{error ? 'Network Graph Unavailable' : 'Loading Network Graph'}</h2>
                <p className="text-[var(--lbl)] text-sm">{error || 'Building node-link diagram from the simulator topology...'}</p>
            </div>
        </div>
    );
}
