import { allReadings, updateReading, previousStats, setPreviousStats, getCurrentPage, getItemsPerPage, getViewMode } from '../state.js';
import { updateCharts } from '../chart.js';
import { createMeterCard, createMeterRow, updateMeterCardContent } from '../ui.js';

export function updateReadings(newReadings) {
    // Merge new readings into global state
    newReadings.forEach(newReading => {
        updateReading(newReading);
    });

    // Update statistics
    let totalGen = 0, totalCons = 0, totalSurp = 0, activeTraders = 0;

    allReadings.forEach(r => {
        // Use energy_generated (kWh) to match card display
        const gen = parseFloat(r.energy_generated || 0);
        const cons = parseFloat(r.energy_consumed || 0);

        totalGen += gen;
        totalCons += cons;
        totalSurp += parseFloat(r.surplus_energy || 0);
        if ((r.surplus_energy || 0) > 0 || (r.deficit_energy || 0) > 0) {
            activeTraders++;
        }
    });

    // Animate values
    animateValue('total-generation', parseFloat(document.getElementById('total-generation').textContent), totalGen);
    animateValue('total-consumption', parseFloat(document.getElementById('total-consumption').textContent), totalCons);
    animateValue('total-surplus', parseFloat(document.getElementById('total-surplus').textContent), totalSurp);
    animateValue('active-traders', parseInt(document.getElementById('active-traders').textContent), activeTraders);

    // Update trends
    updateTrend('gen-trend', 'gen-change', totalGen, previousStats.gen);
    updateTrend('cons-trend', 'cons-change', totalCons, previousStats.cons);
    updateTrend('surplus-trend', 'surplus-change', totalSurp, previousStats.surplus);
    updateTrend('traders-trend', 'traders-change', activeTraders, previousStats.traders, false);

    setPreviousStats({ gen: totalGen, cons: totalCons, surplus: totalSurp, traders: activeTraders });

    // Prepare market prices
    let sellPrice = 0;
    let buyPrice = 0;

    if (newReadings.length > 0) {
        const sample = newReadings[0];
        sellPrice = parseFloat(sample.max_sell_price || 0);
        buyPrice = parseFloat(sample.max_buy_price || 0);
    }

    // Update charts with combined data
    updateCharts({
        total_generation: totalGen,
        total_consumption: totalCons,
        market_prices: {
            sell: sellPrice,
            buy: buyPrice
        }
    });

    // Update weather
    if (newReadings.length > 0) {
        document.getElementById('current-weather').textContent = newReadings[0].weather_condition || '-';
    }

    // Update counts
    document.getElementById('total-count').textContent = allReadings.length;

    // Apply filters
    filterMeters();
}

function animateValue(id, start, end) {
    const element = document.getElementById(id);
    const duration = 500;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        const current = start + (end - start) * progress;
        element.textContent = id === 'active-traders' ? Math.round(current) : current.toFixed(2);

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            // Ensure exact final value
            element.textContent = id === 'active-traders' ? Math.round(end) : end.toFixed(2);
        }
    }

    requestAnimationFrame(update);
}

function updateTrend(trendId, changeId, current, previous, isDecimal = true) {
    const trendEl = document.getElementById(trendId);
    const changeEl = document.getElementById(changeId);

    const change = current - previous;
    const percentChange = previous > 0 ? ((change / previous) * 100) : 0;

    if (change > 0) {
        trendEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline-block mr-1"><path d="m5 12 7-7 7 7"/><path d="M12 19V5"/></svg>${Math.abs(percentChange).toFixed(1)}%`;
        trendEl.className = 'text-xs font-semibold px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/20 flex items-center';
        changeEl.textContent = `+${isDecimal ? change.toFixed(2) : change}`;
        changeEl.className = 'text-xs text-emerald-400 font-semibold';
    } else if (change < 0) {
        trendEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline-block mr-1"><path d="M12 5v14"/><path d="m19 12-7 7-7-7"/></svg>${Math.abs(percentChange).toFixed(1)}%`;
        trendEl.className = 'text-xs font-semibold px-2 py-1 bg-red-500/10 text-red-400 rounded-full border border-red-500/20 flex items-center';
        changeEl.textContent = `${isDecimal ? change.toFixed(2) : change}`;
        changeEl.className = 'text-xs text-red-400 font-semibold';
    } else {
        trendEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline-block mr-1"><path d="M5 12h14"/></svg>0%`;
        trendEl.className = 'text-xs font-semibold px-2 py-1 bg-slate-700/50 text-slate-400 rounded-full border border-slate-600/50 flex items-center';
        changeEl.textContent = isDecimal ? '0.00' : '0';
        changeEl.className = 'text-xs text-slate-500 font-semibold';
    }
}

export function filterMeters() {
    const searchTerm = document.getElementById('meter-search').value.toLowerCase();
    const typeFilter = document.getElementById('meter-type-filter').value;
    const statusFilter = document.getElementById('meter-status-filter').value;
    const container = document.getElementById('readings-container');
    const viewMode = getViewMode();
    const currentPage = getCurrentPage();
    const itemsPerPage = getItemsPerPage();

    const filteredReadings = allReadings.filter(reading => {
        const matchesSearch = !searchTerm ||
            reading.meter_id.toLowerCase().includes(searchTerm) ||
            (reading.location && reading.location.toLowerCase().includes(searchTerm));

        const matchesType = !typeFilter || reading.meter_type === typeFilter;

        let matchesStatus = true;
        if (statusFilter === 'selling') {
            matchesStatus = (reading.surplus_energy || 0) > 0;
        } else if (statusFilter === 'buying') {
            matchesStatus = (reading.deficit_energy || 0) > 0;
        } else if (statusFilter === 'idle') {
            matchesStatus = (reading.surplus_energy || 0) === 0 && (reading.deficit_energy || 0) === 0;
        }

        return matchesSearch && matchesType && matchesStatus;
    });

    // Pagination
    const totalItems = filteredReadings.length;
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedReadings = filteredReadings.slice(startIndex, endIndex);

    document.getElementById('filtered-count').textContent = totalItems;

    // Update pagination info
    const paginationInfo = document.getElementById('pagination-info');
    if (paginationInfo) {
        paginationInfo.innerHTML = `Page ${currentPage} of ${totalPages || 1} (${startIndex + 1}-${Math.min(endIndex, totalItems)} of ${totalItems})`;
    }

    // Update pagination buttons
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;

    if (filteredReadings.length === 0) {
        container.innerHTML = '<div class="col-span-full text-center text-gray-500 py-8">No meters match your filters</div>';
        return;
    }

    // Render based on view mode
    if (viewMode === 'list') {
        container.className = 'w-full';
        container.innerHTML = `
            <table class="w-full text-left">
                <thead class="border-b border-slate-700">
                    <tr class="text-[10px] uppercase tracking-wider text-slate-500">
                        <th class="px-3 py-2 font-medium">Type</th>
                        <th class="px-3 py-2 font-medium">Meter ID</th>
                        <th class="px-3 py-2 font-medium text-right">Gen</th>
                        <th class="px-3 py-2 font-medium text-right">Use</th>
                        <th class="px-3 py-2 font-medium">Battery</th>
                        <th class="px-3 py-2 font-medium text-center">Status</th>
                        <th class="px-3 py-2 font-medium text-right"></th>
                    </tr>
                </thead>
                <tbody id="meter-table-body">
                    ${paginatedReadings.map(r => createMeterRow(r)).join('')}
                </tbody>
            </table>
        `;
    } else {
        container.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4';

        // For card view, we do incremental updates for better performance
        const existingIds = new Set(Array.from(container.children).map(c => c.id.replace('card-', '')));
        const paginatedIds = new Set(paginatedReadings.map(r => r.meter_id));

        // Remove cards not in current page
        Array.from(container.children).forEach(child => {
            const id = child.id.replace('card-', '');
            if (!paginatedIds.has(id)) {
                child.remove();
            }
        });

        paginatedReadings.forEach(reading => {
            const cardId = `card-${reading.meter_id}`;
            const existingCard = document.getElementById(cardId);

            if (existingCard) {
                updateMeterCardContent(existingCard, reading);
            } else {
                const cardHtml = createMeterCard(reading);
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = cardHtml.trim();
                container.appendChild(tempDiv.firstChild);
            }
        });
    }
}
