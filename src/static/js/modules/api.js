// API Logic
import { allReadings, updateReading, setAllReadings, previousStats, setPreviousStats, removeReading } from './state.js';
import { addConsoleMessage, addConsoleReading, updateConsoleLineCount } from './console.js';
import { updateCharts, updateChartTheme } from './chart.js';
import {
    showStatusMessage,
    updateButtonStates,
    createMeterCard,
    updateMeterCardContent,
    toggleManualMode,
    closeAddMeterModal,
    closeMeterDetails
} from './ui.js';

let ws = null;
let reconnectInterval = null;

// API base URL - use port 8000 for Python backend
const API_BASE = 'http://localhost:8000';

// WebSocket
export function connectWebSocket() {
    const wsUrl = `ws://localhost:8000/ws`;

    console.log('Connecting to WebSocket:', wsUrl);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('Connected to WebSocket');
        updateConnectionStatus(true);
        addConsoleMessage('WebSocket connected successfully', 'status');
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            let readings = [];

            if (data.type === 'meter_reading') {
                readings = [data.reading];
            } else if (data.type === 'meter_readings') {
                readings = data.readings || [];
            } else if (Array.isArray(data)) {
                readings = data;
            } else {
                readings = [data];
            }

            updateReadings(readings);

            readings.forEach(reading => {
                addConsoleReading(reading);
            });
        } catch (e) {
            console.error('Error parsing WebSocket message:', e);
            addConsoleMessage(`Error parsing message: ${e.message}`, 'error');
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
        addConsoleMessage('WebSocket connection error', 'error');
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);
        addConsoleMessage('WebSocket connection lost', 'warning');

        if (!reconnectInterval) {
            reconnectInterval = setInterval(() => {
                console.log('Attempting to reconnect...');
                addConsoleMessage('Attempting to reconnect...', 'warning');
                connectWebSocket();
            }, 5000);
        }
    };
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    if (connected) {
        statusEl.innerHTML = '<span class="inline-block w-3 h-3 rounded-full bg-emerald-500 mr-2"></span><span class="font-semibold text-emerald-400">Connected</span>';
    } else {
        statusEl.innerHTML = '<span class="inline-block w-3 h-3 rounded-full bg-red-500 mr-2"></span><span class="font-semibold text-red-400">Disconnected</span>';
    }
}

// Readings Update Logic
function updateReadings(newReadings) {
    // Merge new readings into global state
    newReadings.forEach(newReading => {
        updateReading(newReading);
    });

    // Update statistics
    let totalGen = 0, totalCons = 0, totalSurp = 0, activeTraders = 0;

    allReadings.forEach(r => {
        totalGen += parseFloat(r.energy_generated || 0);
        totalCons += parseFloat(r.energy_consumed || 0);
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
        trendEl.innerHTML = `<span class="material-icons text-xs align-middle">arrow_upward</span> ${Math.abs(percentChange).toFixed(1)}%`;
        trendEl.className = 'text-xs font-semibold px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/20';
        changeEl.textContent = `+${isDecimal ? change.toFixed(2) : change}`;
        changeEl.className = 'text-xs text-emerald-400 font-semibold';
    } else if (change < 0) {
        trendEl.innerHTML = `<span class="material-icons text-xs align-middle">arrow_downward</span> ${Math.abs(percentChange).toFixed(1)}%`;
        trendEl.className = 'text-xs font-semibold px-2 py-1 bg-red-500/10 text-red-400 rounded-full border border-red-500/20';
        changeEl.textContent = `${isDecimal ? change.toFixed(2) : change}`;
        changeEl.className = 'text-xs text-red-400 font-semibold';
    } else {
        trendEl.innerHTML = `<span class="material-icons text-xs align-middle">remove</span> 0%`;
        trendEl.className = 'text-xs font-semibold px-2 py-1 bg-slate-700/50 text-slate-400 rounded-full border border-slate-600/50';
        changeEl.textContent = isDecimal ? '0.00' : '0';
        changeEl.className = 'text-xs text-slate-500 font-semibold';
    }
}

export function filterMeters() {
    const searchTerm = document.getElementById('meter-search').value.toLowerCase();
    const typeFilter = document.getElementById('meter-type-filter').value;
    const statusFilter = document.getElementById('meter-status-filter').value;
    const container = document.getElementById('readings-container');

    const filteredReadings = allReadings.filter(reading => {
        const matchesSearch = !searchTerm ||
            reading.meter_id.toLowerCase().includes(searchTerm) ||
            reading.location.toLowerCase().includes(searchTerm);

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

    document.getElementById('filtered-count').textContent = filteredReadings.length;

    if (filteredReadings.length === 0) {
        container.innerHTML = '<div class="col-span-full text-center text-gray-500 py-8">No meters match your filters</div>';
        return;
    }

    if (container.children.length === 1 && container.children[0].classList.contains('col-span-full')) {
        container.innerHTML = '';
    }

    const filteredIds = new Set(filteredReadings.map(r => r.meter_id));

    Array.from(container.children).forEach(child => {
        const id = child.id.replace('card-', '');
        if (!filteredIds.has(id)) {
            child.remove();
        }
    });

    filteredReadings.forEach(reading => {
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

// API Calls
export async function fetchStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();

        if (data.mode) {
            document.getElementById('simulator-mode').textContent = data.mode;
        }

        updateButtonStates({
            running: data.running,
            paused: data.paused,
            num_meters: data.num_meters
        });

    } catch (e) {
        console.error('Error fetching status:', e);
    }
}

export async function startSimulation() {
    try {
        showStatusMessage('Starting simulation...', 'info');
        addConsoleMessage('Starting simulation...', 'status');
        const response = await fetch(`${API_BASE}/api/control/start`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            showStatusMessage('Simulation started successfully', 'success');
            addConsoleMessage('Simulation started successfully', 'status');
            updateButtonStates(data.status);
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Failed to start: ${message}`, 'error');
            addConsoleMessage(`Failed to start: ${message}`, 'error');
        }
    } catch (e) {
        console.error('Error starting simulation:', e);
        showStatusMessage('Error starting simulation', 'error');
        addConsoleMessage('Error starting simulation', 'error');
    }
}

export async function stopSimulation() {
    try {
        showStatusMessage('Stopping simulation...', 'info');
        addConsoleMessage('Stopping simulation...', 'status');
        const response = await fetch(`${API_BASE}/api/control/stop`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            showStatusMessage('Simulation stopped', 'success');
            addConsoleMessage('Simulation stopped', 'status');
            updateButtonStates(data.status);
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Failed to stop: ${message}`, 'error');
            addConsoleMessage(`Failed to stop: ${message}`, 'error');
        }
    } catch (e) {
        console.error('Error stopping simulation:', e);
        showStatusMessage('Error stopping simulation', 'error');
        addConsoleMessage('Error stopping simulation', 'error');
    }
}

export async function pauseSimulation() {
    try {
        showStatusMessage('Pausing simulation...', 'info');
        addConsoleMessage('Pausing simulation...', 'status');
        const response = await fetch(`${API_BASE}/api/control/pause`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            showStatusMessage('Simulation paused', 'success');
            addConsoleMessage('Simulation paused', 'status');
            updateButtonStates(data.status);
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Failed to pause: ${message}`, 'error');
            addConsoleMessage(`Failed to pause: ${message}`, 'error');
        }
    } catch (e) {
        console.error('Error pausing simulation:', e);
        showStatusMessage('Error pausing simulation', 'error');
        addConsoleMessage('Error pausing simulation', 'error');
    }
}

export async function resumeSimulation() {
    try {
        showStatusMessage('Resuming simulation...', 'info');
        addConsoleMessage('Resuming simulation...', 'status');
        const response = await fetch(`${API_BASE}/api/control/resume`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            showStatusMessage('Simulation resumed', 'success');
            addConsoleMessage('Simulation resumed', 'status');
            updateButtonStates(data.status);
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Failed to resume: ${message}`, 'error');
            addConsoleMessage(`Failed to resume: ${message}`, 'error');
        }
    } catch (e) {
        console.error('Error resuming simulation:', e);
        showStatusMessage('Error resuming simulation', 'error');
        addConsoleMessage('Error resuming simulation', 'error');
    }
}

export async function restartSimulation() {
    try {
        showStatusMessage('Restarting simulation...', 'info');
        addConsoleMessage('Restarting simulation...', 'status');
        const response = await fetch(`${API_BASE}/api/control/restart`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            showStatusMessage('Simulation restarted', 'success');
            addConsoleMessage('Simulation restarted', 'status');
            updateButtonStates(data.status);
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Failed to restart: ${message}`, 'error');
            addConsoleMessage(`Failed to restart: ${message}`, 'error');
        }
    } catch (e) {
        console.error('Error restarting simulation:', e);
        showStatusMessage('Error restarting simulation', 'error');
        addConsoleMessage('Error restarting simulation', 'error');
    }
}

export async function updateMeterCount() {
    const meterCount = document.getElementById('meter-count').value;

    if (!meterCount || meterCount < 1 || meterCount > 1000) {
        showStatusMessage('Please enter a valid meter count (1-1000)', 'error');
        addConsoleMessage('Invalid meter count entered', 'error');
        return;
    }

    try {
        showStatusMessage(`Updating to ${meterCount} meters...`, 'info');
        addConsoleMessage(`Updating to ${meterCount} meters...`, 'status');
        const response = await fetch(`${API_BASE}/api/control/meters`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ num_meters: parseInt(meterCount) })
        });
        const data = await response.json();

        if (data.success) {
            showStatusMessage(`Updated to ${meterCount} meters. Restarting simulation...`, 'success');
            addConsoleMessage(`Updated to ${meterCount} meters. Restarting simulation...`, 'status');
            setTimeout(() => {
                fetchStatus();
            }, 1000);
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Failed to update meters: ${message}`, 'error');
            addConsoleMessage(`Failed to update meters: ${message}`, 'error');
        }
    } catch (e) {
        console.error('Error updating meter count:', e);
        showStatusMessage('Error updating meter count', 'error');
        addConsoleMessage('Error updating meter count', 'error');
    }
}

export async function applyManualValues(meterId, prefix = '') {
    const generation = parseFloat(document.getElementById(`${prefix}gen-${meterId}`).value);
    const consumption = parseFloat(document.getElementById(`${prefix}cons-${meterId}`).value);
    const battery = parseFloat(document.getElementById(`${prefix}batt-${meterId}`).value);

    // New fields
    const voltage = parseFloat(document.getElementById(`${prefix}volt-${meterId}`).value);
    const current = parseFloat(document.getElementById(`${prefix}curr-${meterId}`).value);
    const frequency = parseFloat(document.getElementById(`${prefix}freq-${meterId}`).value);
    const temperature = parseFloat(document.getElementById(`${prefix}temp-${meterId}`).value);
    const sellPrice = parseFloat(document.getElementById(`${prefix}sell-${meterId}`).value);
    const buyPrice = parseFloat(document.getElementById(`${prefix}buy-${meterId}`).value);

    try {
        const response = await fetch(`${API_BASE}/api/meters/${meterId}/override`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                energy_generated: generation,
                energy_consumed: consumption,
                battery_level: battery,
                voltage: voltage,
                current: current,
                frequency: frequency,
                temperature: temperature,
                max_sell_price: sellPrice,
                max_buy_price: buyPrice
            })
        });

        const data = await response.json();

        if (data.success) {
            showStatusMessage(`Manual values applied to ${meterId}`, 'success');
            addConsoleMessage(`Set ${meterId}: Gen=${generation}kWh, Cons=${consumption}kWh, Batt=${battery}%`, 'status');

            const card = document.getElementById(`${prefix}card-${meterId}`);
            if (card) card.classList.add('ring-2', 'ring-orange-400');
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(message, 'error');
        }
    } catch (error) {
        console.error('Error applying manual values:', error);
        showStatusMessage('Error applying manual values', 'error');
    }
}

export async function resetToAuto(meterId, prefix = '') {
    try {
        const response = await fetch(`${API_BASE}/api/meters/${meterId}/override`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showStatusMessage(`${meterId} returned to auto mode`, 'success');
            addConsoleMessage(`Reset ${meterId} to auto mode`, 'status');

            const card = document.getElementById(`${prefix}card-${meterId}`);
            if (card) card.classList.remove('ring-2', 'ring-orange-400');

            toggleManualMode(meterId, prefix);
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(message, 'error');
        }
    } catch (error) {
        console.error('Error resetting to auto:', error);
        showStatusMessage('Error resetting to auto', 'error');
    }
}

export async function submitAddMeter(event) {
    event.preventDefault();

    const meterType = document.getElementById('meter-type').value;
    const location = document.getElementById('meter-location').value;
    const latitude = document.getElementById('meter-latitude').value;
    const longitude = document.getElementById('meter-longitude').value;

    // Get optional fields based on type
    let solarCapacity = 0;
    let batteryCapacity = 0;

    if (meterType !== 'Grid_Consumer' && meterType !== 'Battery_Storage') {
        solarCapacity = parseFloat(document.getElementById('solar-capacity').value) || 0.0;
    }

    if (meterType !== 'Grid_Consumer' && meterType !== 'Solar_Prosumer') {
        batteryCapacity = parseFloat(document.getElementById('battery-capacity').value) || 0.0;
    }

    const tradingPreference = document.getElementById('trading-preference').value;

    try {
        showStatusMessage('Adding new meter...', 'info');
        addConsoleMessage(`Adding new ${meterType} meter at ${location}...`, 'status');

        const payload = {
            meter_type: meterType,
            location: location,
            solar_capacity: solarCapacity,
            battery_capacity: batteryCapacity,
            trading_preference: tradingPreference
        };

        if (latitude) payload.latitude = parseFloat(latitude);
        if (longitude) payload.longitude = parseFloat(longitude);

        const response = await fetch(`${API_BASE}/api/meters/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.success) {
            showStatusMessage(`Successfully added ${meterType} meter! Total meters: ${data.total_meters}`, 'success');
            addConsoleMessage(`Added meter ${data.meter.meter_id} (${meterType}) at ${location}`, 'status');
            closeAddMeterModal();

            // Refresh status immediately
            fetchStatus();
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Error: ${message}`, 'error');
            addConsoleMessage(`Failed to add meter: ${message}`, 'error');
        }
    } catch (error) {
        console.error('Error adding meter:', error);
        showStatusMessage('Failed to add meter. Check console.', 'error');
        addConsoleMessage(`Error adding meter: ${error.message}`, 'error');
    }
}

export async function deleteMeter(meterId) {
    if (!confirm('Are you sure you want to remove this meter? This cannot be undone.')) {
        return;
    }

    console.log(`[Debug] deleteMeter proceeding for ${meterId}`);

    try {
        addConsoleMessage(`Removing meter ${meterId}...`, 'status');

        const response = await fetch(`${API_BASE}/api/meters/${meterId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showStatusMessage(`Successfully removed meter!`, 'success');
            addConsoleMessage(`Removed meter ${meterId}`, 'status');

            // 1. Remove from global state so it doesn't reappear
            removeReading(meterId);

            // 2. Close details modal if it's open for this meter
            closeMeterDetails();

            // 3. Remove card from UI immediately
            const card = document.getElementById(`card-${meterId}`);
            if (card) {
                card.style.opacity = '0';
                setTimeout(() => card.remove(), 300); // Fade out effect
            } else {
                // Try searching with prefix if not found directly
                const prefixedCard = document.querySelector(`[id$="card-${meterId}"]`);
                if (prefixedCard) prefixedCard.remove();
            }

            // Refresh status
            fetchStatus();
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Error: ${message}`, 'error');
            addConsoleMessage(`Failed to remove meter: ${message}`, 'error');
        }
    } catch (error) {
        console.error('Error deleting meter:', error);
        showStatusMessage('Error deleting meter', 'error');
        addConsoleMessage(`Error removing meter: ${error.message}`, 'error');
    }
}
