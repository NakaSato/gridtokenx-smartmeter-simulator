// Import Lucide icons
import { createIcons, icons } from 'lucide';

// UI Logic
import { addConsoleMessage } from './console.js';
import { updateChartTheme } from './chart.js';
import { allReadings, isMeterLive } from './state.js';

/**
 * Initialize Lucide icons in the DOM
 * Should be called after DOM updates that add new icons
 */
export function initLucideIcons() {
    createIcons({ icons });
}

// Dark Mode - Force Dark
export function toggleDarkMode() {
    document.documentElement.classList.add('dark');
    updateChartTheme(true);
}

export function initDarkMode() {
    document.documentElement.classList.add('dark');
    updateChartTheme(true);
}

// Status Message
export function showStatusMessage(message, type = 'info') {
    const messageEl = document.getElementById('status-message');
    const textEl = document.getElementById('status-message-text');
    const colors = {
        'success': 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
        'error': 'bg-red-500/20 text-red-400 border border-red-500/30',
        'warning': 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
        'info': 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
    };

    // Reset classes
    messageEl.className = `hidden ml-auto flex items-center gap-3 px-3 py-1 rounded-lg text-sm transition-all`;

    // Add new classes
    messageEl.classList.add(...colors[type].split(' '));
    messageEl.classList.remove('hidden');

    if (textEl) textEl.textContent = message;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageEl.classList.add('hidden');
    }, 5000);
}

// Button States
export function updateButtonStates(status) {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const pauseBtn = document.getElementById('pause-btn');
    const resumeBtn = document.getElementById('resume-btn');
    const updateBtn = document.getElementById('update-meters-btn');
    const meterCountInput = document.getElementById('meter-count');

    if (status.running) {
        // Running state
        if (startBtn) startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;
        if (updateBtn) updateBtn.disabled = true;
        if (meterCountInput) meterCountInput.disabled = true;

        if (status.paused) {
            // Paused state
            if (pauseBtn) {
                pauseBtn.disabled = true;
                pauseBtn.classList.add('hidden');
            }
            if (resumeBtn) {
                resumeBtn.disabled = false;
                resumeBtn.classList.remove('hidden');
            }
        } else {
            // Normal running state
            if (pauseBtn) {
                pauseBtn.disabled = false;
                pauseBtn.classList.remove('hidden');
            }
            if (resumeBtn) {
                resumeBtn.disabled = true;
                resumeBtn.classList.add('hidden');
            }
        }
    } else {
        // Stopped state
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
        if (pauseBtn) {
            pauseBtn.disabled = true;
            pauseBtn.classList.add('hidden');
        }
        if (resumeBtn) {
            resumeBtn.disabled = true;
            resumeBtn.classList.add('hidden');
        }
        if (updateBtn) updateBtn.disabled = false;
        if (meterCountInput) meterCountInput.disabled = false;
    }

    // Update meter count display
    if (status.num_meters && meterCountInput) {
        meterCountInput.value = status.num_meters;
    }
}

// Meter Cards
export function createMeterCard(reading, prefix = '') {
    const isSelling = (reading.surplus_energy || 0) > 0;
    const isBuying = (reading.deficit_energy || 0) > 0;
    const isLive = isMeterLive(reading.meter_id);

    // Meter type styling
    const meterTypeStyles = {
        'Solar_Prosumer': { bg: 'bg-amber-500/10', text: 'text-amber-400', label: 'Solar' },
        'Grid_Consumer': { bg: 'bg-blue-500/10', text: 'text-blue-400', label: 'Consumer' },
        'Hybrid_Prosumer': { bg: 'bg-purple-500/10', text: 'text-purple-400', label: 'Hybrid' },
        'Battery_Storage': { bg: 'bg-emerald-500/10', text: 'text-emerald-400', label: 'Storage' },
    };
    const meterStyle = meterTypeStyles[reading.meter_type] || meterTypeStyles['Grid_Consumer'];

    return `
        <article class="w-full rounded-xl border border-border/50 bg-card shadow-lg p-5 space-y-4 hover:border-primary/30 transition-colors" id="${prefix}card-${reading.meter_id}">
            <!-- Header -->
            <header class="flex items-start justify-between gap-3">
                <div class="flex items-center gap-3 min-w-0">
                    <div class="min-w-0 space-y-1">
                        <div class="flex items-center gap-2 flex-wrap">
                            <h2 class="text-base font-semibold text-foreground truncate max-w-[160px]" title="${reading.location}">${reading.location}</h2>
                            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide ${meterStyle.bg} ${meterStyle.text}">
                                ${meterStyle.label}
                            </span>
                        </div>
                        <p class="font-mono text-xs text-muted-foreground leading-tight truncate max-w-[200px]" title="${reading.meter_id}">${reading.meter_id.substring(0, 8)}...</p>
                    </div>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                    <span class="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium ${isLive ? 'bg-emerald-500/15 text-emerald-400' : 'bg-slate-500/15 text-slate-400'}">
                        <span class="h-1.5 w-1.5 rounded-full ${isLive ? 'bg-emerald-500 animate-pulse' : 'bg-slate-500'}"></span>
                        ${isLive ? 'LIVE' : 'IDLE'}
                    </span>
                    <button onclick="window.openMeterDetails('${reading.meter_id}')" class="p-1.5 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-md transition-colors" title="View Details">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                        </svg>
                    </button>
                </div>
            </header>

            <!-- Auto Mode Display -->
            <div id="${prefix}auto-${reading.meter_id}" class="space-y-4">
                <!-- Energy Stats Grid -->
                <div class="grid grid-cols-2 gap-3">
                    <!-- Generation - Amber/Green theme -->
                    <article class="rounded-lg bg-gradient-to-br from-amber-500/10 to-emerald-500/5 p-3.5 border border-amber-500/20">
                        <div class="flex items-center gap-2 mb-2">
                            <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/20">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-amber-400">
                                    <circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>
                                </svg>
                            </div>
                            <span class="text-xs font-medium text-amber-400 uppercase tracking-wide">Generation</span>
                        </div>
                        <p class="flex items-baseline gap-1">
                            <span class="text-2xl font-bold tracking-tight text-foreground tabular-nums val-gen">${(reading.energy_generated || 0).toFixed(2)}</span>
                            <span class="text-xs font-medium text-muted-foreground">kWh</span>
                        </p>
                    </article>

                    <!-- Consumption - Blue/Cyan theme -->
                    <article class="rounded-lg bg-gradient-to-br from-blue-500/10 to-cyan-500/5 p-3.5 border border-blue-500/20">
                        <div class="flex items-center gap-2 mb-2">
                            <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/20">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-blue-400">
                                    <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>
                                </svg>
                            </div>
                            <span class="text-xs font-medium text-blue-400 uppercase tracking-wide">Consumption</span>
                        </div>
                        <p class="flex items-baseline gap-1">
                            <span class="text-2xl font-bold tracking-tight text-foreground tabular-nums val-cons">${(reading.energy_consumed || 0).toFixed(2)}</span>
                            <span class="text-xs font-medium text-muted-foreground">kWh</span>
                        </p>
                    </article>
                </div>

                <!-- Battery Section -->
                <section class="space-y-2">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-muted-foreground">
                                <rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><line x1="22" x2="22" y1="11" y2="13"/>
                            </svg>
                            <span class="text-xs font-medium text-muted-foreground uppercase tracking-wide">Battery</span>
                        </div>
                        <span class="text-sm font-semibold tabular-nums text-foreground val-batt-text">${(reading.battery_level || 0).toFixed(1)}%</span>
                    </div>
                    <div class="h-2 w-full rounded-full bg-secondary overflow-hidden">
                        <div class="h-full rounded-full bg-gradient-to-r from-primary to-success transition-all duration-500 val-batt-bar" style="width: ${Math.max(reading.battery_level || 0, 2)}%"></div>
                    </div>
                </section>

                <!-- Metrics Row -->
                <div class="flex items-center justify-between py-2 border-y border-border/50">
                    <div class="flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-orange-500">
                            <path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>
                        </svg>
                        <span class="text-sm font-medium tabular-nums text-foreground val-temp">${(reading.temperature || 0).toFixed(1)}°C</span>
                    </div>
                    <div class="h-4 w-px bg-border"></div>
                    <div class="flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-success">
                            <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
                        </svg>
                        <span class="text-sm font-medium tabular-nums text-foreground val-emission">${(reading.net_emission || 0).toFixed(3)} kg</span>
                    </div>
                </div>

                <!-- Status Banners with Fixed Arrows -->
                <div class="status-container">
                    ${isSelling ? `
                        <section class="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-3">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2.5">
                                    <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/20">
                                        <!-- UP arrow - energy going OUT to grid -->
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-emerald-400">
                                            <path d="M12 19V5"/><path d="m5 12 7-7 7 7"/>
                                        </svg>
                                    </div>
                                    <span class="font-medium text-emerald-400 text-sm">Selling</span>
                                </div>
                                <p class="text-right">
                                    <span class="text-base font-bold tabular-nums text-foreground">${(reading.surplus_energy || 0).toFixed(2)}</span>
                                    <span class="text-xs text-muted-foreground"> kWh</span>
                                    <span class="text-muted-foreground"> @ </span>
                                    <span class="text-base font-bold text-emerald-400">$${(reading.max_sell_price || 0).toFixed(2)}</span>
                                </p>
                            </div>
                        </section>
                    ` : ''}
                    ${isBuying ? `
                        <section class="rounded-lg bg-orange-500/10 border border-orange-500/20 p-3">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2.5">
                                    <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-500/20">
                                        <!-- DOWN arrow - energy coming IN from grid -->
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-orange-400">
                                            <path d="M12 5v14"/><path d="m19 12-7 7-7-7"/>
                                        </svg>
                                    </div>
                                    <span class="font-medium text-orange-400 text-sm">Buying</span>
                                </div>
                                <p class="text-right">
                                    <span class="text-base font-bold tabular-nums text-foreground">${(reading.deficit_energy || 0).toFixed(2)}</span>
                                    <span class="text-xs text-muted-foreground"> kWh</span>
                                    <span class="text-muted-foreground"> @ </span>
                                    <span class="text-base font-bold text-orange-400">$${(reading.max_buy_price || 0).toFixed(2)}</span>
                                </p>
                            </div>
                        </section>
                    ` : ''}
                    ${!isSelling && !isBuying ? `
                        <div class="w-full text-sm text-muted-foreground text-center italic py-3 border border-border/50 rounded-lg bg-secondary/20">
                            System Balanced
                        </div>
                    ` : ''}
                </div>
            </div>

            <!-- Manual Mode Controls (Hidden by default) -->
            <div id="${prefix}manual-${reading.meter_id}" class="hidden space-y-3">
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="text-xs font-medium text-muted-foreground uppercase tracking-wide block mb-1.5">Gen (kWh)</label>
                        <input type="number" id="${prefix}gen-${reading.meter_id}" step="0.01" min="0" 
                               value="${(reading.energy_generated || 0).toFixed(2)}"
                               class="w-full px-3 py-2 bg-secondary border border-border rounded-lg text-foreground text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all">
                    </div>
                    <div>
                        <label class="text-xs font-medium text-muted-foreground uppercase tracking-wide block mb-1.5">Cons (kWh)</label>
                        <input type="number" id="${prefix}cons-${reading.meter_id}" step="0.01" min="0" 
                               value="${(reading.energy_consumed || 0).toFixed(2)}"
                               class="w-full px-3 py-2 bg-secondary border border-border rounded-lg text-foreground text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all">
                    </div>
                </div>
                
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="text-xs font-medium text-muted-foreground uppercase tracking-wide block mb-1.5">Battery %</label>
                        <input type="number" id="${prefix}batt-${reading.meter_id}" step="1" min="0" max="100" 
                               value="${(reading.battery_level || 0).toFixed(0)}"
                               class="w-full px-3 py-2 bg-secondary border border-border rounded-lg text-foreground text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all">
                    </div>
                    <div>
                        <label class="text-xs font-medium text-muted-foreground uppercase tracking-wide block mb-1.5">Temp (°C)</label>
                        <input type="number" id="${prefix}temp-${reading.meter_id}" step="0.1" 
                               value="${(reading.temperature || 25.0).toFixed(1)}"
                               class="w-full px-3 py-2 bg-secondary border border-border rounded-lg text-foreground text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all">
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-2 pt-1">
                     <button onclick="window.applyManualValues('${reading.meter_id}', '${prefix}')" 
                            class="flex-1 px-3 py-2 bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20 text-xs font-semibold uppercase tracking-wide rounded-lg transition-colors">
                        Apply
                    </button>
                    <button onclick="window.resetToAuto('${reading.meter_id}', '${prefix}')" 
                            class="px-3 py-2 border border-border text-muted-foreground hover:text-foreground hover:bg-secondary text-xs font-semibold uppercase tracking-wide rounded-lg transition-colors">
                        Reset
                    </button>
                </div>
                
                <!-- Hidden inputs for extra fields to prevent errors -->
                <input type="hidden" id="${prefix}volt-${reading.meter_id}" value="${(reading.voltage || 240).toFixed(1)}">
                <input type="hidden" id="${prefix}curr-${reading.meter_id}" value="${(reading.current || 0).toFixed(3)}">
                <input type="hidden" id="${prefix}freq-${reading.meter_id}" value="${(reading.frequency || 50).toFixed(2)}">
                <input type="hidden" id="${prefix}sell-${reading.meter_id}" value="${(reading.max_sell_price || 0.12).toFixed(2)}">
                <input type="hidden" id="${prefix}buy-${reading.meter_id}" value="${(reading.max_buy_price || 0.28).toFixed(2)}">
            </div>

            <!-- Footer Actions -->
            <footer class="flex items-center justify-between pt-1 border-t border-border/30">
                <button onclick="window.toggleManualMode('${reading.meter_id}', '${prefix}')" 
                        id="${prefix}mode-btn-${reading.meter_id}"
                        class="inline-flex items-center gap-1.5 text-primary hover:bg-primary/10 px-3 py-1.5 rounded-lg font-medium text-sm transition-colors" title="Override meter values manually">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>
                    </svg>
                    OVERRIDE
                </button>
                <button onclick="window.deleteMeter('${reading.meter_id}')" 
                        class="inline-flex items-center gap-1.5 text-destructive hover:bg-destructive/10 px-3 py-1.5 rounded-lg font-medium text-sm transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>
                    </svg>
                    REMOVE
                </button>
            </footer>
        </article>
    `;
}

export function updateMeterCardContent(card, reading) {
    // Update values using specific classes
    const genEl = card.querySelector('.val-gen');
    if (genEl) genEl.textContent = (reading.energy_generated || 0).toFixed(2);

    const consEl = card.querySelector('.val-cons');
    if (consEl) consEl.textContent = (reading.energy_consumed || 0).toFixed(2);

    const battTextEl = card.querySelector('.val-batt-text');
    if (battTextEl) battTextEl.textContent = `${(reading.battery_level || 0).toFixed(1)}%`;

    const battBarEl = card.querySelector('.val-batt-bar');
    if (battBarEl) battBarEl.style.width = `${Math.max(reading.battery_level || 0, 2)}%`;

    const tempEl = card.querySelector('.val-temp');
    if (tempEl) tempEl.textContent = `${(reading.temperature || 0).toFixed(1)}°C`;

    const emissionEl = card.querySelector('.val-emission');
    if (emissionEl) emissionEl.textContent = `${(reading.net_emission || 0).toFixed(3)} kg`;

    // Update status banners
    const statusContainer = card.querySelector('.status-container');
    if (statusContainer) {
        statusContainer.innerHTML = '';
        const isSelling = (reading.surplus_energy || 0) > 0;
        const isBuying = (reading.deficit_energy || 0) > 0;

        if (isSelling) {
            statusContainer.innerHTML = `
                <section class="rounded-2xl bg-success/10 border border-success/20 p-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-success/20">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-success">
                                    <path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/>
                                </svg>
                            </div>
                            <span class="font-semibold text-success">Selling</span>
                        </div>
                        <p class="text-right">
                            <span class="text-lg font-bold tabular-nums text-foreground">${(reading.surplus_energy || 0).toFixed(2)}</span>
                            <span class="text-sm text-muted-foreground"> kWh</span>
                            <span class="text-muted-foreground"> @ </span>
                            <span class="text-lg font-bold text-success">$${(reading.max_sell_price || 0).toFixed(2)}</span>
                        </p>
                    </div>
                </section>
            `;
        } else if (isBuying) {
            statusContainer.innerHTML = `
                <section class="rounded-2xl bg-success/10 border border-success/20 p-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-success/20">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-success">
                                    <path d="M17 7 7 17"/><path d="M17 17H7V7"/>
                                </svg>
                            </div>
                            <span class="font-semibold text-success">Buying</span>
                        </div>
                        <p class="text-right">
                            <span class="text-lg font-bold tabular-nums text-foreground">${(reading.deficit_energy || 0).toFixed(2)}</span>
                            <span class="text-sm text-muted-foreground"> kWh</span>
                            <span class="text-muted-foreground"> @ </span>
                            <span class="text-lg font-bold text-success">$${(reading.max_buy_price || 0).toFixed(2)}</span>
                        </p>
                    </div>
                </section>
            `;
        } else {
            statusContainer.innerHTML = `
                <div class="w-full text-sm text-muted-foreground text-center italic py-4 border border-border/50 rounded-2xl bg-secondary/30">
                    System Balanced
                </div>
            `;
        }
    }
}

export function toggleManualMode(meterId, prefix = '') {
    const autoDiv = document.getElementById(`${prefix}auto-${meterId}`);
    const manualDiv = document.getElementById(`${prefix}manual-${meterId}`);
    const btn = document.getElementById(`${prefix}mode-btn-${meterId}`);

    if (manualDiv.classList.contains('hidden')) {
        // Switch to manual mode
        autoDiv.classList.add('hidden');
        manualDiv.classList.remove('hidden');
        btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
            </svg>
            AUTO
        `;
        btn.classList.remove('text-primary', 'hover:bg-primary/10');
        btn.classList.add('text-accent', 'hover:bg-accent/10');
    } else {
        // Switch to auto mode
        manualDiv.classList.add('hidden');
        autoDiv.classList.remove('hidden');
        btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="8" y2="8"/><line x1="18" x2="22" y1="16" y2="16"/>
            </svg>
            MANUAL
        `;
        btn.classList.remove('text-accent', 'hover:bg-accent/10');
        btn.classList.add('text-primary', 'hover:bg-primary/10');
    }
}

// Modals
export function openAddMeterModal() {
    const modal = document.getElementById('add-meter-modal');
    modal.classList.remove('hidden');
    document.getElementById('add-meter-form').reset();
    updateMeterTypeFields();
}

export function closeAddMeterModal(event) {
    if (!event || event.target.id === 'add-meter-modal' || event.type === 'click') {
        const modal = document.getElementById('add-meter-modal');
        modal.classList.add('hidden');
    }
}

export function updateMeterTypeFields() {
    const meterType = document.getElementById('meter-type').value;
    const solarField = document.getElementById('solar-capacity-field');
    const batteryField = document.getElementById('battery-capacity-field');

    if (meterType === 'Solar_Prosumer' || meterType === 'Hybrid_Prosumer') {
        solarField.style.display = 'block';
    } else {
        solarField.style.display = 'none';
    }

    if (meterType === 'Hybrid_Prosumer' || meterType === 'Battery_Storage') {
        batteryField.style.display = 'block';
    } else {
        batteryField.style.display = 'none';
    }
}

export function closeMeterDetails(event) {
    if (!event || event.target.id === 'meter-details-modal' || event.type === 'click') {
        document.getElementById('meter-details-modal').classList.add('hidden');
    }
}

export function openMeterDetails(meterId) {
    const reading = allReadings.find(r => r.meter_id === meterId);
    if (!reading) return;

    const modal = document.getElementById('meter-details-modal');
    const content = document.getElementById('meter-details-content');

    const modalHtml = createMeterDetailsModalContent(reading);
    content.innerHTML = modalHtml;
    modal.classList.remove('hidden');
}

function createMeterDetailsModalContent(reading) {
    const isSelling = (reading.surplus_energy || 0) > 0;
    const isBuying = (reading.deficit_energy || 0) > 0;

    return `
        <article class="w-full rounded-3xl border border-border/50 bg-card shadow-2xl shadow-black/40 p-6 space-y-6">
            <!-- Header -->
            <header class="flex items-start justify-between gap-4 border-b border-border/50 pb-6">
                <div class="flex items-center gap-4">
                    <div class="min-w-0 space-y-1">
                        <h2 class="text-2xl font-bold text-foreground truncate" title="${reading.location}">${reading.location}</h2>
                        <p class="font-mono text-sm text-muted-foreground leading-tight break-all">${reading.meter_id}</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold tracking-wide ${reading.is_connected ? 'bg-success/15 text-success' : 'bg-destructive/15 text-destructive'}">
                        <span class="h-2 w-2 rounded-full ${reading.is_connected ? 'bg-success animate-pulse' : 'bg-destructive'}"></span>
                        ${reading.is_connected ? 'ONLINE' : 'OFFLINE'}
                    </span>
                </div>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <!-- Left Column: Primary Stats -->
                <div class="space-y-6">
                    <h3 class="text-lg font-semibold text-foreground">Energy Status</h3>
                    
                    <div class="grid grid-cols-2 gap-4">
                         <article class="group rounded-2xl bg-secondary/50 p-4 transition-colors hover:bg-secondary/70 cursor-default">
                            <div class="flex items-center gap-2 mb-3">
                                <div class="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-400/15">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-amber-400">
                                        <circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>
                                    </svg>
                                </div>
                                <span class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Gen</span>
                            </div>
                            <p class="flex items-baseline gap-1.5">
                                <span class="text-3xl font-bold tracking-tight text-foreground tabular-nums">${(reading.energy_generated || 0).toFixed(2)}</span>
                                <span class="text-sm font-medium text-muted-foreground">kWh</span>
                            </p>
                        </article>

                        <article class="group rounded-2xl bg-secondary/50 p-4 transition-colors hover:bg-secondary/70 cursor-default">
                            <div class="flex items-center gap-2 mb-3">
                                <div class="flex h-8 w-8 items-center justify-center rounded-xl bg-cyan-400/15">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-cyan-400">
                                        <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>
                                    </svg>
                                </div>
                                <span class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Cons</span>
                            </div>
                            <p class="flex items-baseline gap-1.5">
                                <span class="text-3xl font-bold tracking-tight text-foreground tabular-nums">${(reading.energy_consumed || 0).toFixed(2)}</span>
                                <span class="text-sm font-medium text-muted-foreground">kWh</span>
                            </p>
                        </article>
                    </div>

                    <!-- Battery Section -->
                    <section class="space-y-3 p-4 bg-secondary/30 rounded-2xl border border-border/50">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-muted-foreground">
                                    <rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><line x1="22" x2="22" y1="11" y2="13"/>
                                </svg>
                                <span class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Battery Storage</span>
                            </div>
                            <span class="text-sm font-bold tabular-nums text-foreground">${(reading.battery_level || 0).toFixed(1)}%</span>
                        </div>
                        <div class="h-3 w-full rounded-full bg-secondary overflow-hidden">
                            <div class="h-full rounded-full bg-gradient-to-r from-cyan-400 to-green-500 transition-all duration-700 ease-out" style="width: ${(reading.battery_level || 0)}%"></div>
                        </div>
                    </section>

                     <!-- Status Banners -->
                    <div class="status-container">
                        ${isSelling ? `
                            <section class="rounded-2xl bg-green-500/10 border border-green-500/20 p-4">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center gap-3">
                                        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-green-500/20">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-green-500">
                                                <path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/>
                                            </svg>
                                        </div>
                                        <span class="font-semibold text-green-500">Selling to Grid</span>
                                    </div>
                                    <p class="text-right">
                                        <span class="text-lg font-bold tabular-nums text-foreground">${(reading.surplus_energy || 0).toFixed(2)}</span>
                                        <span class="text-sm text-muted-foreground"> kWh</span>
                                    </p>
                                </div>
                            </section>
                        ` : ''}
                        ${isBuying ? `
                            <section class="rounded-2xl bg-orange-500/10 border border-orange-500/20 p-4">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center gap-3">
                                        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500/20">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-orange-500">
                                                <path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/>
                                            </svg>
                                        </div>
                                        <span class="font-semibold text-orange-500">Buying from Grid</span>
                                    </div>
                                    <p class="text-right">
                                        <span class="text-lg font-bold tabular-nums text-foreground">${(reading.deficit_energy || 0).toFixed(2)}</span>
                                        <span class="text-sm text-muted-foreground"> kWh</span>
                                    </p>
                                </div>
                            </section>
                        ` : ''}
                        ${!isSelling && !isBuying ? `
                            <div class="w-full text-sm text-muted-foreground text-center italic py-4 border border-border/50 rounded-2xl bg-secondary/30">
                                System Balanced
                            </div>
                        ` : ''}
                    </div>
                </div>

                <!-- Right Column: Technical Specs & Controls -->
                <div class="space-y-6">
                    <h3 class="text-lg font-semibold text-foreground">Technical Metrics</h3>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div class="p-4 bg-secondary/30 rounded-2xl border border-border/50">
                            <span class="text-xs font-medium text-muted-foreground uppercase tracking-wider block mb-1">Voltage</span>
                            <span class="text-2xl font-bold text-foreground tabular-nums">${(reading.voltage || 240).toFixed(1)}</span>
                            <span class="text-xs text-muted-foreground ml-1">V</span>
                        </div>
                        <div class="p-4 bg-secondary/30 rounded-2xl border border-border/50">
                            <span class="text-xs font-medium text-muted-foreground uppercase tracking-wider block mb-1">Current</span>
                            <span class="text-2xl font-bold text-foreground tabular-nums">${(reading.current || 0).toFixed(3)}</span>
                            <span class="text-xs text-muted-foreground ml-1">A</span>
                        </div>
                        <div class="p-4 bg-secondary/30 rounded-2xl border border-border/50">
                            <span class="text-xs font-medium text-muted-foreground uppercase tracking-wider block mb-1">Frequency</span>
                            <span class="text-2xl font-bold text-foreground tabular-nums">${(reading.frequency || 50).toFixed(2)}</span>
                            <span class="text-xs text-muted-foreground ml-1">Hz</span>
                        </div>
                        <div class="p-4 bg-secondary/30 rounded-2xl border border-border/50">
                            <span class="text-xs font-medium text-muted-foreground uppercase tracking-wider block mb-1">Temperature</span>
                            <span class="text-2xl font-bold text-foreground tabular-nums">${(reading.temperature || 0).toFixed(1)}</span>
                            <span class="text-xs text-muted-foreground ml-1">°C</span>
                        </div>
                    </div>

                    <div class="space-y-3 pt-4 border-t border-border/50">
                        <h3 class="text-lg font-semibold text-foreground">Market Prices</h3>
                        <div class="flex items-center justify-between p-3 bg-secondary/30 rounded-xl">
                            <span class="text-sm text-muted-foreground">Sell Price</span>
                            <span class="text-base font-bold text-green-500">$${(reading.max_sell_price || 0).toFixed(2)}</span>
                        </div>
                        <div class="flex items-center justify-between p-3 bg-secondary/30 rounded-xl">
                            <span class="text-sm text-muted-foreground">Buy Price</span>
                            <span class="text-base font-bold text-orange-500">$${(reading.max_buy_price || 0).toFixed(2)}</span>
                        </div>
                    </div>

                    <!-- Manual Controls (Always visible in modal) -->
                    <div class="pt-4 border-t border-border/50">
                        <h3 class="text-lg font-semibold text-foreground mb-4">Manual Override</h3>
                        <div class="grid grid-cols-2 gap-4 mb-4">
                            <div>
                                <label class="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-2">Gen (kWh)</label>
                                <input type="number" id="modal-gen-${reading.meter_id}" step="0.01" min="0" 
                                       value="${(reading.energy_generated || 0).toFixed(2)}"
                                       class="w-full px-3 py-2 bg-secondary border border-border rounded-xl text-foreground focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all">
                            </div>
                            <div>
                                <label class="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-2">Cons (kWh)</label>
                                <input type="number" id="modal-cons-${reading.meter_id}" step="0.01" min="0" 
                                       value="${(reading.energy_consumed || 0).toFixed(2)}"
                                       class="w-full px-3 py-2 bg-secondary border border-border rounded-xl text-foreground focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all">
                            </div>
                        </div>
                        <div class="flex gap-3">
                            <button onclick="window.applyManualValues('${reading.meter_id}', 'modal-')" 
                                    class="flex-1 px-4 py-2 bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20 text-sm font-bold uppercase tracking-wide rounded-xl transition-colors">
                                Apply
                            </button>
                            <button onclick="window.resetToAuto('${reading.meter_id}', 'modal-')" 
                                    class="px-4 py-2 border border-border text-muted-foreground hover:text-foreground hover:bg-secondary text-sm font-bold uppercase tracking-wide rounded-xl transition-colors">
                                Reset
                            </button>
                        </div>
                        
                        <!-- Hidden inputs required by applyManualValues -->
                        <input type="hidden" id="modal-batt-${reading.meter_id}" value="${(reading.battery_level || 0).toFixed(0)}">
                        <input type="hidden" id="modal-temp-${reading.meter_id}" value="${(reading.temperature || 25.0).toFixed(1)}">
                        <input type="hidden" id="modal-volt-${reading.meter_id}" value="${(reading.voltage || 240).toFixed(1)}">
                        <input type="hidden" id="modal-curr-${reading.meter_id}" value="${(reading.current || 0).toFixed(3)}">
                        <input type="hidden" id="modal-freq-${reading.meter_id}" value="${(reading.frequency || 50).toFixed(2)}">
                        <input type="hidden" id="modal-sell-${reading.meter_id}" value="${(reading.max_sell_price || 0.12).toFixed(2)}">
                        <input type="hidden" id="modal-buy-${reading.meter_id}" value="${(reading.max_buy_price || 0.28).toFixed(2)}">
                    </div>
                </div>
            </div>

            <!-- Footer Actions -->
            <footer class="flex items-center justify-end pt-6 border-t border-border/50 gap-3">
                <button onclick="window.deleteMeter('${reading.meter_id}')" 
                        class="inline-flex items-center gap-2 text-destructive hover:bg-destructive/10 px-4 py-2 rounded-xl font-semibold text-sm transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>
                    </svg>
                    REMOVE METER
                </button>
            </footer>
        </article>
    `;
}
