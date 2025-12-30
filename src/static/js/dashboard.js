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
    testP2PTransaction,
    nextPage,
    prevPage,
    changeViewMode,
    changeItemsPerPage,
} from './modules/api.js';

// Import console functions
import { clearConsole, toggleConsoleScroll, addConsoleMessage } from './modules/console.js';

// Import utility functions
import { exportData } from './modules/utils.js';
import { QuantumDashboard } from './modules/quantum.js';

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
window.nextPage = nextPage;
window.prevPage = prevPage;
window.changeViewMode = changeViewMode;
window.changeItemsPerPage = changeItemsPerPage;


// New P2P Check Function
window.runP2PCheck = async (meterId, currentZone) => {
    const targetZone = document.getElementById(`p2p-target-zone-${meterId}`).value;
    const amount = document.getElementById(`p2p-amount-${meterId}`).value;
    const resultDiv = document.getElementById(`p2p-result-${meterId}`);

    resultDiv.innerHTML = '<span>Analyzing Grid Physics...</span>';
    resultDiv.className = 'mt-3 p-3 rounded-xl text-sm bg-secondary/50 text-muted-foreground';
    resultDiv.classList.remove('hidden');

    try {
        const cost = await testP2PTransaction(targetZone, currentZone, amount);

        if (cost.is_grid_compliant) {
            resultDiv.className = 'mt-3 p-3 rounded-xl text-sm bg-emerald-500/10 border border-emerald-500/20 text-emerald-400';
            resultDiv.innerHTML = `
                <div class="flex items-center gap-2 mb-1">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    <span class="font-bold">Grid Compliant</span>
                </div>
                <div class="flex justify-between text-xs mt-2">
                   <span>Energy Cost:</span>
                   <span class="font-mono text-foreground">${cost.energy_cost.toFixed(2)} THB</span>
                </div>
                 <div class="flex justify-between text-xs">
                   <span>Wheeling:</span>
                   <span class="font-mono text-foreground">${cost.wheeling_charge.toFixed(2)} THB</span>
                </div>
                <div class="flex justify-between font-bold border-t border-emerald-500/20 pt-1 mt-1">
                   <span>Total:</span>
                   <span>${cost.total_cost.toFixed(2)} THB</span>
                </div>
            `;
        } else {
            resultDiv.className = 'mt-3 p-3 rounded-xl text-sm bg-red-500/10 border border-red-500/20 text-red-500';
            resultDiv.innerHTML = `
                <div class="flex items-center gap-2 mb-1">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" x2="9" y1="9" y2="15"/><line x1="9" x2="15" y1="9" y2="15"/></svg>
                    <span class="font-bold">Trade Rejected</span>
                </div>
                <p class="text-xs text-red-400 mt-1">${cost.grid_violation_reason || "Grid Instability Detected"}</p>
                 <p class="text-xs text-red-400/70 italic mt-1">Physics Validation Failed</p>
            `;
        }
    } catch (e) {
        console.error(e);
        resultDiv.className = 'mt-3 p-3 rounded-xl text-sm bg-red-500/10 border border-red-500/20 text-red-500';
        resultDiv.textContent = 'Validation Error. See Console.';
    }
};

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

        // Initialize Quantum Dashboard
        const quantumDashboard = new QuantumDashboard();
        quantumDashboard.init();

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
