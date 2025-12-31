
import { Chart } from 'chart.js/auto';

// Configuration
const REFRESH_INTERVAL_MS = 5000;

export class QuantumDashboard {
    constructor() {
        this.ctxDepth = document.getElementById('quantumDepthChart');
        this.ctxNetwork = document.getElementById('quantumNetworkChart');

        this.depthChart = null;
        this.networkChart = null;
        this.voltageChart = null;
        this.intervalId = null;
    }

    init() {
        console.log("Initializing Quantum Dashboard...");
        if (!this.ctxDepth) {
            console.warn("Quantum chart elements not found. Skipping init.");
            return;
        }

        this.initCharts();
        this.startPolling();
    }

    initCharts() {
        // 1. Market Depth Chart (Bids vs Asks) - Scatter or Bar
        this.depthChart = new Chart(this.ctxDepth, {
            type: 'scatter',
            data: {
                datasets: [
                    {
                        label: 'Bids (Buyers)',
                        data: [],
                        backgroundColor: '#ef4444', // Red for demand/buy (or green? usually buy is green in trading, sell is red. Let's stick to Buy=Green, Sell=Red)
                        pointRadius: 6,
                        pointHoverRadius: 8
                    },
                    {
                        label: 'Asks (Sellers)',
                        data: [],
                        backgroundColor: '#10b981', // Green for supply/sell (?) No, Market Depth: Bids (Buy) Green, Asks (Sell) Red.
                        pointRadius: 6,
                        pointHoverRadius: 8
                    },
                    {
                        label: 'Matched',
                        data: [],
                        backgroundColor: '#3b82f6', // Blue for matches
                        pointRadius: 8,
                        pointStyle: 'star'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: { display: true, text: 'Price (THB/kWh)', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        title: { display: true, text: 'Energy (kWh)', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#e2e8f0' } },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const p = context.raw;
                                return `${context.dataset.label}: ${p.amount} kWh @ ${p.x} THB (ID: ${p.id})`;
                            }
                        }
                    }
                }
            }
        });

        // 2. Network/Welfare Chart (Time Series of Welfare)
        // Or maybe just a bar chart of recent match scores
        if (this.ctxNetwork) {
            this.networkChart = new Chart(this.ctxNetwork, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Optimization Score (Welfare)',
                        data: [],
                        borderColor: '#8b5cf6', // Violet
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { display: false }, // Time step
                        y: {
                            grid: { color: '#334155' },
                            ticks: { color: '#94a3b8' }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        // 3. Voltage Profile Chart (Bar)
        const ctxVoltage = document.getElementById('quantumVoltageChart');
        if (ctxVoltage) {
            this.voltageChart = new Chart(ctxVoltage, {
                type: 'bar',
                data: {
                    labels: [], // Zone IDs
                    datasets: [{
                        label: 'Voltage (p.u.)',
                        data: [],
                        backgroundColor: [], // Dynamic colors
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false,
                            min: 0.90,
                            max: 1.10,
                            grid: { color: '#334155' },
                            ticks: { color: '#94a3b8' },
                            title: { display: true, text: 'Per Unit (p.u.)', color: '#64748b' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#94a3b8' }
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        annotation: {
                            annotations: {
                                line1: {
                                    type: 'line',
                                    yMin: 0.96,
                                    yMax: 0.96,
                                    borderColor: 'rgba(239, 68, 68, 0.5)', // Red
                                    borderWidth: 1,
                                    borderDash: [5, 5],
                                    label: { content: 'Min Safe', enabled: true, color: 'red', position: 'start' }
                                },
                                line2: {
                                    type: 'line',
                                    yMin: 1.04,
                                    yMax: 1.04,
                                    borderColor: 'rgba(239, 68, 68, 0.5)', // Red
                                    borderWidth: 1,
                                    borderDash: [5, 5],
                                    label: { content: 'Max Safe', enabled: true, color: 'red', position: 'start' }
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    startPolling() {
        this.fetchData();
        this.intervalId = setInterval(() => this.fetchData(), REFRESH_INTERVAL_MS);
    }

    async fetchData() {
        try {
            const response = await fetch('/api/v1/p2p/matching/quantum');
            if (!response.ok) return;
            const data = await response.json();

            this.updateCharts(data);
            this.updateStats(data);

            // Also fetch transactions
            this.fetchTransactions();
        } catch (e) {
            console.error("Failed to fetch quantum data:", e);
        }
    }

    async fetchTransactions() {
        try {
            const response = await fetch('/api/v1/p2p/transactions?limit=10');
            if (!response.ok) return;
            const transactions = await response.json();
            this.updateTable(transactions);
        } catch (e) {
            console.error("Failed to fetch transactions:", e);
        }
    }

    updateTable(transactions) {
        const tbody = document.getElementById('transaction-table-body');
        if (!tbody) return;

        if (transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-slate-500 italic">No transactions recorded yet.</td></tr>';
            return;
        }

        tbody.innerHTML = transactions.map(tx => `
            <tr class="hover:bg-slate-700/20 transition-colors">
                <td class="px-6 py-4 text-slate-300">${new Date(tx.timestamp).toLocaleString()}</td>
                <td class="px-6 py-4 font-mono text-xs text-blue-300">${tx.buyer_id}</td>
                <td class="px-6 py-4 font-mono text-xs text-orange-300">${tx.seller_id}</td>
                <td class="px-6 py-4 text-right font-mono text-white">${tx.amount_kwh.toFixed(2)}</td>
                <td class="px-6 py-4 text-right font-mono text-emerald-400">${tx.price_per_kwh.toFixed(2)}</td>
                <td class="px-6 py-4 text-right font-mono text-emerald-300 font-bold">${tx.total_cost.toFixed(2)}</td>
                <td class="px-6 py-4 text-center">
                    <span class="px-2 py-0.5 rounded text-xs font-medium border ${tx.transaction_type === 'QUANTUM'
                ? 'bg-violet-500/10 text-violet-400 border-violet-500/30'
                : 'bg-slate-700 text-slate-300 border-slate-600'
            }">${tx.transaction_type}</span>
                </td>
                <td class="px-6 py-4 font-mono text-xs text-slate-500" title="${tx.tx_hash || ''}">
                    ${tx.tx_hash ? tx.tx_hash.substring(0, 8) + '...' : '-'}
                </td>
            </tr>
        `).join('');
    }

    updateCharts(data) {
        if (!data.matches || !this.depthChart) return;

        // Process matches to find bids/asks that were part of it
        // Note: The API currently only returns "matches". It doesn't return the full order book (unmatched bids/asks).
        // For visualization, we will just plot the matched points for now, 
        // effectively showing the "cleared" trades.

        // Matches are: { buyer_id, seller_id, amount_kwh, price_per_kwh, ... }

        const matchesPoints = data.matches.map(m => ({
            x: m.price_per_kwh,
            y: m.amount_kwh,
            amount: m.amount_kwh,
            id: `${m.buyer_id}-${m.seller_id}`
        }));

        // Bids (Buy side) - We simulate the buy/sell points from the match
        // Buyer bought at Price X.
        const buyPoints = data.matches.map(m => ({
            x: m.price_per_kwh, // In a real match, buyer bid >= price. Here we just show the deal price.
            y: m.amount_kwh,
            amount: m.amount_kwh,
            id: m.buyer_id
        }));

        const sellPoints = data.matches.map(m => ({
            x: m.price_per_kwh,
            y: m.amount_kwh,
            amount: m.amount_kwh,
            id: m.seller_id
        }));

        // For scatter plot:
        // Dataset 0: Bids (Buy) -> Green match color #10b981
        // Dataset 1: Asks (Sell) -> Red match color #ef4444
        // Dataset 2: Match -> Blue

        // Since we only know the match result, let's just show the Matches in Blue 
        // and maybe offsets for Bids/Asks to visualize the "Meeting point"

        this.depthChart.data.datasets[0].data = buyPoints; // Bids
        this.depthChart.data.datasets[1].data = sellPoints; // Asks
        this.depthChart.data.datasets[2].data = matchesPoints; // Matches

        this.depthChart.data.datasets[0].backgroundColor = '#10b981'; // Buy
        this.depthChart.data.datasets[1].backgroundColor = '#ef4444'; // Sell

        this.depthChart.update();

        // Update Welfare Chart (Append new point)
        if (this.networkChart && data.meta && data.meta.score !== undefined) {
            const score = data.meta.score || 0;
            const timestamp = new Date().toLocaleTimeString();

            this.networkChart.data.labels.push(timestamp);
            this.networkChart.data.datasets[0].data.push(score);

            // Keep last 20 points
            if (this.networkChart.data.labels.length > 20) {
                this.networkChart.data.labels.shift();
                this.networkChart.data.datasets[0].data.shift();
            }
            this.networkChart.update();
        }
        this.networkChart.update();


        // Update Voltage Chart
        if (this.voltageChart && data.meta && data.meta.zone_voltages) {
            const voltageMap = data.meta.zone_voltages;
            const zones = Object.keys(voltageMap).sort((a, b) => parseInt(a) - parseInt(b));
            const voltages = zones.map(z => voltageMap[z]);

            // Color Logic: Green if 0.96-1.04, else Red/Orange
            const colors = voltages.map(v => {
                if (v >= 0.96 && v <= 1.04) return '#10b981'; // Emerald 500
                return '#f59e0b'; // Amber 500 (Warning)
            });

            this.voltageChart.data.labels = zones.map(z => `Zone ${z}`);
            this.voltageChart.data.datasets[0].data = voltages;
            this.voltageChart.data.datasets[0].backgroundColor = colors;
            this.voltageChart.update();

            const statusEl = document.getElementById('voltage-status');
            if (statusEl) {
                const unhealthy = voltages.filter(v => v < 0.96 || v > 1.04).length;
                if (unhealthy > 0) {
                    statusEl.innerText = `${unhealthy} Zone(s) Unstable`;
                    statusEl.className = "absolute top-2 right-2 text-xs bg-red-900/80 px-2 py-1 rounded text-red-200 border border-red-700 font-bold animate-pulse";
                } else {
                    statusEl.innerText = "Grid Healthy";
                    statusEl.className = "absolute top-2 right-2 text-xs bg-emerald-900/80 px-2 py-1 rounded text-emerald-200 border border-emerald-700";
                }
            }
        }
    }

    updateStats(data) {
        // Update DOM elements if they exist
        const durationEl = document.getElementById('quantum-duration');
        const countEl = document.getElementById('quantum-match-count');
        const welfareEl = document.getElementById('quantum-welfare');
        const methodEl = document.getElementById('quantum-method');

        if (data.meta) {
            if (durationEl) durationEl.innerText = (data.meta.duration || 0).toFixed(3) + 's';
            if (methodEl) methodEl.innerText = data.meta.method || 'Unknown';
            // If matches is array
            if (countEl) countEl.innerText = data.matches.length;

            // Score is essentially welfare (negative cost or positive surplus)
            // In API it might be returned as 'score'
            if (welfareEl) welfareEl.innerText = (data.meta.score || 0).toFixed(2);
        }
    }
}
