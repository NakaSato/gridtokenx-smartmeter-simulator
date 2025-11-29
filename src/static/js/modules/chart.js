// Import Chart.js from npm
import {
    Chart,
    LineController,
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js';

// Register Chart.js components (tree-shaking friendly)
Chart.register(
    LineController,
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
    Title,
    Tooltip,
    Legend,
    Filler
);

// Chart instances
let energyChart = null;
let marketChart = null;

// Data buffers
const MAX_DATA_POINTS = 50;
const energyData = { labels: [], generation: [], consumption: [] };
const marketData = { labels: [], buyPrice: [], sellPrice: [] };

// Common Chart Options
const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: {
        mode: 'index',
        intersect: false,
    },
    plugins: {
        legend: {
            position: 'top',
            labels: {
                usePointStyle: true,
                color: '#94a3b8' // slate-400
            }
        },
        tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: '#1e293b', // slate-800
            titleColor: '#f8fafc', // slate-50
            bodyColor: '#cbd5e1', // slate-300
            borderColor: '#334155', // slate-700
            borderWidth: 1
        }
    },
    scales: {
        x: {
            display: true,
            grid: {
                color: '#334155' // slate-700
            },
            ticks: {
                color: '#94a3b8' // slate-400
            }
        },
        y: {
            display: true,
            beginAtZero: true,
            grid: {
                color: '#334155' // slate-700
            },
            ticks: {
                color: '#94a3b8' // slate-400
            }
        }
    }
};

// Initialize Energy Flow Chart
export function initEnergyChart() {
    const ctx = document.getElementById('energyFlowChart').getContext('2d');

    // Gradient for Generation
    const gradientGen = ctx.createLinearGradient(0, 0, 0, 400);
    gradientGen.addColorStop(0, 'rgba(16, 185, 129, 0.5)'); // Emerald-500
    gradientGen.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    // Gradient for Consumption
    const gradientCons = ctx.createLinearGradient(0, 0, 0, 400);
    gradientCons.addColorStop(0, 'rgba(59, 130, 246, 0.5)'); // Blue-500
    gradientCons.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

    energyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Generation (kWh)',
                    data: [],
                    borderColor: '#10B981', // Emerald-500
                    backgroundColor: gradientGen,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                },
                {
                    label: 'Consumption (kWh)',
                    data: [],
                    borderColor: '#3B82F6', // Blue-500
                    backgroundColor: gradientCons,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }
            ]
        },
        options: {
            ...commonOptions,
            plugins: {
                ...commonOptions.plugins,
                title: {
                    display: false,
                    text: 'Energy Flow'
                }
            }
        }
    });
}

// Initialize Market Price Chart
export function initMarketChart() {
    const ctx = document.getElementById('marketPriceChart').getContext('2d');

    marketChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Buy Price ($)',
                    data: [],
                    borderColor: '#F87171', // Red-400
                    backgroundColor: 'rgba(248, 113, 113, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1, // Stepped look
                    stepped: true,
                    pointRadius: 0
                },
                {
                    label: 'Sell Price ($)',
                    data: [],
                    borderColor: '#34D399', // Emerald-400
                    backgroundColor: 'rgba(52, 211, 153, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1, // Stepped look
                    stepped: true,
                    pointRadius: 0
                }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: {
                    ...commonOptions.scales.y,
                    ticks: {
                        callback: function (value) {
                            return '$' + value.toFixed(2);
                        },
                        color: '#94a3b8' // slate-400
                    }
                }
            }
        }
    });
}

// Update Charts with new data
export function updateCharts(data) {
    const now = new Date();
    const timeLabel = now.toLocaleTimeString();

    // Update Data Buffers
    energyData.labels.push(timeLabel);
    energyData.generation.push(data.total_generation || 0);
    energyData.consumption.push(data.total_consumption || 0);

    marketData.labels.push(timeLabel);
    marketData.buyPrice.push(data.market_prices?.buy || 0);
    marketData.sellPrice.push(data.market_prices?.sell || 0);

    // Maintain Buffer Size
    if (energyData.labels.length > MAX_DATA_POINTS) {
        energyData.labels.shift();
        energyData.generation.shift();
        energyData.consumption.shift();
    }

    if (marketData.labels.length > MAX_DATA_POINTS) {
        marketData.labels.shift();
        marketData.buyPrice.shift();
        marketData.sellPrice.shift();
    }

    // Update Charts
    if (energyChart) {
        energyChart.data.labels = energyData.labels;
        energyChart.data.datasets[0].data = energyData.generation;
        energyChart.data.datasets[1].data = energyData.consumption;
        energyChart.update('none'); // 'none' mode for performance
    }

    if (marketChart) {
        marketChart.data.labels = marketData.labels;
        marketChart.data.datasets[0].data = marketData.buyPrice;
        marketChart.data.datasets[1].data = marketData.sellPrice;
        marketChart.update('none');
    }
}

// Update Chart Theme (Dark/Light Mode) - Deprecated/No-op as we are dark only
export function updateChartTheme(isDark) {
    // Force dark theme colors if called
    const textColor = '#94a3b8'; // slate-400
    const gridColor = '#334155'; // slate-700

    const updateTheme = (chart) => {
        if (!chart) return;

        // Update Scales
        if (chart.options.scales.x) {
            chart.options.scales.x.ticks.color = textColor;
            chart.options.scales.x.grid.color = gridColor;
        }
        if (chart.options.scales.y) {
            chart.options.scales.y.ticks.color = textColor;
            chart.options.scales.y.grid.color = gridColor;
        }

        // Update Legend
        if (chart.options.plugins.legend) {
            chart.options.plugins.legend.labels.color = textColor;
        }

        chart.update();
    };

    updateTheme(energyChart);
    updateTheme(marketChart);
}
