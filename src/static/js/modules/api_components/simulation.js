import { showStatusMessage, updateButtonStates } from '../ui.js';
import { addConsoleMessage } from '../console.js';

const API_BASE = window.location.origin;

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
