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
    const pageNumbers = useMemo(() =>
        Array.from({ length: totalPages }, (_, i) => i + 1),
        [totalPages]
    );

    if (totalPages <= 1) return null;

    return (
        <div className="flex items-center justify-between bg-[var(--panel)] p-4 border border-[var(--line)] mt-6">
            <div className="hmi-lbl">
                Showing <span className="mono text-[var(--txt-val)]">{startIndex}</span> - <span className="mono text-[var(--txt-val)]">{endIndex}</span> of <span className="mono text-[var(--txt-val)]">{totalItems}</span> Meters
            </div>
            <div className="flex items-center gap-2">
                <button
                    type="button"
                    onClick={onPrevPage}
                    disabled={currentPage === 1}
                    className="hmi-btn p-2"
                    aria-label="Previous page"
                >
                    <ChevronLeft className="w-4 h-4" />
                </button>

                <div className="flex items-center gap-1 px-2">
                    {pageNumbers.map(page => (
                        <button
                            type="button"
                            key={page}
                            onClick={() => onPageChange(page)}
                            className={cn(
                                "hmi-btn mono w-8 h-8 p-0",
                                currentPage === page && "active"
                            )}
                            aria-label={`Go to page ${page}`}
                            aria-current={currentPage === page ? 'page' : undefined}
                        >
                            {page}
                        </button>
                    ))}
                </div>

                <button
                    type="button"
                    onClick={onNextPage}
                    disabled={currentPage === totalPages}
                    className="hmi-btn p-2"
                    aria-label="Next page"
                >
                    <ChevronRight className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
});

Pagination.displayName = 'Pagination';
