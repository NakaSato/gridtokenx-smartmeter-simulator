"use client";

import { useMemo, memo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/common';

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    startIndex: number;
    endIndex: number;
    totalItems: number;
    onPageChange: (page: number) => void;
    onPrevPage: () => void;
    onNextPage: () => void;
}

export const Pagination = memo(({
    currentPage,
    totalPages,
    startIndex,
    endIndex,
    totalItems,
    onPageChange,
    onPrevPage,
    onNextPage
}: PaginationProps) => {
    if (totalPages <= 1) return null;

    const pageNumbers = useMemo(() =>
        Array.from({ length: totalPages }, (_, i) => i + 1),
        [totalPages]
    );

    return (
        <div className="flex items-center justify-between bg-slate-900/50 p-4 rounded-2xl border border-white/5 mt-6">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                Showing <span className="text-slate-300">{startIndex}</span> - <span className="text-slate-300">{endIndex}</span> of <span className="text-slate-300">{totalItems}</span> Meters
            </div>
            <div className="flex items-center gap-2">
                <button
                    onClick={onPrevPage}
                    disabled={currentPage === 1}
                    className="p-2 bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-white/5 rounded-xl transition-all active:scale-95"
                    aria-label="Previous page"
                >
                    <ChevronLeft className="w-4 h-4 text-slate-300" />
                </button>

                <div className="flex items-center gap-1 px-2">
                    {pageNumbers.map(page => (
                        <button
                            key={page}
                            onClick={() => onPageChange(page)}
                            className={cn(
                                "w-8 h-8 rounded-lg text-[10px] font-black transition-all",
                                currentPage === page
                                    ? "bg-emerald-500 text-slate-900 shadow-lg shadow-emerald-500/20"
                                    : "hover:bg-white/10 text-slate-400"
                            )}
                            aria-label={`Go to page ${page}`}
                            aria-current={currentPage === page ? 'page' : undefined}
                        >
                            {page}
                        </button>
                    ))}
                </div>

                <button
                    onClick={onNextPage}
                    disabled={currentPage === totalPages}
                    className="p-2 bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-white/5 rounded-xl transition-all active:scale-95"
                    aria-label="Next page"
                >
                    <ChevronRight className="w-4 h-4 text-slate-300" />
                </button>
            </div>
        </div>
    );
});

Pagination.displayName = 'Pagination';
