import { showStatusMessage, closeAddMeterModal, closeMeterDetails } from '../ui.js';
import { addConsoleMessage } from '../console.js';
import { fetchStatus } from './simulation.js';
import { removeReading } from '../state.js';
import { filterMeters } from './readings.js';
import apiService from '../../services/apiService.js';

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
    const meterId = document.getElementById('meter-id').value;
    const walletAddress = document.getElementById('meter-wallet').value;

    try {
        showStatusMessage('Adding new meter...', 'info');
        addConsoleMessage(`Adding new ${meterType} meter at ${location}...`, 'status');

        const payload = {
            meter_type: meterType,
            location: location,
            solar_capacity: solarCapacity,
            battery_capacity: batteryCapacity,
            trading_preference: tradingPreference,
            meter_id: meterId || null,
            wallet_address: walletAddress || null
        };

        if (latitude) payload.latitude = parseFloat(latitude);
        if (longitude) payload.longitude = parseFloat(longitude);

        const data = await apiService.addMeter(payload);

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
        const message = error.message || 'Unknown error';
        showStatusMessage(`Failed to add meter: ${message}`, 'error');
        addConsoleMessage(`Error adding meter: ${message}`, 'error');
    }
}

export async function deleteMeter(meterId) {
    console.log(`[Debug] deleteMeter proceeding for ${meterId}`);

    try {
        addConsoleMessage(`Removing meter ${meterId}...`, 'status');

        const data = await apiService.deleteMeter(meterId);
        console.log(`[Debug] deleteMeter response data:`, data);

        if (data.success) {
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

            // 4. Force a UI filter refresh to handle any cards not found by ID
            filterMeters();

            // Refresh status from server
            fetchStatus();
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Error: ${message}`, 'error');
            addConsoleMessage(`Failed to remove meter: ${message}`, 'error');
        }
    } catch (error) {
        const message = error.message || 'Unknown error';
        showStatusMessage(`Error deleting meter: ${message}`, 'error');
        addConsoleMessage(`Error removing meter: ${message}`, 'error');
    }
}
