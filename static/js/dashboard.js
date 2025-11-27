import { initDarkMode, toggleDarkMode, openAddMeterModal, closeAddMeterModal, closeMeterDetails, toggleManualMode } from './modules/ui.js';
import { initEnergyChart, initMarketChart } from './modules/chart.js';
import { connectWebSocket, fetchStatus, startSimulation, stopSimulation, pauseSimulation, resumeSimulation, restartSimulation, updateMeterCount, submitAddMeter, applyManualValues, resetToAuto, deleteMeter } from './modules/api.js';
import { clearConsole, toggleConsoleScroll } from './modules/console.js';

// Re-export functions to window for HTML onclick handlers
window.toggleDarkMode = toggleDarkMode;
window.startSimulation = startSimulation;
window.stopSimulation = stopSimulation;
window.pauseSimulation = pauseSimulation;
window.resumeSimulation = resumeSimulation;
window.restartSimulation = restartSimulation;
window.updateMeterCount = updateMeterCount;
window.openAddMeterModal = openAddMeterModal;
window.closeAddMeterModal = closeAddMeterModal;
window.submitAddMeter = submitAddMeter;
window.closeMeterDetails = closeMeterDetails;
window.toggleManualMode = toggleManualMode;
window.applyManualValues = applyManualValues;
window.resetToAuto = resetToAuto;
window.deleteMeter = deleteMeter;
window.clearConsole = clearConsole;
window.toggleConsoleScroll = toggleConsoleScroll;

// Export Data Functions
import { exportData } from './modules/utils.js';
window.exportData = exportData;

// Initialize
function init() {
    initDarkMode();
    initEnergyChart();
    initMarketChart();
    connectWebSocket();
    fetchStatus();

    // Add initial console message
    import('./modules/console.js').then(module => {
        module.addConsoleMessage('Smart Meter Simulator Dashboard initialized', 'status');
        module.addConsoleMessage('Waiting for real-time meter data...', 'info');
    });

    setInterval(fetchStatus, 10000);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
