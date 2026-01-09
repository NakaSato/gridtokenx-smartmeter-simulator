import { isMeterLive } from '../state.js';

// Meter Cards
export function createMeterCard(reading, prefix = '') {
    const isSelling = (reading.surplus_energy || 0) > 0;
    const isBuying = (reading.deficit_energy || 0) > 0;
    const isLive = isMeterLive(reading.meter_id);
    const batteryLevel = reading.battery_level || 0;

    // Meter type styling with icons
    const meterTypeStyles = {
        'Solar_Prosumer': {
            bg: 'bg-gradient-to-r from-amber-500/20 to-orange-500/10',
            border: 'border-amber-500/30',
            text: 'text-amber-400',
            label: 'Solar',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>`
        },
        'Grid_Consumer': {
            bg: 'bg-gradient-to-r from-blue-500/20 to-cyan-500/10',
            border: 'border-blue-500/30',
            text: 'text-blue-400',
            label: 'Consumer',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/></svg>`
        },
        'Hybrid_Prosumer': {
            bg: 'bg-gradient-to-r from-purple-500/20 to-pink-500/10',
            border: 'border-purple-500/30',
            text: 'text-purple-400',
            label: 'Hybrid',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><line x1="22" x2="22" y1="11" y2="13"/></svg>`
        },
        'Battery_Storage': {
            bg: 'bg-gradient-to-r from-emerald-500/20 to-teal-500/10',
            border: 'border-emerald-500/30',
            text: 'text-emerald-400',
            label: 'Storage',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><line x1="22" x2="22" y1="11" y2="13"/></svg>`
        },
    };
    const meterStyle = meterTypeStyles[reading.meter_type] || meterTypeStyles['Grid_Consumer'];

    // Battery color based on level
    const batteryColor = batteryLevel > 60 ? 'from-emerald-400 to-green-500' :
        batteryLevel > 30 ? 'from-amber-400 to-yellow-500' :
            'from-red-400 to-orange-500';

    // Trading status styling
    const tradingBg = isSelling ? 'bg-emerald-500/5 border-emerald-500/20' :
        isBuying ? 'bg-orange-500/5 border-orange-500/20' :
            'bg-slate-800/30 border-slate-700/30';

    return `
        <article class="group relative w-full rounded-2xl border ${tradingBg} bg-slate-900/40 backdrop-blur-sm shadow-lg hover:shadow-xl hover:shadow-slate-900/50 transition-all duration-300 overflow-hidden" id="${prefix}card-${reading.meter_id}">
            
            <!-- Glow effect for live meters -->
            ${isLive ? '<div class="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-transparent pointer-events-none"></div>' : ''}
            
            <!-- Header -->
            <header class="relative px-4 pt-4 pb-3 flex items-start justify-between gap-2">
                <div class="flex items-center gap-2.5 min-w-0 flex-1">
                    <!-- Type Badge -->
                    <div class="flex-shrink-0 flex h-9 w-9 items-center justify-center rounded-xl ${meterStyle.bg} ${meterStyle.border} border">
                        <span class="${meterStyle.text}">${meterStyle.icon}</span>
                    </div>
                    <div class="min-w-0 flex-1">
                        <div class="flex items-center gap-2">
                            <h2 class="text-sm font-semibold text-white truncate" title="${reading.meter_id}">${reading.meter_id}</h2>
                            <span class="flex-shrink-0 inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${meterStyle.bg} ${meterStyle.text}">
                                ${meterStyle.label}
                            </span>
                        </div>
                        <p class="text-[10px] text-slate-500 truncate" title="${reading.location}">${reading.location || 'Unknown location'}</p>
                    </div>
                </div>
                
                <!-- Status & Actions -->
                <div class="flex items-center gap-1.5 flex-shrink-0">
                    <span class="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wide ${isLive ? 'bg-emerald-500/15 text-emerald-400 animate-pulse' : 'bg-slate-700/50 text-slate-500'}">
                        <span class="h-1.5 w-1.5 rounded-full ${isLive ? 'bg-emerald-400' : 'bg-slate-500'}"></span>
                        ${isLive ? 'LIVE' : 'IDLE'}
                    </span>
                    <button onclick="window.openMeterDetails('${reading.meter_id}')" class="p-1.5 text-slate-500 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors" title="View Details">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                        </svg>
                    </button>
                </div>
            </header>

            <!-- Energy Stats - Main Focus -->
            <div id="${prefix}auto-${reading.meter_id}" class="px-4 pb-4 space-y-3">
                <div class="grid grid-cols-2 gap-2">
                    <!-- Generation -->
                    <div class="relative overflow-hidden rounded-xl bg-gradient-to-br from-amber-500/10 via-amber-500/5 to-transparent p-3 border border-amber-500/10">
                        <div class="flex items-center gap-1.5 mb-1">
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-amber-400">
                                <circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/>
                            </svg>
                            <span class="text-[10px] font-medium text-amber-400/80 uppercase tracking-wider">Gen</span>
                        </div>
                        <p class="flex items-baseline gap-0.5">
                            <span class="text-xl font-bold tracking-tight text-white tabular-nums val-gen transition-all duration-300">${(reading.energy_generated || 0).toFixed(1)}</span>
                            <span class="text-[10px] font-medium text-slate-500">kWh</span>
                        </p>
                    </div>

                    <!-- Consumption -->
                    <div class="relative overflow-hidden rounded-xl bg-gradient-to-br from-blue-500/10 via-blue-500/5 to-transparent p-3 border border-blue-500/10">
                        <div class="flex items-center gap-1.5 mb-1">
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-blue-400">
                                <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>
                            </svg>
                            <span class="text-[10px] font-medium text-blue-400/80 uppercase tracking-wider">Use</span>
                        </div>
                        <p class="flex items-baseline gap-0.5">
                            <span class="text-xl font-bold tracking-tight text-white tabular-nums val-cons transition-all duration-300">${(reading.energy_consumed || 0).toFixed(1)}</span>
                            <span class="text-[10px] font-medium text-slate-500">kWh</span>
                        </p>
                    </div>
                </div>

                <!-- Battery + Metrics Row -->
                <div class="flex items-center gap-3 px-0.5">
                    <!-- Battery -->
                    <div class="flex items-center gap-2 flex-1">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-500 flex-shrink-0">
                            <rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><line x1="22" x2="22" y1="11" y2="13"/>
                        </svg>
                        <div class="flex-1 h-2 rounded-full bg-slate-800 overflow-hidden">
                            <div class="h-full rounded-full bg-gradient-to-r ${batteryColor} transition-all duration-500 val-batt-bar" style="width: ${Math.max(batteryLevel, 3)}%"></div>
                        </div>
                        <span class="text-xs font-semibold tabular-nums text-slate-400 val-batt-text w-10 text-right">${batteryLevel.toFixed(0)}%</span>
                    </div>
                    
                    <!-- Temp -->
                    <div class="flex items-center gap-1.5 px-2 py-1 bg-slate-800/50 rounded-lg">
                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-orange-400">
                            <path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>
                        </svg>
                        <span class="text-[11px] font-medium tabular-nums text-slate-400 val-temp">${(reading.temperature || 0).toFixed(0)}°</span>
                    </div>
                </div>

                <!-- Trading Status -->
                <div class="status-container mt-auto">
                    ${isSelling ? `
                        <div class="group/status flex items-center justify-between p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/15 transition-colors">
                            <div class="flex items-center gap-3">
                                <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 group-hover/status:scale-110 transition-transform">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M12 19V5"/><path d="m5 12 7-7 7 7"/>
                                    </svg>
                                </div>
                                <div>
                                    <span class="block text-[10px] font-bold text-emerald-400 uppercase tracking-wider leading-none mb-1">Selling</span>
                                    <span class="text-xs text-slate-300 font-medium">${(reading.surplus_energy || 0).toFixed(2)} kWh</span>
                                </div>
                            </div>
                            <div class="text-right">
                                <span class="block text-[10px] font-medium text-emerald-400/70 uppercase tracking-wider leading-none mb-1">Price</span>
                                <span class="text-base font-bold text-emerald-400">$${(reading.max_sell_price || 0).toFixed(2)}</span>
                            </div>
                        </div>
                    ` : ''}
                    ${isBuying ? `
                        <div class="group/status flex items-center justify-between p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/15 transition-colors">
                            <div class="flex items-center gap-3">
                                <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400 group-hover/status:scale-110 transition-transform">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M12 5v14"/><path d="m19 12-7 7-7-7"/>
                                    </svg>
                                </div>
                                <div>
                                    <span class="block text-[10px] font-bold text-amber-400 uppercase tracking-wider leading-none mb-1">Buying</span>
                                    <span class="text-xs text-slate-300 font-medium">${(reading.deficit_energy || 0).toFixed(2)} kWh</span>
                                </div>
                            </div>
                            <div class="text-right">
                                <span class="block text-[10px] font-medium text-amber-400/70 uppercase tracking-wider leading-none mb-1">Price</span>
                                <span class="text-base font-bold text-amber-400">$${(reading.max_buy_price || 0).toFixed(2)}</span>
                            </div>
                        </div>
                    ` : ''}
                    ${!isSelling && !isBuying ? `
                        <div class="flex items-center justify-center gap-2 py-3 px-3 rounded-xl bg-slate-800/30 border border-slate-700/30">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-500">
                                <path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/>
                            </svg>
                            <span class="text-xs text-slate-500 font-medium">System Balanced</span>
                        </div>
                    ` : ''}
                </div>
            </div>

            <!-- Manual Mode Controls (Hidden by default) -->
            <div id="${prefix}manual-${reading.meter_id}" class="hidden px-4 pb-4 space-y-3">
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="text-[10px] font-medium text-slate-500 uppercase tracking-wide block mb-1">Gen (kWh)</label>
                        <input type="number" id="${prefix}gen-${reading.meter_id}" step="0.01" min="0" 
                               value="${(reading.energy_generated || 0).toFixed(2)}"
                               class="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all">
                    </div>
                    <div>
                        <label class="text-[10px] font-medium text-slate-500 uppercase tracking-wide block mb-1">Use (kWh)</label>
                        <input type="number" id="${prefix}cons-${reading.meter_id}" step="0.01" min="0" 
                               value="${(reading.energy_consumed || 0).toFixed(2)}"
                               class="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all">
                    </div>
                </div>
                
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="text-[10px] font-medium text-slate-500 uppercase tracking-wide block mb-1">Battery %</label>
                        <input type="number" id="${prefix}batt-${reading.meter_id}" step="1" min="0" max="100" 
                               value="${batteryLevel.toFixed(0)}"
                               class="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all">
                    </div>
                    <div>
                        <label class="text-[10px] font-medium text-slate-500 uppercase tracking-wide block mb-1">Temp (°C)</label>
                        <input type="number" id="${prefix}temp-${reading.meter_id}" step="0.1" 
                               value="${(reading.temperature || 25.0).toFixed(1)}"
                               class="w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all">
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-2">
                     <button onclick="window.applyManualValues('${reading.meter_id}', '${prefix}')" 
                            class="px-3 py-1.5 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/20 text-xs font-bold uppercase tracking-wide rounded-lg transition-colors">
                        Apply
                    </button>
                    <button onclick="window.resetToAuto('${reading.meter_id}', '${prefix}')" 
                            class="px-3 py-1.5 border border-slate-700 text-slate-400 hover:text-white hover:bg-slate-800 text-xs font-bold uppercase tracking-wide rounded-lg transition-colors">
                        Reset
                    </button>
                </div>
                
                <!-- Hidden inputs for extra fields -->
                <input type="hidden" id="${prefix}volt-${reading.meter_id}" value="${(reading.voltage || 240).toFixed(1)}">
                <input type="hidden" id="${prefix}curr-${reading.meter_id}" value="${(reading.current || 0).toFixed(3)}">
                <input type="hidden" id="${prefix}freq-${reading.meter_id}" value="${(reading.frequency || 50).toFixed(2)}">
                <input type="hidden" id="${prefix}sell-${reading.meter_id}" value="${(reading.max_sell_price || 0.12).toFixed(2)}">
                <input type="hidden" id="${prefix}buy-${reading.meter_id}" value="${(reading.max_buy_price || 0.28).toFixed(2)}">
            </div>

            <!-- Footer Actions -->
            <footer class="grid grid-cols-2 gap-2 px-4 py-3 border-t border-slate-800/80 bg-slate-900/30">
                <button onclick="window.toggleManualMode('${reading.meter_id}', '${prefix}')" 
                        id="${prefix}mode-btn-${reading.meter_id}"
                        class="flex items-center justify-center gap-2 text-slate-400 hover:text-white hover:bg-slate-800 px-3 py-2 rounded-xl text-xs font-semibold uppercase tracking-wide transition-all border border-transparent hover:border-slate-700">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>
                    </svg>
                    Override
                </button>
                <button onclick="window.deleteMeter('${reading.meter_id}')" 
                        class="flex items-center justify-center gap-2 text-red-400/80 hover:text-red-400 hover:bg-red-500/10 px-3 py-2 rounded-xl text-xs font-semibold uppercase tracking-wide transition-all border border-transparent hover:border-red-500/20">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                    </svg>
                    Remove
                </button>
            </footer>
        </article>
    `;
}

// Compact list row for table view
export function createMeterRow(reading) {
    const isSelling = (reading.surplus_energy || 0) > 0;
    const isBuying = (reading.deficit_energy || 0) > 0;
    const isLive = isMeterLive(reading.meter_id);
    const batteryLevel = reading.battery_level || 0;

    const meterTypeStyles = {
        'Solar_Prosumer': { bg: 'bg-amber-500/20', text: 'text-amber-400', label: 'Solar' },
        'Grid_Consumer': { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Consumer' },
        'Hybrid_Prosumer': { bg: 'bg-purple-500/20', text: 'text-purple-400', label: 'Hybrid' },
        'Battery_Storage': { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'Storage' },
    };
    const ms = meterTypeStyles[reading.meter_type] || meterTypeStyles['Grid_Consumer'];

    const tradingStatus = isSelling
        ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400"><svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg>${(reading.surplus_energy || 0).toFixed(1)}</span>`
        : isBuying
            ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-orange-500/20 text-orange-400"><svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14"/><path d="m19 12-7 7-7-7"/></svg>${(reading.deficit_energy || 0).toFixed(1)}</span>`
            : `<span class="text-[10px] text-slate-500">—</span>`;

    const batteryColor = batteryLevel > 60 ? 'bg-emerald-500' : batteryLevel > 30 ? 'bg-amber-500' : 'bg-red-500';

    return `
        <tr class="group border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors" id="row-${reading.meter_id}">
            <td class="px-3 py-2">
                <div class="flex items-center gap-2">
                    <span class="h-2 w-2 rounded-full ${isLive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}"></span>
                    <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${ms.bg} ${ms.text}">${ms.label}</span>
                </div>
            </td>
            <td class="px-3 py-2">
                <button onclick="window.openMeterDetails('${reading.meter_id}')" class="text-xs font-mono text-slate-300 hover:text-white hover:underline transition-colors">${reading.meter_id}</button>
            </td>
            <td class="px-3 py-2 text-right">
                <span class="text-xs font-semibold tabular-nums text-amber-400 val-gen">${(reading.energy_generated || 0).toFixed(1)}</span>
            </td>
            <td class="px-3 py-2 text-right">
                <span class="text-xs font-semibold tabular-nums text-blue-400 val-cons">${(reading.energy_consumed || 0).toFixed(1)}</span>
            </td>
            <td class="px-3 py-2">
                <div class="flex items-center gap-1.5">
                <div class="flex items-center gap-2">
                    <div class="w-16 h-2 rounded-full bg-slate-800 overflow-hidden">
                        <div class="h-full rounded-full ${batteryColor} val-batt-bar transition-all duration-300" style="width: ${Math.max(batteryLevel, 3)}%"></div>
                    </div>
                    <span class="text-xs font-medium tabular-nums text-slate-400 val-batt-text w-9 text-right">${batteryLevel.toFixed(0)}%</span>
                </div>
                </div>
            </td>
            <td class="px-3 py-2 text-center">${tradingStatus}</td>
            <td class="px-3 py-2 text-right">
                <button onclick="window.openMeterDetails('${reading.meter_id}')" class="p-1 text-slate-500 hover:text-white hover:bg-slate-700 rounded transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>
                </button>
            </td>
        </tr>
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
                <div class="group/status flex items-center justify-between p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/15 transition-colors">
                    <div class="flex items-center gap-3">
                        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 group-hover/status:scale-110 transition-transform">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 19V5"/><path d="m5 12 7-7 7 7"/>
                            </svg>
                        </div>
                        <div>
                            <span class="block text-[10px] font-bold text-emerald-400 uppercase tracking-wider leading-none mb-1">Selling</span>
                            <span class="text-xs text-slate-300 font-medium">${(reading.surplus_energy || 0).toFixed(2)} kWh</span>
                        </div>
                    </div>
                    <div class="text-right">
                        <span class="block text-[10px] font-medium text-emerald-400/70 uppercase tracking-wider leading-none mb-1">Price</span>
                        <span class="text-base font-bold text-emerald-400">$${(reading.max_sell_price || 0).toFixed(2)}</span>
                    </div>
                </div>
            `;
        } else if (isBuying) {
            statusContainer.innerHTML = `
                <div class="group/status flex items-center justify-between p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/15 transition-colors">
                    <div class="flex items-center gap-3">
                        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400 group-hover/status:scale-110 transition-transform">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 5v14"/><path d="m19 12-7 7-7-7"/>
                            </svg>
                        </div>
                        <div>
                            <span class="block text-[10px] font-bold text-amber-400 uppercase tracking-wider leading-none mb-1">Buying</span>
                            <span class="text-xs text-slate-300 font-medium">${(reading.deficit_energy || 0).toFixed(2)} kWh</span>
                        </div>
                    </div>
                    <div class="text-right">
                        <span class="block text-[10px] font-medium text-amber-400/70 uppercase tracking-wider leading-none mb-1">Price</span>
                        <span class="text-base font-bold text-amber-400">$${(reading.max_buy_price || 0).toFixed(2)}</span>
                    </div>
                </div>
            `;
        } else {
            statusContainer.innerHTML = `
                 <div class="flex items-center justify-center gap-2 py-3 px-3 rounded-xl bg-slate-800/30 border border-slate-700/30">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-500">
                        <path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/>
                    </svg>
                    <span class="text-xs text-slate-500 font-medium">System Balanced</span>
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
