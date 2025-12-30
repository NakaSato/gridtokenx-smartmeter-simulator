/**
 * Smart Meter Map - JavaScript Controller
 * Handles map initialization, meter markers, zone visualization, and real-time updates
 */

// Global state
let map = null;
let markers = {};
let metersData = [];
let refreshInterval = null;
let isInitialLoad = true;

// Zone visualization state
// Zone visualization state
let zonePolygons = [];
let transformerMarkers = [];
let feederLines = [];
let zonesData = {};
let showZones = true;
let showFeeders = true;

// Default center (Thailand)
const DEFAULT_CENTER = [13.7563, 100.5018];
const DEFAULT_ZOOM = 10;

// Zone colors
const ZONE_COLORS = [
    { fill: 'rgba(239, 68, 68, 0.2)', stroke: '#ef4444', bg: '#ef4444' },   // Red
    { fill: 'rgba(34, 197, 94, 0.2)', stroke: '#22c55e', bg: '#22c55e' },   // Green
    { fill: 'rgba(59, 130, 246, 0.2)', stroke: '#3b82f6', bg: '#3b82f6' },  // Blue
    { fill: 'rgba(168, 85, 247, 0.2)', stroke: '#a855f7', bg: '#a855f7' },  // Purple
    { fill: 'rgba(245, 158, 11, 0.2)', stroke: '#f59e0b', bg: '#f59e0b' },  // Amber
];

// Meter type configurations
const METER_TYPES = {
    Solar_Prosumer: { class: 'solar', icon: '☀️', color: '#f59e0b' },
    Grid_Consumer: { class: 'consumer', icon: '⚡', color: '#3b82f6' },
    Hybrid_Prosumer: { class: 'hybrid', icon: '🔋', color: '#8b5cf6' },
    Battery_Storage: { class: 'battery', icon: '🔌', color: '#10b981' }
};

/**
 * Initialize the Leaflet map
 */
function initMap() {
    map = L.map('map', {
        center: DEFAULT_CENTER,
        zoom: DEFAULT_ZOOM,
        zoomControl: true,
        attributionControl: true
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    map.zoomControl.setPosition('topright');
}

/**
 * Create a custom marker for a meter
 */
function createMeterMarker(meter) {
    const meterType = meter.name || 'Grid_Consumer';
    const typeConfig = METER_TYPES[meterType] || METER_TYPES.Grid_Consumer;

    // Get zone color if available
    const zoneColor = meter.zone_id !== undefined && meter.zone_id !== null
        ? ZONE_COLORS[meter.zone_id % ZONE_COLORS.length].bg
        : typeConfig.color;

    const icon = L.divIcon({
        className: 'custom-marker',
        html: `<div class="meter-marker ${typeConfig.class}" style="border-color: ${zoneColor};">${typeConfig.icon}</div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        popupAnchor: [0, -16]
    });

    let lat = meter.latitude || DEFAULT_CENTER[0] + (Math.random() - 0.5) * 0.1;
    let lng = meter.longitude || DEFAULT_CENTER[1] + (Math.random() - 0.5) * 0.1;

    const marker = L.marker([lat, lng], { icon });
    const popupContent = createPopupContent(meter);
    marker.bindPopup(popupContent, { maxWidth: 300, minWidth: 250 });

    return marker;
}

/**
 * Create popup HTML content for a meter
 */
function createPopupContent(meter) {
    const meterType = meter.name || 'Unknown';
    const typeConfig = METER_TYPES[meterType] || METER_TYPES.Grid_Consumer;
    const generation = (meter.current_generation || 0).toFixed(4);
    const consumption = (meter.current_consumption || 0).toFixed(4);
    const net = (parseFloat(generation) - parseFloat(consumption)).toFixed(4);
    const netClass = parseFloat(net) >= 0 ? 'text-emerald-400' : 'text-red-400';
    const netSign = parseFloat(net) >= 0 ? '+' : '';

    // Zone info
    const zoneInfo = meter.zone_id !== undefined && meter.zone_id !== null
        ? `<div class="flex justify-between"><span class="text-slate-400">Zone</span><span class="text-violet-400">Zone ${meter.zone_id}</span></div>`
        : '';

    // Wallet info (Simulated)
    const walletAddr = meter.wallet_address ? `${meter.wallet_address.substring(0, 4)}...${meter.wallet_address.substring(meter.wallet_address.length - 4)}` : 'N/A';
    const balGtx = meter.balance_gtx !== undefined ? meter.balance_gtx.toFixed(2) : '0.00';
    const balNrg = meter.balance_nrg !== undefined ? meter.balance_nrg.toFixed(2) : '0.00';

    return `
    <div class="p-2">
      <div class="flex items-center gap-2 mb-3 pb-2 border-b border-slate-600">
        <div class="w-8 h-8 rounded-lg flex items-center justify-center text-lg" 
             style="background: ${typeConfig.color}20; border: 1px solid ${typeConfig.color}50;">
          ${typeConfig.icon}
        </div>
        <div>
          <h3 class="font-semibold text-white text-sm">${meter.meter_id}</h3>
          <p class="text-xs text-slate-400">${meterType.replace(/_/g, ' ')}</p>
        </div>
      </div>
      <div class="space-y-2 text-xs">
        <div class="flex justify-between"><span class="text-slate-400">Location</span><span class="text-slate-200">${meter.location || 'Unknown'}</span></div>
        ${zoneInfo}
        <div class="flex justify-between"><span class="text-slate-400">Generation</span><span class="text-emerald-400">${generation} kWh</span></div>
        <div class="flex justify-between"><span class="text-slate-400">Consumption</span><span class="text-blue-400">${consumption} kWh</span></div>
        <div class="flex justify-between pt-2 border-t border-slate-600"><span class="text-slate-400 font-medium">Net Energy</span><span class="${netClass} font-medium">${netSign}${net} kWh</span></div>
        
        <!-- Wallet / Token Section -->
        <div class="mt-2 pt-2 border-t border-slate-600 bg-slate-800/50 -mx-2 px-2 pb-2 mb-[-8px]">
             <div class="flex justify-between items-center mb-1">
                <span class="text-[10px] text-slate-400 uppercase tracking-wider">Wallet</span>
                <span class="text-[10px] font-mono text-slate-300" title="${meter.wallet_address || ''}">${walletAddr}</span>
             </div>
             <div class="grid grid-cols-2 gap-2 text-[10px]">
                <div class="bg-indigo-900/30 p-1.5 rounded border border-indigo-500/30 text-center">
                    <span class="block text-indigo-300 font-bold">${balGtx}</span>
                    <span class="block text-indigo-400/70 text-[9px]">GTX (Pay)</span>
                </div>
                <div class="bg-amber-900/30 p-1.5 rounded border border-amber-500/30 text-center">
                    <span class="block text-amber-300 font-bold">${balNrg}</span>
                    <span class="block text-amber-400/70 text-[9px]">NRG (REC)</span>
                </div>
             </div>
        </div>
      </div>
      <div class="mt-3 pt-2 border-t border-slate-600 flex items-center gap-2">
        <span class="relative flex h-2 w-2">
          <span class="absolute inline-flex h-full w-full rounded-full ${meter.is_connected ? 'bg-emerald-400' : 'bg-slate-500'} opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 ${meter.is_connected ? 'bg-emerald-400' : 'bg-slate-500'}"></span>
        </span>
        <span class="text-xs ${meter.is_connected ? 'text-emerald-400' : 'text-slate-500'}">${meter.is_connected ? 'Connected' : 'Disconnected'}</span>
      </div>
    </div>`;
}

/**
 * Convex hull algorithm for zone polygons
 */
function convexHull(points) {
    if (points.length < 3) return points;
    let leftmost = 0;
    for (let i = 1; i < points.length; i++) {
        if (points[i][1] < points[leftmost][1]) leftmost = i;
    }
    const hull = [];
    let p = leftmost, q;
    do {
        hull.push(points[p]);
        q = (p + 1) % points.length;
        for (let i = 0; i < points.length; i++) {
            const val = (points[i][1] - points[p][1]) * (points[q][0] - points[i][0]) -
                (points[i][0] - points[p][0]) * (points[q][1] - points[i][1]);
            if (val < 0) q = i;
        }
        p = q;
    } while (p !== leftmost && hull.length < points.length + 1);
    return hull;
}

/**
 * Render zone polygons and transformer markers
 */
function renderZones(zones, meters) {
    // Clear existing zones
    zonePolygons.forEach(p => map.removeLayer(p));
    transformerMarkers.forEach(m => map.removeLayer(m));
    zonePolygons = [];
    transformerMarkers = [];

    if (!showZones || !zones || Object.keys(zones).length === 0) return;

    // Group meters by zone
    const metersByZone = {};
    meters.forEach(m => {
        if (m.zone_id !== undefined && m.zone_id !== null && m.latitude && m.longitude) {
            if (!metersByZone[m.zone_id]) metersByZone[m.zone_id] = [];
            metersByZone[m.zone_id].push(m);
        }
    });

    // Render each zone
    Object.entries(zones).forEach(([zoneId, info]) => {
        const zid = parseInt(zoneId);
        const color = ZONE_COLORS[zid % ZONE_COLORS.length];
        const zoneMeters = metersByZone[zid] || [];

        // Draw convex hull polygon
        if (zoneMeters.length >= 3) {
            const points = zoneMeters.map(m => [m.latitude, m.longitude]);
            const hull = convexHull(points);
            const polygon = L.polygon(hull, {
                fillColor: color.fill,
                fillOpacity: 0.25,
                color: color.stroke,
                weight: 2,
                dashArray: '5, 5',
            }).addTo(map);
            polygon.bindPopup(`<strong>Zone ${zid}</strong><br><span style="color:#94a3b8;">Transformer: ${info.transformer_name}</span><br><span style="color:#94a3b8;">Meters: ${info.meter_count}</span>`);
            zonePolygons.push(polygon);
        }

        // Add transformer marker at centroid
        if (info.centroid_lat && info.centroid_lon) {
            const txIcon = L.divIcon({
                className: 'transformer-marker',
                html: `<div style="width:36px;height:36px;border-radius:6px;background:${color.bg};display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:10px;border:2px solid rgba(255,255,255,0.5);box-shadow:0 2px 8px rgba(0,0,0,0.4);">TX</div>`,
                iconSize: [36, 36],
                iconAnchor: [18, 18],
            });
            const txMarker = L.marker([info.centroid_lat, info.centroid_lon], { icon: txIcon }).addTo(map);
            txMarker.bindPopup(`<strong>${info.transformer_name}</strong><br><span style="color:#94a3b8;">Zone ${zid} Centroid</span><br><span style="color:#64748b;font-size:11px;">${info.centroid_lat.toFixed(4)}°N, ${info.centroid_lon.toFixed(4)}°E</span>`);
            transformerMarkers.push(txMarker);
        }
    });

    // Update zone legend
    updateZoneLegend(zones);

    // Render topology lines
    renderFeeders(zones, meters);
}

/**
 * Render feeder lines (Topology Visualization)
 */
function renderFeeders(zones, meters) {
    // Clear existing lines
    feederLines.forEach(l => map.removeLayer(l));
    feederLines = [];

    if (!showFeeders || !zones || Object.keys(zones).length === 0) return;

    // 1. Calculate Main Substation Location (Centroid of Zones)
    let sumLat = 0, sumLon = 0, count = 0;
    Object.values(zones).forEach(info => {
        if (info.centroid_lat && info.centroid_lon) {
            sumLat += info.centroid_lat;
            sumLon += info.centroid_lon;
            count++;
        }
    });

    if (count === 0) return;
    const mainSubstation = [sumLat / count, sumLon / count];

    // Add Main Substation Marker
    const mainIcon = L.divIcon({
        className: 'main-substation-marker',
        html: `<div style="width:40px;height:40px;border-radius:4px;background:#0f172a;display:flex;align-items:center;justify-content:center;font-weight:800;color:#facc15;font-size:12px;border:3px solid #facc15;box-shadow:0 0 20px rgba(250, 204, 21, 0.4);">SUB</div>`,
        iconSize: [40, 40],
        iconAnchor: [20, 20],
    });
    const subMarker = L.marker(mainSubstation, { icon: mainIcon }).addTo(map);
    subMarker.bindPopup(`<strong>Main Substation</strong><br><span style="color:#94a3b8;">22kV Grid Connection</span>`);
    feederLines.push(subMarker); // Store marker in same array for cleanup

    // Group meters
    const metersByZone = {};
    meters.forEach(m => {
        if (m.zone_id !== undefined && m.zone_id !== null) {
            if (!metersByZone[m.zone_id]) metersByZone[m.zone_id] = [];
            metersByZone[m.zone_id].push(m);
        }
    });

    Object.entries(zones).forEach(([zoneId, info]) => {
        const zid = parseInt(zoneId);
        const color = ZONE_COLORS[zid % ZONE_COLORS.length];
        const zoneCenter = [info.centroid_lat, info.centroid_lon];

        // 2. Draw MV Feeder (Main -> Zone Transformer)
        const mvLine = L.polyline([mainSubstation, zoneCenter], {
            color: '#facc15', // Yellow for MV
            weight: 3,
            opacity: 0.8,
            dashArray: '10, 10'
        }).addTo(map);
        mvLine.bindPopup(`<strong>22kV Feeder</strong><br>Main -> Zone ${zid}`);
        feederLines.push(mvLine);

        // 3. Draw LV Lines (Zone Transformer -> Meters)
        const zoneMeters = metersByZone[zid] || [];
        zoneMeters.forEach(m => {
            if (m.latitude && m.longitude) {
                const lvLine = L.polyline([zoneCenter, [m.latitude, m.longitude]], {
                    color: color.stroke,
                    weight: 1,
                    opacity: 0.4
                }).addTo(map);
                feederLines.push(lvLine);
            }
        });
    });
}

/**
 * Update zone legend in the UI
 */
function updateZoneLegend(zones) {
    const legend = document.getElementById('zone-legend');
    if (!legend) return;
    legend.innerHTML = '';

    // Handle empty zones case
    if (!zones || Object.keys(zones).length === 0) {
        legend.innerHTML = '<div class="text-xs text-slate-500 italic p-2 text-center">No Active Zones</div>';
        return;
    }

    // Calculate zone stats from global metersData
    const zoneStats = {};
    if (typeof metersData !== 'undefined' && Array.isArray(metersData)) {
        metersData.forEach(m => {
            if (m.zone_id !== undefined && m.zone_id !== null) {
                if (!zoneStats[m.zone_id]) zoneStats[m.zone_id] = { gen: 0, cons: 0 };
                zoneStats[m.zone_id].gen += (m.current_generation || 0);
                zoneStats[m.zone_id].cons += (m.current_consumption || 0);
            }
        });
    }

    Object.entries(zones).forEach(([zoneId, info]) => {
        const zid = parseInt(zoneId);
        // Safety check for color index
        const colorIndex = isNaN(zid) ? 0 : Math.abs(zid) % ZONE_COLORS.length;
        const color = ZONE_COLORS[colorIndex] || ZONE_COLORS[0];

        const stats = zoneStats[zid] || { gen: 0, cons: 0 };
        const net = stats.gen - stats.cons;

        const item = document.createElement('div');
        item.className = 'mb-2 pb-2 border-b border-slate-700/30 last:border-0 last:mb-0 last:pb-0';
        item.innerHTML = `
            <div class="flex items-start gap-2">
                <div class="legend-dot mt-1" style="background:${color.bg}; flex-shrink: 0;"></div>
                <div class="flex-1 w-full">
                    <div class="flex justify-between items-start mb-1">
                        <span class="text-xs font-semibold text-slate-200">Zone ${zid}</span>
                        <span class="text-[10px] text-slate-400 bg-slate-800/50 px-1.5 py-0.5 rounded border border-slate-700/50">${info.transformer_name || 'TX-Unknown'}</span>
                    </div>
                    <div class="grid grid-cols-2 gap-x-2 gap-y-0.5 text-[10px] leading-tight">
                        <div class="flex justify-between text-slate-400"><span>Meters:</span> <span class="text-slate-200 font-medium">${info.meter_count}</span></div>
                        <div class="flex justify-between text-slate-400"><span>Net:</span> <span class="${net >= 0 ? 'text-emerald-400' : 'text-red-400'} font-medium">${net > 0 ? '+' : ''}${net.toFixed(1)}</span></div>
                        <div class="flex justify-between text-slate-400"><span>Gen:</span> <span class="text-emerald-500/90">${stats.gen.toFixed(1)}k</span></div>
                        <div class="flex justify-between text-slate-400"><span>Load:</span> <span class="text-blue-500/90">${stats.cons.toFixed(1)}k</span></div>
                    </div>
                </div>
            </div>`;
        legend.appendChild(item);
    });
}

function updateConnectionStatus(connected, meterCount) {
    const statusEl = document.getElementById('connection-status');
    const countEl = document.getElementById('meter-count');
    if (connected) {
        statusEl.innerHTML = `<span class="relative flex h-2.5 w-2.5"><span class="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span><span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span></span><span class="text-emerald-400 font-medium text-sm">Connected</span>`;
    } else {
        statusEl.innerHTML = `<span class="relative flex h-2.5 w-2.5"><span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span></span><span class="text-red-400 font-medium text-sm">Disconnected</span>`;
    }
    countEl.textContent = `${meterCount} meters`;
}

function updateStats(meters) {
    let totalGeneration = 0, totalConsumption = 0;
    meters.forEach(meter => {
        totalGeneration += meter.current_generation || 0;
        totalConsumption += meter.current_consumption || 0;
    });
    document.getElementById('stat-generation').textContent = totalGeneration.toFixed(2) + ' kWh';
    document.getElementById('stat-consumption').textContent = totalConsumption.toFixed(2) + ' kWh';
    document.getElementById('stat-surplus').textContent = (totalGeneration - totalConsumption).toFixed(2) + ' kWh';
}

async function fetchMeterData() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) throw new Error('Failed to fetch meter data');
        return await response.json();
    } catch (error) {
        console.error('Error fetching meter data:', error);
        return null;
    }
}

async function fetchZoneData() {
    try {
        const response = await fetch('/api/zones');
        if (!response.ok) throw new Error('Failed to fetch zone data');
        return await response.json();
    } catch (error) {
        console.error('Error fetching zone data:', error);
        return null;
    }
}

function updateMarkers(meters) {
    Object.values(markers).forEach(marker => map.removeLayer(marker));
    markers = {};
    const bounds = [];
    meters.forEach(meter => {
        const marker = createMeterMarker(meter);
        marker.addTo(map);
        markers[meter.meter_id] = marker;
        const lat = meter.latitude || DEFAULT_CENTER[0];
        const lng = meter.longitude || DEFAULT_CENTER[1];
        bounds.push([lat, lng]);
    });
    if (bounds.length > 0 && isInitialLoad) {
        map.fitBounds(L.latLngBounds(bounds), { padding: [50, 50], maxZoom: 15 });
        isInitialLoad = false;
    }
}

async function refreshData() {
    const refreshBtn = document.getElementById('refresh-btn');
    const refreshIcon = refreshBtn?.querySelector('i');
    if (refreshBtn) refreshBtn.disabled = true;
    if (refreshIcon) refreshIcon.classList.add('animate-spin');

    try {
        // Fetch both meter and zone data
        const [statusData, zoneData] = await Promise.all([fetchMeterData(), fetchZoneData()]);

        if (statusData && statusData.meters) {
            // Merge zone_id from zone data into meters
            if (zoneData && zoneData.meters) {
                const zoneMap = {};
                zoneData.meters.forEach(m => { zoneMap[m.meter_id] = m.zone_id; });
                statusData.meters.forEach(m => { m.zone_id = zoneMap[m.meter_id]; });
            }
            metersData = statusData.meters;
            updateMarkers(metersData);
            updateStats(metersData);
            updateConnectionStatus(statusData.status === 'running', metersData.length);
        } else {
            updateConnectionStatus(false, 0);
        }

        if (zoneData && zoneData.zones) {
            zonesData = zoneData.zones;
            renderZones(zonesData, metersData);
        }
    } catch (error) {
        console.error('Error refreshing data:', error);
        updateConnectionStatus(false, 0);
    } finally {
        if (refreshBtn) refreshBtn.disabled = false;
        if (refreshIcon) refreshIcon.classList.remove('animate-spin');
    }
}

function toggleFeeders() {
    showFeeders = !showFeeders;
    const btn = document.getElementById('toggle-feeders-btn');
    const span = btn?.querySelector('span');

    if (showFeeders) {
        renderFeeders(zonesData, metersData);
        if (btn) btn.classList.replace('text-slate-400', 'text-emerald-400');
        if (span) span.textContent = 'Hide Lines';
    } else {
        feederLines.forEach(l => map.removeLayer(l));
        feederLines = [];
        if (btn) btn.classList.replace('text-emerald-400', 'text-slate-400');
        if (span) span.textContent = 'Show Lines';
    }
}

function toggleZones() {
    showZones = !showZones;
    const btn = document.getElementById('toggle-zones-btn');
    const span = btn?.querySelector('span');

    if (showZones) {
        renderZones(zonesData, metersData);
        if (btn) btn.classList.replace('text-slate-400', 'text-emerald-400');
        if (span) span.textContent = 'Hide Zones';
    } else {
        zonePolygons.forEach(p => map.removeLayer(p));
        transformerMarkers.forEach(m => map.removeLayer(m));
        zonePolygons = [];
        transformerMarkers = [];
        if (btn) btn.classList.replace('text-emerald-400', 'text-slate-400');
        if (span) span.textContent = 'Show Zones';
    }
}

function startAutoRefresh(interval = 5000) {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(refreshData, interval);
}

function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    ws.onopen = () => console.log('WebSocket connected');
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.meter_id && markers[data.meter_id]) {
                const existingMeter = metersData.find(m => m.meter_id === data.meter_id);
                if (existingMeter) {
                    existingMeter.current_generation = data.energy_generated || existingMeter.current_generation;
                    existingMeter.current_consumption = data.energy_consumed || existingMeter.current_consumption;
                    // Update Zone ID if present (from backend grid_zone_id)
                    if (data.grid_zone_id !== undefined && data.grid_zone_id !== null) {
                        existingMeter.zone_id = data.grid_zone_id;
                    }
                    const popup = markers[data.meter_id].getPopup();
                    if (popup) popup.setContent(createPopupContent(existingMeter));
                }
            }
            updateStats(metersData);
            // Also update the zone legend stats in real-time
            if (zonesData && Object.keys(zonesData).length > 0) {
                updateZoneLegend(zonesData);
            }
        } catch (error) { }
    };
    ws.onclose = () => { console.log('WebSocket disconnected, reconnecting...'); setTimeout(initWebSocket, 3000); };
    ws.onerror = (error) => console.error('WebSocket error:', error);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    refreshData();
    startAutoRefresh(10000);
    initWebSocket();
});

