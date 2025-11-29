// Import styles
import '@css/dashboard.css';

// Import UI functions
import {
    initDarkMode,
    toggleDarkMode,
    openAddMeterModal,
    closeAddMeterModal,
    closeMeterDetails,
    toggleManualMode,
    openMeterDetails,
    initLucideIcons,
} from './modules/ui.js';

// Import chart functions
import { initEnergyChart, initMarketChart } from './modules/chart.js';

// Import API functions
import {
    connectWebSocket,
    fetchStatus,
    startSimulation,
    stopSimulation,
    pauseSimulation,
    resumeSimulation,
    restartSimulation,
    updateMeterCount,
    submitAddMeter,
    applyManualValues,
    resetToAuto,
    deleteMeter,
} from './modules/api.js';

// Import console functions
import { clearConsole, toggleConsoleScroll, addConsoleMessage } from './modules/console.js';

// Import utility functions
import { exportData } from './modules/utils.js';

// Re-export functions to window for HTML onclick handlers
// Note: This is a temporary bridge for legacy HTML onclick attributes
// TODO: Migrate to proper event listeners in the future
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
window.openMeterDetails = openMeterDetails;
window.toggleManualMode = toggleManualMode;
window.applyManualValues = applyManualValues;
window.resetToAuto = resetToAuto;
window.deleteMeter = deleteMeter;
window.clearConsole = clearConsole;
window.toggleConsoleScroll = toggleConsoleScroll;
window.exportData = exportData;

/**
 * Initialize the dashboard application
 */
function init() {
    try {
        // Initialize dark mode
        initDarkMode();

        // Initialize Lucide icons
        initLucideIcons();

        // Initialize charts
        initEnergyChart();
        initMarketChart();

        // Connect to WebSocket for real-time updates
        connectWebSocket();

        // Fetch initial status
        fetchStatus();

        // Add initial console messages
        addConsoleMessage('Smart Meter Simulator Dashboard initialized', 'status');
        addConsoleMessage('Waiting for real-time meter data...', 'info');

        // Set up periodic status updates
        setInterval(fetchStatus, 10000);

        console.log('Dashboard initialized successfully');
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        addConsoleMessage(`Initialization error: ${error.message}`, 'error');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Handle page visibility changes to pause/resume updates
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('Page hidden - consider pausing updates');
    } else {
        console.log('Page visible - resuming updates');
        fetchStatus();
    }
});

// Handle errors globally
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    addConsoleMessage(`Error: ${event.error?.message || 'Unknown error'}`, 'error');
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    addConsoleMessage(`Promise rejection: ${event.reason?.message || 'Unknown error'}`, 'error');
});
