// Console Logic

let consoleLineCount = 0;
let consoleAutoScroll = true;

export function addConsoleMessage(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const consoleEl = document.getElementById('console-output');

    let colorClass = '';
    switch (type) {
        case 'error': colorClass = 'console-error'; break;
        case 'warning': colorClass = 'console-warning'; break;
        case 'status': colorClass = 'console-status'; break;
        default: colorClass = 'text-green-400'; break;
    }

    const messageEl = document.createElement('div');
    messageEl.className = colorClass;
    messageEl.innerHTML = `<span class="console-timestamp">[${timestamp}]</span> ${message}`;

    consoleEl.appendChild(messageEl);
    consoleLineCount++;
    updateConsoleLineCount();

    if (consoleAutoScroll) {
        consoleEl.scrollTop = consoleEl.scrollHeight;
    }

    // Limit console lines
    if (consoleLineCount > 1000) {
        const firstChild = consoleEl.firstChild;
        if (firstChild) {
            consoleEl.removeChild(firstChild);
            consoleLineCount--;
        }
    }
}

export function addConsoleReading(reading) {
    const timestamp = new Date().toLocaleTimeString();
    const consoleEl = document.getElementById('console-output');

    const readingEl = document.createElement('div');

    // Format based on reading type
    let message = `<span class="console-timestamp">[${timestamp}]</span> `;
    message += `<span class="console-meter-id">${reading.meter_id || 'UNKNOWN'}</span> `;
    message += `| <span class="text-gray-400">${reading.meter_type || 'Unknown'}</span> `;

    if (reading.energy_generated && parseFloat(reading.energy_generated) > 0) {
        message += `| <span class="console-energy">Generated: ${parseFloat(reading.energy_generated).toFixed(2)} kWh</span> `;
    }

    if (reading.energy_consumed && parseFloat(reading.energy_consumed) > 0) {
        message += `| <span class="console-energy">Consumed: ${parseFloat(reading.energy_consumed).toFixed(2)} kWh</span> `;
    }

    if (reading.surplus_energy && parseFloat(reading.surplus_energy) > 0) {
        message += `| <span class="console-status">SELL: ${parseFloat(reading.surplus_energy).toFixed(2)} kWh</span> `;
        if (reading.max_sell_price) {
            message += `@ <span class="console-price">$${parseFloat(reading.max_sell_price).toFixed(2)}</span>`;
        }
    }

    if (reading.deficit_energy && parseFloat(reading.deficit_energy) > 0) {
        message += `| <span class="console-warning">BUY: ${parseFloat(reading.deficit_energy).toFixed(2)} kWh</span> `;
        if (reading.max_buy_price) {
            message += `@ <span class="console-price">$${parseFloat(reading.max_buy_price).toFixed(2)}</span>`;
        }
    }

    if (reading.battery_level !== undefined) {
        message += `| Battery: ${parseFloat(reading.battery_level).toFixed(1)}%`;
    }

    if (reading.location) {
        message += ` | Location: ${reading.location}`;
    }

    readingEl.innerHTML = message;
    consoleEl.appendChild(readingEl);
    consoleLineCount++;
    updateConsoleLineCount();

    if (consoleAutoScroll) {
        consoleEl.scrollTop = consoleEl.scrollHeight;
    }

    // Limit console lines
    if (consoleLineCount > 1000) {
        const firstChild = consoleEl.firstChild;
        if (firstChild) {
            consoleEl.removeChild(firstChild);
            consoleLineCount--;
        }
    }
}

export function clearConsole() {
    const consoleEl = document.getElementById('console-output');
    consoleEl.innerHTML = '<div class="text-gray-500">Console cleared</div>';
    consoleLineCount = 1;
    updateConsoleLineCount();
    addConsoleMessage('Console cleared by user', 'status');
}

export function toggleConsoleScroll() {
    consoleAutoScroll = !consoleAutoScroll;
    const btn = document.getElementById('console-scroll-btn');
    btn.textContent = `Auto-scroll: ${consoleAutoScroll ? 'ON' : 'OFF'}`;
    btn.className = consoleAutoScroll ?
        'text-xs text-green-400 hover:text-green-300 uppercase tracking-wider' :
        'text-xs text-gray-400 hover:text-gray-300 uppercase tracking-wider';

    addConsoleMessage(`Auto-scroll ${consoleAutoScroll ? 'enabled' : 'disabled'}`, 'status');
}

export function updateConsoleLineCount() {
    // Optional: if we had a counter element
    // document.getElementById('console-line-count').textContent = consoleLineCount;
}
