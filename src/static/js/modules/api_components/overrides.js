import { showStatusMessage, toggleManualMode } from '../ui.js';
import { addConsoleMessage } from '../console.js';
import apiService from '../../services/apiService.js';

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
        const data = await apiService.setMeterOverride(meterId, {
            energy_generated: generation,
            energy_consumed: consumption,
            battery_level: battery,
            voltage: voltage,
            current: current,
            frequency: frequency,
            temperature: temperature,
            max_sell_price: sellPrice,
            max_buy_price: buyPrice
        });

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
        const message = error.message || 'Unknown error';
        showStatusMessage(`Error applying manual values: ${message}`, 'error');
    }
}

export async function resetToAuto(meterId, prefix = '') {
    try {
        const data = await apiService.clearMeterOverride(meterId);

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
