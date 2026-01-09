import { allReadings } from '../state.js';

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
        <article class="w-full rounded-[2rem] border border-white/10 bg-slate-900/90 backdrop-blur-xl shadow-2xl p-8 space-y-8 relative overflow-hidden">
             <!-- Background Decorative Gradients -->
            <div class="absolute -top-24 -right-24 w-64 h-64 bg-primary/20 rounded-full blur-[100px] pointer-events-none"></div>
            <div class="absolute -bottom-24 -left-24 w-64 h-64 bg-purple-500/20 rounded-full blur-[100px] pointer-events-none"></div>

            <!-- Header -->
            <header class="relative flex items-start justify-between gap-6 pb-6 border-b border-white/5">
                <div class="space-y-1.5 flex-1 min-w-0">
                    <div class="flex items-center gap-3">
                        <div class="p-2 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-white/5 shadow-inner shrink-0">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-primary">
                                <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/>
                            </svg>
                        </div>
                        <h2 class="text-3xl font-bold text-white tracking-tight truncate" title="${reading.location}">${reading.location}</h2>
                    </div>
                    <p class="font-mono text-sm text-slate-400 pl-[3.25rem] truncate">${reading.meter_id}</p>
                </div>
                
                <div class="flex flex-col items-end gap-2 shrink-0">
                     <div class="flex items-center gap-3">
                        <span class="inline-flex items-center gap-2 rounded-full pl-2 pr-3 py-1 text-xs font-bold tracking-wider uppercase border ${reading.is_connected ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.15)]' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'}">
                            <span class="relative flex h-2.5 w-2.5">
                            <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${reading.is_connected ? 'bg-emerald-400' : 'bg-rose-400'}"></span>
                            <span class="relative inline-flex rounded-full h-2.5 w-2.5 ${reading.is_connected ? 'bg-emerald-500' : 'bg-rose-500'}"></span>
                            </span>
                            ${reading.is_connected ? 'Online' : 'Offline'}
                        </span>
                        <button onclick="closeMeterDetails()" class="p-1 text-slate-400 hover:text-white transition-colors rounded-lg hover:bg-white/5">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M18 6 6 18"/><path d="M6 6 18 18"/>
                            </svg>
                        </button>
                    </div>
                     <div class="px-2.5 py-0.5 rounded-lg bg-slate-800/50 border border-white/5 text-[10px] font-medium text-slate-400 self-end mr-[36px]">
                        v1.0.2
                    </div>
                </div>
            </header>

            <div class="relative grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Left Column: Primary Stats -->
                <div class="space-y-6">
                    <div class="flex items-center justify-between">
                         <h3 class="text-base font-semibold text-slate-200 flex items-center gap-2">
                            <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                            Power Flow
                        </h3>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                         <!-- Generation Card -->
                         <article class="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-white/5 p-5 transition-all duration-300 hover:scale-[1.02] hover:border-amber-400/30 hover:shadow-[0_0_30px_rgba(251,191,36,0.1)]">
                            <div class="absolute inset-0 bg-amber-400/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                            <div class="relative z-10">
                                <div class="flex items-center gap-2 mb-4">
                                    <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-400/10 text-amber-400 group-hover:bg-amber-400 group-hover:text-black transition-colors duration-300">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                            <circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>
                                        </svg>
                                    </div>
                                    <span class="text-xs font-bold text-amber-400/80 uppercase tracking-widest">Gen</span>
                                </div>
                                <div class="space-y-1">
                                    <div class="text-3xl font-bold tracking-tight text-white tabular-nums group-hover:text-amber-400 transition-colors">${(reading.energy_generated || 0).toFixed(2)}</div>
                                    <div class="text-xs font-medium text-slate-500">kWh produced</div>
                                </div>
                            </div>
                        </article>

                        <!-- Consumption Card -->
                        <article class="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-white/5 p-5 transition-all duration-300 hover:scale-[1.02] hover:border-cyan-400/30 hover:shadow-[0_0_30px_rgba(34,211,238,0.1)]">
                            <div class="absolute inset-0 bg-cyan-400/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                             <div class="relative z-10">
                                <div class="flex items-center gap-2 mb-4">
                                    <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-400 group-hover:bg-cyan-400 group-hover:text-black transition-colors duration-300">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>
                                        </svg>
                                    </div>
                                    <span class="text-xs font-bold text-cyan-400/80 uppercase tracking-widest">Cons</span>
                                </div>
                                <div class="space-y-1">
                                    <div class="text-3xl font-bold tracking-tight text-white tabular-nums group-hover:text-cyan-400 transition-colors">${(reading.energy_consumed || 0).toFixed(2)}</div>
                                    <div class="text-xs font-medium text-slate-500">kWh used</div>
                                </div>
                            </div>
                        </article>
                    </div>

                    <!-- Battery Section -->
                    <section class="group relative rounded-2xl bg-slate-900/50 border border-white/5 p-5 transition-all hover:bg-slate-900/80">
                        <div class="flex items-center justify-between mb-4">
                            <div class="flex items-center gap-3">
                                <div class="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><line x1="22" x2="22" y1="11" y2="13"/>
                                    </svg>
                                </div>
                                <div>
                                    <span class="text-xs font-bold text-slate-400 uppercase tracking-wider block">Storage</span>
                                    <span class="text-lg font-bold tabular-nums text-white">${(reading.battery_level || 0).toFixed(1)}%</span>
                                </div>
                            </div>
                             <div class="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">Optimal</div>
                        </div>
                        <div class="relative h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                            <div class="absolute top-0 left-0 h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400 shadow-[0_0_10px_rgba(16,185,129,0.5)] transition-all duration-1000 ease-out" 
                                 style="width: ${(reading.battery_level || 0)}%">
                            </div>
                        </div>
                    </section>

                     <!-- Status Banners -->
                    <div class="space-y-3">
                        ${isSelling ? `
                            <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20 p-4">
                                <div class="flex items-center justify-between relative z-10">
                                    <div class="flex items-center gap-3">
                                        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500 text-black shadow-lg shadow-emerald-500/20">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                                <path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/>
                                            </svg>
                                        </div>
                                        <div>
                                            <span class="block text-sm font-bold text-emerald-400">Exporting</span>
                                            <span class="text-xs text-emerald-400/70">Selling surplus to grid</span>
                                        </div>
                                    </div>
                                    <div class="text-right">
                                        <div class="text-xl font-bold tabular-nums text-white">${(reading.surplus_energy || 0).toFixed(2)}</div>
                                        <div class="text-xs font-medium text-emerald-400/70">kWh</div>
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                        ${isBuying ? `
                            <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-rose-500/10 to-rose-500/5 border border-rose-500/20 p-4">
                                <div class="flex items-center justify-between relative z-10">
                                    <div class="flex items-center gap-3">
                                        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500 text-white shadow-lg shadow-rose-500/20">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                                <path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/>
                                            </svg>
                                        </div>
                                        <div>
                                            <span class="block text-sm font-bold text-rose-400">Importing</span>
                                            <span class="text-xs text-rose-400/70">Buying from grid</span>
                                        </div>
                                    </div>
                                    <div class="text-right">
                                        <div class="text-xl font-bold tabular-nums text-white">${(reading.deficit_energy || 0).toFixed(2)}</div>
                                        <div class="text-xs font-medium text-rose-400/70">kWh</div>
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                        ${!isSelling && !isBuying ? `
                            <div class="flex items-center justify-center gap-2 p-4 rounded-2xl border border-dashed border-slate-700 bg-slate-800/30">
                                <span class="h-2 w-2 rounded-full bg-slate-500"></span>
                                <span class="text-sm font-medium text-slate-400">Grid Balanced</span>
                            </div>
                        ` : ''}
                    </div>
                </div>

                <!-- Right Column: Technical Specs & Controls -->
                <div class="space-y-6">
                    <div class="flex items-center justify-between">
                         <h3 class="text-base font-semibold text-slate-200 flex items-center gap-2">
                            <svg class="w-4 h-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                            Metrics
                        </h3>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-3">
                         <!-- Metric Item -->
                        <div class="group p-3 bg-slate-800/40 rounded-xl border border-white/5 transition-all hover:bg-slate-800/60 hover:border-white/10">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Voltage</span>
                            <div class="flex items-baseline gap-1">
                                <span class="text-xl font-bold text-white tabular-nums group-hover:text-primary transition-colors">${(reading.voltage || 240).toFixed(1)}</span>
                                <span class="text-xs text-slate-500">V</span>
                            </div>
                        </div>
                        <div class="group p-3 bg-slate-800/40 rounded-xl border border-white/5 transition-all hover:bg-slate-800/60 hover:border-white/10">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Current</span>
                            <div class="flex items-baseline gap-1">
                                <span class="text-xl font-bold text-white tabular-nums group-hover:text-primary transition-colors">${(reading.current || 0).toFixed(3)}</span>
                                <span class="text-xs text-slate-500">A</span>
                            </div>
                        </div>
                        <div class="group p-3 bg-slate-800/40 rounded-xl border border-white/5 transition-all hover:bg-slate-800/60 hover:border-white/10">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Frequency</span>
                            <div class="flex items-baseline gap-1">
                                <span class="text-xl font-bold text-white tabular-nums group-hover:text-primary transition-colors">${(reading.frequency || 50).toFixed(2)}</span>
                                <span class="text-xs text-slate-500">Hz</span>
                            </div>
                        </div>
                        <div class="group p-3 bg-slate-800/40 rounded-xl border border-white/5 transition-all hover:bg-slate-800/60 hover:border-white/10">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Temp</span>
                            <div class="flex items-baseline gap-1">
                                <span class="text-xl font-bold text-white tabular-nums group-hover:text-primary transition-colors">${(reading.temperature || 0).toFixed(1)}</span>
                                <span class="text-xs text-slate-500">°C</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Identity & Pricing Compact Info -->
                    <div class="grid grid-cols-2 gap-4 pt-2">
                        <div class="space-y-2">
                             <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider">Identity</h4>
                             <div class="px-3 py-2 bg-slate-800/50 rounded-lg border border-white/5 text-xs text-slate-300 font-mono truncate">
                                Zone ${(reading.grid_zone_id || 0)}
                             </div>
                        </div>
                         <div class="space-y-2">
                             <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider">Market</h4>
                             <div class="flex gap-2">
                                <div class="px-2 py-1 bg-emerald-500/10 rounded border border-emerald-500/20 text-xs font-bold text-emerald-400">S: $${(reading.max_sell_price || 0).toFixed(2)}</div>
                                <div class="px-2 py-1 bg-rose-500/10 rounded border border-rose-500/20 text-xs font-bold text-rose-400">B: $${(reading.max_buy_price || 0).toFixed(2)}</div>
                             </div>
                        </div>
                    </div>

                    <!-- P2P Simulation Section -->
                    <div class="pt-4 border-t border-white/5">
                        <div class="p-5 bg-gradient-to-br from-purple-500/5 to-blue-500/5 rounded-2xl border border-purple-500/10">
                            <h3 class="text-sm font-bold text-purple-300 mb-4 flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                                P2P Trace Simulation
                            </h3>
                            
                            <div class="flex gap-3 mb-3">
                                <div class="w-1/3">
                                    <label class="text-[10px] font-bold text-purple-300/70 uppercase tracking-wider block mb-1.5 pl-1">Target Zone</label>
                                    <input type="number" id="p2p-target-zone-${reading.meter_id}" min="0" max="4" value="${(reading.grid_zone_id === 0 ? 1 : 0)}"
                                           class="w-full px-3 py-2 bg-slate-900/80 border border-purple-500/20 rounded-xl text-white text-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 focus:outline-none transition-all placeholder-slate-600">
                                </div>
                                <div class="w-2/3">
                                   <label class="text-[10px] font-bold text-purple-300/70 uppercase tracking-wider block mb-1.5 pl-1">Energy Amount</label>
                                    <input type="number" id="p2p-amount-${reading.meter_id}" min="1" value="10"
                                           class="w-full px-3 py-2 bg-slate-900/80 border border-purple-500/20 rounded-xl text-white text-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 focus:outline-none transition-all placeholder-slate-600">
                                </div>
                            </div>
                            
                            <button onclick="window.runP2PCheck('${reading.meter_id}', ${(reading.grid_zone_id || 0)})" 
                                    class="w-full py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white text-xs font-bold uppercase tracking-wider rounded-xl shadow-lg shadow-purple-900/20 transition-all hover:shadow-purple-900/40 active:scale-[0.98]">
                                    Run Simulation
                            </button>
                            <div id="p2p-result-${reading.meter_id}" class="hidden mt-3 p-3 bg-slate-900/80 rounded-xl text-xs border border-purple-500/20"></div>
                        </div>
                    </div>

                    <!-- Manual Controls Accordion-like -->
                    <div class="pt-4 border-t border-white/5">
                        <details class="group">
                            <summary class="flex items-center justify-between cursor-pointer list-none text-slate-400 hover:text-white transition-colors">
                                <h3 class="text-sm font-semibold">Manual Overrides</h3>
                                <svg class="w-4 h-4 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
                            </summary>
                            
                            <div class="pt-4 animate-in slide-in-from-top-2 duration-200">
                                <div class="grid grid-cols-2 gap-4 mb-4">
                                    <div>
                                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5 pl-1">Gen (kWh)</label>
                                        <input type="number" id="modal-gen-${reading.meter_id}" step="0.01" min="0" 
                                               value="${(reading.energy_generated || 0).toFixed(2)}"
                                               class="w-full px-3 py-2 bg-slate-800/50 border border-white/10 rounded-xl text-white text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all">
                                    </div>
                                    <div>
                                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5 pl-1">Cons (kWh)</label>
                                        <input type="number" id="modal-cons-${reading.meter_id}" step="0.01" min="0" 
                                               value="${(reading.energy_consumed || 0).toFixed(2)}"
                                               class="w-full px-3 py-2 bg-slate-800/50 border border-white/10 rounded-xl text-white text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all">
                                    </div>
                                </div>
                                <div class="flex gap-3">
                                    <button onclick="window.applyManualValues('${reading.meter_id}', 'modal-')" 
                                            class="flex-1 py-2 bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20 text-xs font-bold uppercase tracking-wide rounded-lg transition-colors">
                                        Apply
                                    </button>
                                    <button onclick="window.resetToAuto('${reading.meter_id}', 'modal-')" 
                                            class="flex-1 py-2 bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 border border-white/5 text-xs font-bold uppercase tracking-wide rounded-lg transition-colors">
                                        Reset
                                    </button>
                                </div>
                                
                                <!-- Hidden inputs -->
                                <input type="hidden" id="modal-batt-${reading.meter_id}" value="${(reading.battery_level || 0).toFixed(0)}">
                                <input type="hidden" id="modal-temp-${reading.meter_id}" value="${(reading.temperature || 25.0).toFixed(1)}">
                                <input type="hidden" id="modal-volt-${reading.meter_id}" value="${(reading.voltage || 240).toFixed(1)}">
                                <input type="hidden" id="modal-curr-${reading.meter_id}" value="${(reading.current || 0).toFixed(3)}">
                                <input type="hidden" id="modal-freq-${reading.meter_id}" value="${(reading.frequency || 50).toFixed(2)}">
                                <input type="hidden" id="modal-sell-${reading.meter_id}" value="${(reading.max_sell_price || 0.12).toFixed(2)}">
                                <input type="hidden" id="modal-buy-${reading.meter_id}" value="${(reading.max_buy_price || 0.28).toFixed(2)}">
                            </div>
                        </details>
                    </div>
                </div>
            </div>

            <!-- Footer Actions -->
            <footer class="flex items-center justify-between pt-6 border-t border-white/5">
                <div class="text-[10px] text-slate-600">
                    ID: ${reading.meter_id}
                </div>
                <button onclick="window.deleteMeter('${reading.meter_id}')" 
                        class="group inline-flex items-center gap-2 text-rose-500/70 hover:text-rose-400 hover:bg-rose-500/10 px-4 py-2 rounded-xl transition-all">
                    <svg class="opacity-50 group-hover:opacity-100 transition-opacity" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>
                    </svg>
                    <span class="text-xs font-bold tracking-wider">DELETE UNIT</span>
                </button>
            </footer>
        </article>
    `;
}
