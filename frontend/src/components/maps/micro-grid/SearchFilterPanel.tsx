"use client";

import { useState } from 'react';
import { Search, Filter } from 'lucide-react';

interface SearchFilterPanelProps {
    searchQuery: string;
    filterType: 'all' | 'producer' | 'consumer';
    onSearchChange: (q: string) => void;
    onFilterChange: (f: 'all' | 'producer' | 'consumer') => void;
}

export const SearchFilterPanel = ({ searchQuery, filterType, onSearchChange, onFilterChange }: SearchFilterPanelProps) => {
    const [open, setOpen] = useState(false);
    return (
        <div className="relative">
            <button onClick={() => setOpen(!open)} className="glass p-2 rounded-lg shadow-xl hover:bg-white/10 transition-all">
                {open ? <Filter className="w-4 h-4 text-white" /> : <Search className="w-4 h-4 text-white" />}
            </button>
            {open && (
                <div className="absolute bottom-10 right-0 glass p-3 rounded-xl shadow-2xl min-w-[200px] space-y-3">
                    <div>
                        <input
                            type="text"
                            placeholder="Search meters..."
                            value={searchQuery}
                            onChange={e => onSearchChange(e.target.value)}
                            className="w-full px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                        />
                    </div>
                    <div className="flex gap-1">
                        {(['all', 'producer', 'consumer'] as const).map(f => (
                            <button
                                key={f}
                                onClick={() => onFilterChange(f)}
                                className={`flex-1 px-2 py-1 rounded text-[10px] font-bold uppercase ${
                                    filterType === f ? 'bg-emerald-500/20 text-emerald-400' : 'text-slate-400 hover:bg-white/5'
                                }`}
                            >
                                {f}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
