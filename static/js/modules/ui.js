// UI Logic
import { addConsoleMessage } from './console.js';
import { updateChartTheme } from './chart.js';

// Dark Mode
export function toggleDarkMode() {
    const html = document.documentElement;
    const isDark = html.classList.toggle('dark');
    localStorage.setItem('darkMode', isDark);

    const icon = document.getElementById('theme-icon');
    if (icon) icon.textContent = isDark ? 'light_mode' : 'dark_mode';

    updateChartTheme(isDark);
    addConsoleMessage(`Switched to ${isDark ? 'dark' : 'light'} mode`, 'status');
}

export function initDarkMode() {
    const isDark = localStorage.getItem('darkMode') === 'true';
    if (isDark) {
        document.documentElement.classList.add('dark');
        const icon = document.getElementById('theme-icon');
        if (icon) icon.textContent = 'light_mode';
    }
}

// Status Message
export function showStatusMessage(message, type = 'info') {
    const messageEl = document.getElementById('status-message');
    const textEl = document.getElementById('status-message-text');
    const colors = {
        'success': 'bg-green-100 text-green-800 border-green-200',
        'error': 'bg-red-100 text-red-800 border-red-200',
        'warning': 'bg-yellow-100 text-yellow-800 border-yellow-200',
        'info': 'bg-blue-100 text-blue-800 border-blue-200'
    };

    // Reset classes
    messageEl.className = `hidden mt-4 p-4 rounded shadow-lg text-sm flex items-center justify-between`;

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
            pauseBtn.classList.remove('hidden');
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
export function createMeterCard(reading) {
    const meterTypeColors = {
        'Solar_Prosumer': 'border-yellow-500',
        'Grid_Consumer': 'border-blue-500',
        'Hybrid_Prosumer': 'border-purple-500',
        'Battery_Storage': 'border-green-500'
    };

    const meterTypeBadgeClasses = {
        'Solar_Prosumer': 'bg-yellow-100 text-yellow-700',
        'Grid_Consumer': 'bg-blue-100 text-blue-700',
        'Hybrid_Prosumer': 'bg-purple-100 text-purple-700',
        'Battery_Storage': 'bg-green-100 text-green-700'
    };

    const meterTypeIcons = {
        'Solar_Prosumer': 'wb_sunny',
        'Grid_Consumer': 'home',
        'Hybrid_Prosumer': 'electric_bolt',
        'Battery_Storage': 'battery_charging_full'
    };

    const borderColor = meterTypeColors[reading.meter_type] || 'border-gray-400';
    const typeClass = meterTypeBadgeClasses[reading.meter_type] || 'bg-gray-100 text-gray-600';
    const typeIcon = meterTypeIcons[reading.meter_type] || 'device_unknown';

    const isSelling = (reading.surplus_energy || 0) > 0;
    const isBuying = (reading.deficit_energy || 0) > 0;

    return `
        <div class="bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-200 border border-gray-100 overflow-hidden group" id="card-${reading.meter_id}">
            <!-- Header -->
            <div class="p-4 border-b border-gray-50 bg-gray-50/50">
                <div class="flex justify-between items-start">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-lg ${typeClass} flex items-center justify-center shadow-sm">
                            <span class="material-icons text-xl">${typeIcon}</span>
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 text-sm leading-tight">${reading.meter_id}</h3>
                            <p class="text-xs text-gray-500 truncate max-w-[120px]" title="${reading.location}">
                                ${reading.location}
                            </p>
                        </div>
                    </div>
                    <div class="flex flex-col items-end gap-1">
                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${reading.is_connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'} flex items-center gap-1">
                            <span class="w-1.5 h-1.5 rounded-full ${reading.is_connected ? 'bg-green-500' : 'bg-red-500'}"></span>
                            ${reading.is_connected ? 'Online' : 'Offline'}
                        </span>
                        <span class="text-[10px] text-gray-400 font-mono">
                            ${reading.latitude ? `${reading.latitude.toFixed(2)}, ${reading.longitude.toFixed(2)}` : ''}
                        </span>
                    </div>
                </div>
            </div>

            <!-- Content -->
            <div class="p-4">
                <!-- Auto Mode Display -->
                <div id="auto-${reading.meter_id}" class="space-y-4">
                    <!-- Metrics Grid -->
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-gray-50 rounded-lg p-2.5 border border-gray-100">
                            <div class="flex items-center gap-1.5 mb-1">
                                <span class="material-icons text-[14px] text-green-500">wb_sunny</span>
                                <span class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Gen</span>
                            </div>
                            <span class="text-lg font-bold text-gray-800 val-gen">${(reading.energy_generated || 0).toFixed(2)}</span>
                            <span class="text-[10px] text-gray-400">kWh</span>
                        </div>
                        <div class="bg-gray-50 rounded-lg p-2.5 border border-gray-100">
                            <div class="flex items-center gap-1.5 mb-1">
                                <span class="material-icons text-[14px] text-blue-500">bolt</span>
                                <span class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Cons</span>
                            </div>
                            <span class="text-lg font-bold text-gray-800 val-cons">${(reading.energy_consumed || 0).toFixed(2)}</span>
                            <span class="text-[10px] text-gray-400">kWh</span>
                        </div>
                    </div>

                    <!-- Battery & Temp -->
                    <div class="space-y-3">
                        <div>
                            <div class="flex justify-between items-end mb-1">
                                <div class="flex items-center gap-1.5">
                                    <span class="material-icons text-[14px] text-gray-400">battery_full</span>
                                    <span class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Battery</span>
                                </div>
                                <span class="text-xs font-bold text-gray-700 val-batt-text">${(reading.battery_level || 0).toFixed(1)}%</span>
                            </div>
                            <div class="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                                <div class="bg-green-500 h-1.5 rounded-full transition-all duration-500 val-batt-bar" 
                                     style="width: ${(reading.battery_level || 0)}%"></div>
                            </div>
                        </div>
                        
                        <div class="flex justify-between items-center text-xs text-gray-500 border-t border-dashed border-gray-200 pt-2">
                            <div class="flex items-center gap-1" title="Temperature">
                                <span class="material-icons text-[14px] text-gray-400">thermostat</span>
                                <span class="val-temp font-medium">${(reading.temperature || 0).toFixed(1)}°C</span>
                            </div>
                            <div class="flex items-center gap-1" title="Net Carbon Emission">
                                <span class="material-icons text-[14px] text-gray-400">eco</span>
                                <span class="font-medium">${(reading.net_emission || 0).toFixed(3)} kg</span>
                            </div>
                        </div>
                    </div>

                    <!-- Status Banners -->
                    <div class="status-container min-h-[40px] flex items-center">
                        ${isSelling ? `
                            <div class="w-full text-xs bg-green-50 text-green-700 px-3 py-2 rounded-lg border border-green-100 flex justify-between items-center">
                                <div class="flex items-center gap-1.5">
                                    <span class="material-icons text-[14px]">arrow_upward</span>
                                    <span class="font-bold">Selling</span>
                                </div>
                                <span class="font-mono font-medium">${(reading.surplus_energy || 0).toFixed(2)} kWh @ $${(reading.max_sell_price || 0).toFixed(2)}</span>
                            </div>
                        ` : ''}
                        ${isBuying ? `
                            <div class="w-full text-xs bg-orange-50 text-orange-700 px-3 py-2 rounded-lg border border-orange-100 flex justify-between items-center">
                                <div class="flex items-center gap-1.5">
                                    <span class="material-icons text-[14px]">arrow_downward</span>
                                    <span class="font-bold">Buying</span>
                                </div>
                                <span class="font-mono font-medium">${(reading.deficit_energy || 0).toFixed(2)} kWh @ $${(reading.max_buy_price || 0).toFixed(2)}</span>
                            </div>
                        ` : ''}
                        ${!isSelling && !isBuying ? `
                            <div class="w-full text-xs text-gray-400 text-center italic py-2">
                                System Balanced
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <!-- Manual Mode Controls (Hidden by default) -->
                <div id="manual-${reading.meter_id}" class="hidden space-y-3">
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <label class="text-[10px] text-gray-500 uppercase font-bold block mb-1">Gen (kWh)</label>
                            <input type="number" id="gen-${reading.meter_id}" step="0.01" min="0" 
                                   value="${(reading.energy_generated || 0).toFixed(2)}"
                                   class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all">
                        </div>
                        <div>
                            <label class="text-[10px] text-gray-500 uppercase font-bold block mb-1">Cons (kWh)</label>
                            <input type="number" id="cons-${reading.meter_id}" step="0.01" min="0" 
                                   value="${(reading.energy_consumed || 0).toFixed(2)}"
                                   class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all">
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <label class="text-[10px] text-gray-500 uppercase font-bold block mb-1">Battery %</label>
                            <input type="number" id="batt-${reading.meter_id}" step="1" min="0" max="100" 
                                   value="${(reading.battery_level || 0).toFixed(0)}"
                                   class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all">
                        </div>
                        <div>
                            <label class="text-[10px] text-gray-500 uppercase font-bold block mb-1">Temp (°C)</label>
                            <input type="number" id="temp-${reading.meter_id}" step="0.1" 
                                   value="${(reading.temperature || 25.0).toFixed(1)}"
                                   class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all">
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-2 pt-1">
                         <button onclick="window.applyManualValues('${reading.meter_id}')" 
                                class="flex-1 px-3 py-2 bg-indigo-600 text-white text-xs font-bold uppercase tracking-wide rounded hover:bg-indigo-700 transition-colors shadow-sm">
                            Apply
                        </button>
                        <button onclick="window.resetToAuto('${reading.meter_id}')" 
                                class="px-3 py-2 border border-gray-200 text-gray-600 text-xs font-bold uppercase tracking-wide rounded hover:bg-gray-50 transition-colors">
                            Reset
                        </button>
                    </div>
                    
                    <!-- Hidden inputs for extra fields to prevent errors -->
                    <input type="hidden" id="volt-${reading.meter_id}" value="${(reading.voltage || 240).toFixed(1)}">
                    <input type="hidden" id="curr-${reading.meter_id}" value="${(reading.current || 0).toFixed(3)}">
                    <input type="hidden" id="freq-${reading.meter_id}" value="${(reading.frequency || 50).toFixed(2)}">
                    <input type="hidden" id="sell-${reading.meter_id}" value="${(reading.max_sell_price || 0.12).toFixed(2)}">
                    <input type="hidden" id="buy-${reading.meter_id}" value="${(reading.max_buy_price || 0.28).toFixed(2)}">
                </div>
            </div>

            <!-- Footer Actions -->
            <div class="px-4 py-3 bg-gray-50/50 border-t border-gray-50 flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <button onclick="window.toggleManualMode('${reading.meter_id}')" 
                        id="mode-btn-${reading.meter_id}"
                        class="text-xs font-bold text-indigo-600 hover:text-indigo-800 uppercase tracking-wider flex items-center gap-1">
                    <span class="material-icons text-[14px]">tune</span> Manual
                </button>
                <button onclick="window.deleteMeter('${reading.meter_id}')" 
                        class="text-xs font-bold text-red-500 hover:text-red-700 uppercase tracking-wider flex items-center gap-1">
                    <span class="material-icons text-[14px]">delete</span> Remove
                </button>
            </div>
        </div>
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
    if (battBarEl) battBarEl.style.width = `${(reading.battery_level || 0)}%`;

    const tempEl = card.querySelector('.val-temp');
    if (tempEl) tempEl.textContent = `${(reading.temperature || 0).toFixed(1)}°C`;

    // Update status banners
    const statusContainer = card.querySelector('.status-container');
    if (statusContainer) {
        statusContainer.innerHTML = '';
        const isSelling = (reading.surplus_energy || 0) > 0;
        const isBuying = (reading.deficit_energy || 0) > 0;

        if (isSelling) {
            statusContainer.innerHTML = `
                <div class="w-full text-xs bg-green-50 text-green-700 px-3 py-2 rounded-lg border border-green-100 flex justify-between items-center">
                    <div class="flex items-center gap-1.5">
                        <span class="material-icons text-[14px]">arrow_upward</span>
                        <span class="font-bold">Selling</span>
                    </div>
                    <span class="font-mono font-medium">${(reading.surplus_energy || 0).toFixed(2)} kWh @ $${(reading.max_sell_price || 0).toFixed(2)}</span>
                </div>
            `;
        } else if (isBuying) {
            statusContainer.innerHTML = `
                <div class="w-full text-xs bg-orange-50 text-orange-700 px-3 py-2 rounded-lg border border-orange-100 flex justify-between items-center">
                    <div class="flex items-center gap-1.5">
                        <span class="material-icons text-[14px]">arrow_downward</span>
                        <span class="font-bold">Buying</span>
                    </div>
                    <span class="font-mono font-medium">${(reading.deficit_energy || 0).toFixed(2)} kWh @ $${(reading.max_buy_price || 0).toFixed(2)}</span>
                </div>
            `;
        } else {
            statusContainer.innerHTML = `
                <div class="w-full text-xs text-gray-400 text-center italic py-2">
                    System Balanced
                </div>
            `;
        }
    }
}

export function toggleManualMode(meterId) {
    const autoDiv = document.getElementById(`auto-${meterId}`);
    const manualDiv = document.getElementById(`manual-${meterId}`);
    const btn = document.getElementById(`mode-btn-${meterId}`);

    if (manualDiv.classList.contains('hidden')) {
        // Switch to manual mode
        autoDiv.classList.add('hidden');
        manualDiv.classList.remove('hidden');
        btn.textContent = 'Auto';
        btn.classList.remove('border-indigo-600', 'text-indigo-600', 'hover:bg-indigo-50');
        btn.classList.add('border-orange-500', 'text-orange-500', 'hover:bg-orange-50');
    } else {
        // Switch to auto mode
        manualDiv.classList.add('hidden');
        autoDiv.classList.remove('hidden');
        btn.textContent = 'Manual';
        btn.classList.remove('border-orange-500', 'text-orange-500', 'hover:bg-orange-50');
        btn.classList.add('border-indigo-600', 'text-indigo-600', 'hover:bg-indigo-50');
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
