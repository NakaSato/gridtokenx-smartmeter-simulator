import { updateChartTheme } from '../chart.js';

// Dark Mode - Force Dark
export function toggleDarkMode() {
    document.documentElement.classList.add('dark');
    updateChartTheme(true);
}

export function initDarkMode() {
    document.documentElement.classList.add('dark');
    updateChartTheme(true);
}
