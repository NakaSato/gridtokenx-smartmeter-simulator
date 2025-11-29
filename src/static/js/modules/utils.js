// Utility Functions

export function formatNumber(num, decimals = 2) {
    return (num || 0).toFixed(decimals);
}

export function formatCurrency(num) {
    return `$${(num || 0).toFixed(2)}`;
}

export function formatDate(date) {
    return new Date(date).toLocaleTimeString();
}

export function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

import { allReadings } from './state.js';
import { addConsoleMessage } from './console.js';
import { showStatusMessage } from './ui.js';

export function exportData() {
    const format = prompt('Export format: CSV or JSON?', 'CSV').toUpperCase();

    if (format === 'CSV') {
        exportCSV();
    } else if (format === 'JSON') {
        exportJSON();
    } else {
        showStatusMessage('Invalid format. Please choose CSV or JSON', 'error');
    }
}

function exportCSV() {
    if (allReadings.length === 0) {
        showStatusMessage('No data to export', 'warning');
        return;
    }

    const headers = ['Meter ID', 'Type', 'Location', 'Generation (kWh)', 'Consumption (kWh)',
        'Surplus (kWh)', 'Deficit (kWh)', 'Battery (%)', 'Weather', 'Timestamp'];

    const rows = allReadings.map(r => [
        r.meter_id,
        r.meter_type,
        r.location,
        (r.energy_generated || 0).toFixed(2),
        (r.energy_consumed || 0).toFixed(2),
        (r.surplus_energy || 0).toFixed(2),
        (r.deficit_energy || 0).toFixed(2),
        (r.battery_level || 0).toFixed(1),
        r.weather_condition || '-',
        r.timestamp || new Date().toISOString()
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    downloadFile(csv, 'meter-readings.csv', 'text/csv');

    showStatusMessage(`Exported ${allReadings.length} meter readings as CSV`, 'success');
    addConsoleMessage(`Exported ${allReadings.length} readings to CSV`, 'status');
}

function exportJSON() {
    if (allReadings.length === 0) {
        showStatusMessage('No data to export', 'warning');
        return;
    }

    const json = JSON.stringify({
        exported_at: new Date().toISOString(),
        total_meters: allReadings.length,
        readings: allReadings
    }, null, 2);

    downloadFile(json, 'meter-readings.json', 'application/json');

    showStatusMessage(`Exported ${allReadings.length} meter readings as JSON`, 'success');
    addConsoleMessage(`Exported ${allReadings.length} readings to JSON`, 'status');
}
