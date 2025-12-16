// Global State
export let allReadings = [];
export let previousStats = { gen: 0, cons: 0, surplus: 0, traders: 0 };

// Track last update time for each meter to determine "live" status
const meterLastUpdated = new Map();

export function setAllReadings(readings) {
    allReadings = readings;
}

export function updateReading(newReading) {
    const index = allReadings.findIndex(r => r.meter_id === newReading.meter_id);

    // Track when this meter was last updated
    meterLastUpdated.set(newReading.meter_id, Date.now());

    if (index !== -1) {
        allReadings[index] = newReading;
    } else {
        allReadings.push(newReading);
    }
}

export function removeReading(meterId) {
    const index = allReadings.findIndex(r => r.meter_id === meterId);
    if (index !== -1) {
        allReadings.splice(index, 1);
    }
    meterLastUpdated.delete(meterId);
}

export function setPreviousStats(stats) {
    previousStats = stats;
}

// Check if a meter is "live" (received data within last 30 seconds)
export function isMeterLive(meterId) {
    const lastUpdate = meterLastUpdated.get(meterId);
    if (!lastUpdate) return false;
    return (Date.now() - lastUpdate) < 30000; // 30 seconds
}
