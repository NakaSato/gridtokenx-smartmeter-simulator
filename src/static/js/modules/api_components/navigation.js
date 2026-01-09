import { setCurrentPage, getItemsPerPage, setViewMode, setCurrentPage as setPage, allReadings, getCurrentPage, getViewMode, setItemsPerPage } from '../state.js';
import { filterMeters } from './readings.js';

export function goToPage(page) {
    const totalItems = allReadings.length;
    const totalPages = Math.ceil(totalItems / getItemsPerPage());
    if (page >= 1 && page <= totalPages) {
        setCurrentPage(page);
        filterMeters();
    }
}

export function nextPage() {
    goToPage(getCurrentPage() + 1);
}

export function prevPage() {
    goToPage(getCurrentPage() - 1);
}

export function changeViewMode(mode) {
    setViewMode(mode);
    setCurrentPage(1); // Reset to first page on view change
    filterMeters();

    // Update button states
    const cardBtn = document.getElementById('view-card-btn');
    const listBtn = document.getElementById('view-list-btn');
    if (cardBtn && listBtn) {
        if (mode === 'card') {
            cardBtn.classList.add('bg-slate-700', 'text-white');
            cardBtn.classList.remove('text-slate-400');
            listBtn.classList.remove('bg-slate-700', 'text-white');
            listBtn.classList.add('text-slate-400');
        } else {
            listBtn.classList.add('bg-slate-700', 'text-white');
            listBtn.classList.remove('text-slate-400');
            cardBtn.classList.remove('bg-slate-700', 'text-white');
            cardBtn.classList.add('text-slate-400');
        }
    }
}

export function changeItemsPerPage(count) {
    setItemsPerPage(parseInt(count));
    filterMeters();
}
