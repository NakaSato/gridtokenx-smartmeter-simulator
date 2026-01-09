import { showStatusMessage, updateButtonStates } from '../ui.js';
import { addConsoleMessage } from '../console.js';
import apiService from '../../services/apiService.js';

export async function fetchStatus() {
    try {
        const data = await apiService.getStatus();

        if (data.mode) {
            document.getElementById('simulator-mode').textContent = data.mode;
        }

        updateButtonStates({
            running: data.running,
            paused: data.paused,
            num_meters: data.num_meters
        });

    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

export async function startSimulation() {
    try {
        showStatusMessage('Starting simulation...', 'info');
        addConsoleMessage('Starting simulation...', 'status');

        const data = await apiService.startSimulation();

        if (data.success) {
            showStatusMessage('Simulation started successfully', 'success');
            addConsoleMessage('Simulation started successfully', 'status');
            updateButtonStates(data.status);
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Failed to start: ${message}`, 'error');
            addConsoleMessage(`Failed to start: ${message}`, 'error');
        }
    } catch (error) {
        const message = error.message || 'Unknown error';
        showStatusMessage(`Error starting simulation: ${message}`, 'error');
        addConsoleMessage(`Error starting simulation: ${message}`, 'error');
    }
}

export async function stopSimulation() {
    try {
        showStatusMessage('Stopping simulation...', 'info');
        addConsoleMessage('Stopping simulation...', 'status');

        const data = await apiService.stopSimulation();

        if (data.success) {
            showStatusMessage('Simulation stopped', 'success');
            addConsoleMessage('Simulation stopped', 'status');
            updateButtonStates(data.status);
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Failed to stop: ${message}`, 'error');
            addConsoleMessage(`Failed to stop: ${message}`, 'error');
        }
    } catch (error) {
        const message = error.message || 'Unknown error';
        showStatusMessage(`Error stopping simulation: ${message}`, 'error');
        addConsoleMessage(`Error stopping simulation: ${message}`, 'error');
    }
}

export async function pauseSimulation() {
    try {
        showStatusMessage('Pausing simulation...', 'info');
        addConsoleMessage('Pausing simulation...', 'status');

        const data = await apiService.pauseSimulation();

        if (data.success) {
            showStatusMessage('Simulation paused', 'success');
            addConsoleMessage('Simulation paused', 'status');
            updateButtonStates(data.status);
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Failed to pause: ${message}`, 'error');
            addConsoleMessage(`Failed to pause: ${message}`, 'error');
        }
    } catch (error) {
        const message = error.message || 'Unknown error';
        showStatusMessage(`Error pausing simulation: ${message}`, 'error');
        addConsoleMessage(`Error pausing simulation: ${message}`, 'error');
    }
}

export async function resumeSimulation() {
    try {
        showStatusMessage('Resuming simulation...', 'info');
        addConsoleMessage('Resuming simulation...', 'status');

        const data = await apiService.resumeSimulation();

        if (data.success) {
            showStatusMessage('Simulation resumed', 'success');
            addConsoleMessage('Simulation resumed', 'status');
            updateButtonStates(data.status);
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Failed to resume: ${message}`, 'error');
            addConsoleMessage(`Failed to resume: ${message}`, 'error');
        }
    } catch (error) {
        const message = error.message || 'Unknown error';
        showStatusMessage(`Error resuming simulation: ${message}`, 'error');
        addConsoleMessage(`Error resuming simulation: ${message}`, 'error');
    }
}

export async function restartSimulation() {
    try {
        showStatusMessage('Restarting simulation...', 'info');
        addConsoleMessage('Restarting simulation...', 'status');

        const data = await apiService.restartSimulation();

        if (data.success) {
            showStatusMessage('Simulation restarted', 'success');
            addConsoleMessage('Simulation restarted', 'status');
            updateButtonStates(data.status);
        } else {
            const message = data.detail || data.message || 'Unknown error';
            showStatusMessage(`Failed to restart: ${message}`, 'error');
            addConsoleMessage(`Failed to restart: ${message}`, 'error');
        }
    } catch (error) {
        const message = error.message || 'Unknown error';
        showStatusMessage(`Error restarting simulation: ${message}`, 'error');
        addConsoleMessage(`Error restarting simulation: ${message}`, 'error');
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

        const data = await apiService.updateMeterCount(parseInt(meterCount));

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
    } catch (error) {
        const message = error.message || 'Unknown error';
        showStatusMessage(`Error updating meter count: ${message}`, 'error');
        addConsoleMessage(`Error updating meter count: ${message}`, 'error');
    }
}
