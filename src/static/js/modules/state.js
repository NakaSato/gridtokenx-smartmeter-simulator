// Global State
export let allReadings = [];
export let previousStats = { gen: 0, cons: 0, surplus: 0, traders: 0 };

export function setAllReadings(readings) {
    allReadings = readings;
}

export function updateReading(newReading) {
    const index = allReadings.findIndex(r => r.meter_id === newReading.meter_id);
    if (index !== -1) {
        allReadings[index] = newReading;
    } else {
        allReadings.push(newReading);
    }
}

export function setPreviousStats(stats) {
    previousStats = stats;
}
