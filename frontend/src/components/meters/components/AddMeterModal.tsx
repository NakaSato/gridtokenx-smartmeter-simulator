import React, { useState } from 'react';
import { X, Plus, Loader2, MapPin, Sun, Zap, Cpu, ToggleLeft, ToggleRight, Activity, Wallet, Battery } from 'lucide-react';
import { useSimulatorApi } from '@/hooks/useSimulatorApi';
import { clearTopologyCache } from '@/lib/topology/cache';
import { cn } from '@/lib/common';

interface AddMeterModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (data: any) => void;
}

const METER_TYPES = [
    "Solar_Prosumer",
    "Grid_Consumer",
    "Hybrid_Prosumer",
    "Battery_Storage",
    "Residential",
    "Commercial"
];

const AddMeterModal = ({ isOpen, onClose, onSuccess }: AddMeterModalProps) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const api = useSimulatorApi();

    const [formData, setFormData] = useState({
        meter_type: "Solar_Prosumer",
        location: "",
        latitude: "",
        longitude: "",
        has_solar: true,
        solar_capacity: "5.0",
        has_battery: false,
        battery_capacity_kwh: "10.0",
        min_load_kw: "0.1",
        max_load_kw: "500.0",
        trading_preference: "moderate",
        custom_id: "",
        wallet_address: ""
    });

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Basic validation
        const minVal = parseFloat(formData.min_load_kw);
        const maxVal = parseFloat(formData.max_load_kw);
        if (!isNaN(minVal) && !isNaN(maxVal) && minVal > maxVal) {
            setError("Max Load must be greater than Min Load");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const payload = {
                meter_type: formData.meter_type,
                location: formData.location || undefined,
                lat: formData.latitude ? parseFloat(formData.latitude) : undefined,
                lon: formData.longitude ? parseFloat(formData.longitude) : undefined,
                has_solar: formData.has_solar,
                solar_capacity: formData.has_solar ? parseFloat(formData.solar_capacity) : 0,
                has_battery: formData.has_battery,
                battery_capacity_kwh: formData.has_battery ? parseFloat(formData.battery_capacity_kwh) : 0,
                min_load_kw: parseFloat(formData.min_load_kw),
                max_load_kw: parseFloat(formData.max_load_kw),
                custom_id: formData.custom_id || undefined,
                wallet_address: formData.wallet_address || undefined
            };

            const data = await api.createMeter(payload);

            clearTopologyCache(); // new meter attached to a bus → topology changed
            onSuccess(data);
            onClose();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60">
            <div className="hmi-panel w-full max-w-2xl max-h-[90vh] overflow-y-auto custom-scrollbar">
                <div className="hmi-panel-hd">
                    <div className="flex items-center gap-3">
                        <div className="p-2 border border-[var(--line-2)] bg-[var(--panel-2)]">
                            <Plus className="w-5 h-5 text-[var(--txt-val)]" />
                        </div>
                        <div>
                            <h2 className="text-base font-semibold text-[var(--txt-val)] tracking-wide uppercase leading-none">Register New Meter</h2>
                            <p className="hmi-lbl mt-1">Grid Node Onboarding</p>
                        </div>
                    </div>
                    <button type="button" onClick={onClose} aria-label="Close" className="hmi-btn">
                        <X className="w-4 h-4" />
                    </button>
                </div>

                <div className="hmi-panel-bd">
                    {error && (
                        <div className="mb-6 p-3 border border-[var(--alarm-bd)] bg-[var(--alarm-bg)] text-sm text-[var(--alarm)] flex items-center gap-3">
                            <span className="hmi-dot alarm" />
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Core Identity */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 px-1">
                                <Cpu className="w-4 h-4 text-[var(--lbl)]" />
                                <span className="hmi-lbl">Core Identity</span>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label htmlFor="add-meter-type" className="hmi-lbl block">Meter Profile</label>
                                    <select
                                        id="add-meter-type"
                                        value={formData.meter_type}
                                        onChange={(e) => setFormData({ ...formData, meter_type: e.target.value })}
                                        className="hmi-input w-full"
                                    >
                                        {METER_TYPES.map(type => (
                                            <option key={type} value={type}>{type.replace(/_/g, ' ')}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="space-y-2">
                                    <label htmlFor="add-location" className="hmi-lbl block">Location Alias</label>
                                    <input
                                        id="add-location"
                                        type="text"
                                        value={formData.location}
                                        onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                                        placeholder="e.g. Zone_1_Building_A"
                                        className="hmi-input w-full mono"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Geospatial Section */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 px-1">
                                <MapPin className="w-4 h-4 text-[var(--lbl)]" />
                                <span className="hmi-lbl">Spatial Data (Optional)</span>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-[var(--panel-2)] border border-[var(--line)] p-3 space-y-2">
                                    <label htmlFor="add-latitude" className="hmi-lbl block">Latitude</label>
                                    <input
                                        id="add-latitude"
                                        type="number"
                                        step="any"
                                        value={formData.latitude}
                                        onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                                        placeholder="Auto-assign"
                                        className="hmi-input w-full mono"
                                    />
                                </div>
                                <div className="bg-[var(--panel-2)] border border-[var(--line)] p-3 space-y-2">
                                    <label htmlFor="add-longitude" className="hmi-lbl block">Longitude</label>
                                    <input
                                        id="add-longitude"
                                        type="number"
                                        step="any"
                                        value={formData.longitude}
                                        onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                                        placeholder="Auto-assign"
                                        className="hmi-input w-full mono"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Hardware Configuration */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 px-1">
                                <Zap className="w-4 h-4 text-[var(--lbl)]" />
                                <span className="hmi-lbl">Power Configuration</span>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* Solar Toggle */}
                                <div className={cn(
                                    "p-4 border bg-[var(--panel-2)] border-[var(--line)] space-y-3",
                                    !formData.has_solar && "opacity-60"
                                )}>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className={cn("p-2 border border-[var(--line)] bg-[var(--canvas)]", formData.has_solar ? "text-[var(--txt-val)]" : "text-[var(--lbl-dim)]")}>
                                                <Sun className="w-4 h-4" />
                                            </div>
                                            <span className="text-sm font-semibold text-[var(--txt-val)] uppercase tracking-wide">Solar PV</span>
                                        </div>
                                        <button
                                            type="button"
                                            aria-label="Toggle solar PV"
                                            onClick={() => setFormData({...formData, has_solar: !formData.has_solar})}
                                        >
                                            {formData.has_solar ? <ToggleRight className="w-8 h-8 text-[var(--ok)]" /> : <ToggleLeft className="w-8 h-8 text-[var(--lbl-dim)]" />}
                                        </button>
                                    </div>
                                    {formData.has_solar && (
                                        <div className="space-y-1">
                                            <label htmlFor="add-solar-capacity" className="hmi-lbl block">Max Output (kW)</label>
                                            <input
                                                id="add-solar-capacity"
                                                type="number"
                                                step="0.1"
                                                value={formData.solar_capacity}
                                                onChange={(e) => setFormData({ ...formData, solar_capacity: e.target.value })}
                                                className="hmi-input w-full mono"
                                            />
                                        </div>
                                    )}
                                </div>

                                {/* Battery Toggle */}
                                <div className={cn(
                                    "p-4 border bg-[var(--panel-2)] border-[var(--line)] space-y-3",
                                    !formData.has_battery && "opacity-60"
                                )}>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className={cn("p-2 border border-[var(--line)] bg-[var(--canvas)]", formData.has_battery ? "text-[var(--txt-val)]" : "text-[var(--lbl-dim)]")}>
                                                <Battery className="w-4 h-4" />
                                            </div>
                                            <span className="text-sm font-semibold text-[var(--txt-val)] uppercase tracking-wide">Storage</span>
                                        </div>
                                        <button
                                            type="button"
                                            aria-label="Toggle battery storage"
                                            onClick={() => setFormData({...formData, has_battery: !formData.has_battery})}
                                        >
                                            {formData.has_battery ? <ToggleRight className="w-8 h-8 text-[var(--ok)]" /> : <ToggleLeft className="w-8 h-8 text-[var(--lbl-dim)]" />}
                                        </button>
                                    </div>
                                    {formData.has_battery && (
                                        <div className="space-y-1">
                                            <label htmlFor="add-battery-capacity" className="hmi-lbl block">Capacity (kWh)</label>
                                            <input
                                                id="add-battery-capacity"
                                                type="number"
                                                step="0.1"
                                                value={formData.battery_capacity_kwh}
                                                onChange={(e) => setFormData({ ...formData, battery_capacity_kwh: e.target.value })}
                                                className="hmi-input w-full mono"
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Operational Limits */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 px-1">
                                <Activity className="w-4 h-4 text-[var(--lbl)]" />
                                <span className="hmi-lbl">Operational Limits</span>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2 p-3 bg-[var(--panel-2)] border border-[var(--line)]">
                                    <label htmlFor="add-min-load" className="hmi-lbl block">Min Load (kW)</label>
                                    <input
                                        id="add-min-load"
                                        type="number"
                                        step="0.01"
                                        value={formData.min_load_kw}
                                        onChange={(e) => setFormData({ ...formData, min_load_kw: e.target.value })}
                                        className="hmi-input w-full mono"
                                    />
                                </div>
                                <div className="space-y-2 p-3 bg-[var(--panel-2)] border border-[var(--line)]">
                                    <label htmlFor="add-max-load" className="hmi-lbl block">Max Load (kW)</label>
                                    <input
                                        id="add-max-load"
                                        type="number"
                                        step="0.1"
                                        value={formData.max_load_kw}
                                        onChange={(e) => setFormData({ ...formData, max_load_kw: e.target.value })}
                                        className="hmi-input w-full mono"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Network Identity */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 px-1">
                                <Wallet className="w-4 h-4 text-[var(--lbl)]" />
                                <span className="hmi-lbl">Network Identity</span>
                            </div>
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label htmlFor="add-custom-id" className="hmi-lbl block">Custom Meter ID (Optional)</label>
                                    <input
                                        id="add-custom-id"
                                        type="text"
                                        value={formData.custom_id}
                                        onChange={(e) => setFormData({ ...formData, custom_id: e.target.value })}
                                        placeholder="e.g. SIM-NODE-404"
                                        className="hmi-input w-full mono"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label htmlFor="add-wallet-address" className="hmi-lbl block">Solana Wallet (Optional)</label>
                                    <input
                                        id="add-wallet-address"
                                        type="text"
                                        value={formData.wallet_address}
                                        onChange={(e) => setFormData({ ...formData, wallet_address: e.target.value })}
                                        placeholder="Auto-generate"
                                        className="hmi-input w-full mono"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="flex gap-3 mt-8 pt-5 border-t border-[var(--line)]">
                            <button
                                type="button"
                                onClick={onClose}
                                className="hmi-btn flex-1"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={loading}
                                className="hmi-btn ok flex-[2]"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        <span>Deploying Node...</span>
                                    </>
                                ) : (
                                    <>
                                        <Plus className="w-4 h-4" />
                                        <span>Register Meter</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default AddMeterModal;
