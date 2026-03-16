import { Activity } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface SearchFilterPanelProps {
    searchQuery: string;
    filterType: 'all' | 'producer' | 'consumer';
    onSearchChange: (query: string) => void;
    onFilterChange: (type: 'all' | 'producer' | 'consumer') => void;
}

export const SearchFilterPanel = ({
    searchQuery,
    filterType,
    onSearchChange,
    onFilterChange
}: SearchFilterPanelProps) => {
    return (
        <div className="absolute top-20 left-6 z-10 w-80 space-y-4">
            <div className="bg-slate-900/80 backdrop-blur-md border border-slate-700/50 rounded-xl p-3 shadow-2xl">
                <div className="relative">
                    <Activity className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                    <input
                        type="text"
                        placeholder="Find House #..."
                        className="w-full bg-slate-800/50 border border-slate-700 rounded-lg py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/50 text-slate-200"
                        value={searchQuery}
                        onChange={(e) => onSearchChange(e.target.value)}
                    />
                </div>
                <div className="flex gap-2 mt-3">
                    {(['all', 'producer', 'consumer'] as const).map(t => (
                        <button
                            key={t}
                            onClick={() => onFilterChange(t)}
                            className={cn(
                                "flex-1 py-1 px-2 rounded-md text-xs font-medium transition-all capitalize",
                                filterType === t
                                    ? "bg-orange-500 text-white shadow-lg shadow-orange-500/20"
                                    : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                            )}
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            <CommunityHealthCard />
        </div>
    );
};

interface CommunityHealthCardProps {
    selfSufficiency?: number;
    carbonOffset?: number;
}

export const CommunityHealthCard = ({ selfSufficiency = 0, carbonOffset = 0 }: CommunityHealthCardProps) => {
    return (
        <div className="bg-slate-900/80 backdrop-blur-md border border-slate-700/50 rounded-xl p-4 shadow-2xl">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Activity className="h-4 w-4 text-green-400" />
                Community Health
            </h3>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Self-Sufficiency</p>
                    <p className="text-xl font-bold text-green-400">{selfSufficiency.toFixed(0)}%</p>
                </div>
                <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Carbon Offset</p>
                    <p className="text-xl font-bold text-orange-400">{carbonOffset.toFixed(1)}t</p>
                </div>
            </div>
        </div>
    );
};
