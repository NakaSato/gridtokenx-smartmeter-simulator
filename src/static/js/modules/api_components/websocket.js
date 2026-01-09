import { addConsoleMessage, addConsoleReading } from '../console.js';
import { updateReadings } from './readings.js';

let ws = null;
let reconnectInterval = null;
const API_BASE = window.location.origin;

export function connectWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws`;

    console.log('Connecting to WebSocket:', wsUrl);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('Connected to WebSocket');
        updateConnectionStatus(true);
        addConsoleMessage('WebSocket connected successfully', 'status');
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            let readings = [];

            if (data.type === 'meter_reading') {
                readings = [data.reading];
            } else if (data.type === 'meter_readings') {
                readings = data.readings || [];
            } else if (Array.isArray(data)) {
                readings = data;
            } else {
                readings = [data];
            }

            updateReadings(readings);

            readings.forEach(reading => {
                addConsoleReading(reading);
            });
        } catch (e) {
            console.error('Error parsing WebSocket message:', e);
            addConsoleMessage(`Error parsing message: ${e.message}`, 'error');
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
        addConsoleMessage('WebSocket connection error', 'error');
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);
        addConsoleMessage('WebSocket connection lost', 'warning');

        if (!reconnectInterval) {
            reconnectInterval = setInterval(() => {
                console.log('Attempting to reconnect...');
                addConsoleMessage('Attempting to reconnect...', 'warning');
                connectWebSocket();
            }, 5000);
        }
    };
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    if (connected) {
        statusEl.innerHTML = '<span class="inline-block w-3 h-3 rounded-full bg-emerald-500 mr-2"></span><span class="font-semibold text-emerald-400">Connected</span>';
    } else {
        statusEl.innerHTML = '<span class="inline-block w-3 h-3 rounded-full bg-red-500 mr-2"></span><span class="font-semibold text-red-400">Disconnected</span>';
    }
}
