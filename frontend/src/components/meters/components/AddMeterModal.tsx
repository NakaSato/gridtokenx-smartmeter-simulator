import React, { useState } from 'react';
import { X, Plus, Loader2, MapPin, Sun, Zap, Settings, Cpu, ToggleLeft, ToggleRight, Activity, Wallet, Battery } from 'lucide-react';
import { useNetwork } from '@/components/providers/NetworkProvider';
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
    const { getApiUrl } = useNetwork();

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

            const res = await fetch(getApiUrl('/api/v1/meters'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || data.message || 'Failed to add meter');
            }

            onSuccess(data);
            onClose();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
            <div className="bg-slate-900 border border-white/10 rounded-[2rem] w-full max-w-2xl p-8 shadow-2xl scale-100 animate-in zoom-in-95 duration-300 max-h-[90vh] overflow-y-auto custom-scrollbar">
                <div className="flex justify-between items-start mb-8">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-emerald-500/20 rounded-2xl border border-emerald-500/20">
                            <Plus className="w-6 h-6 text-emerald-400" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-white tracking-tight uppercase leading-none">Register New Meter</h2>
                            <p className="text-[10px] text-slate-500 font-black uppercase tracking-[0.2em] mt-2 opacity-60">Grid Node Onboarding</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-xl transition-colors">
                        <X className="w-6 h-6 text-slate-500" />
                    </button>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl text-sm text-rose-300 font-bold flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-rose-500" />
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-8">
                    {/* Core Identity */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 px-1">
                            <Cpu className="w-4 h-4 text-slate-500" />
                            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Core Identity</span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-1">Meter Profile</label>
                                <select
                                    value={formData.meter_type}
                                    onChange={(e) => setFormData({ ...formData, meter_type: e.target.value })}
                                    className="w-full bg-slate-950 border border-white/5 rounded-2xl p-4 text-sm text-white outline-none focus:border-indigo-500/50 transition-all"
                                >
                                    {METER_TYPES.map(type => (
                                        <option key={type} value={type}>{type.replace(/_/g, ' ')}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-1">Location Alias</label>
                                <input
                                    type="text"
                                    value={formData.location}
                                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                                    placeholder="e.g. Zone_1_Building_A"
                                    className="w-full bg-slate-950 border border-white/5 rounded-2xl p-4 text-sm text-white outline-none focus:border-indigo-500/50 transition-all font-mono"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Geospatial Section */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 px-1">
                            <MapPin className="w-4 h-4 text-slate-500" />
                            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Spatial Data (Optional)</span>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-white/5 p-4 rounded-2xl border border-white/5 space-y-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Latitude</label>
                                <input
                                    type="number"
                                    step="any"
                                    value={formData.latitude}
                                    onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                                    placeholder="Auto-assign"
                                    className="w-full bg-transparent border-none p-0 text-sm text-white outline-none font-mono"
                                />
                            </div>
                            <div className="bg-white/5 p-4 rounded-2xl border border-white/5 space-y-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Longitude</label>
                                <input
                                    type="number"
                                    step="any"
                                    value={formData.longitude}
                                    onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                                    placeholder="Auto-assign"
                                    className="w-full bg-transparent border-none p-0 text-sm text-white outline-none font-mono"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Hardware Configuration */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 px-1">
                            <Zap className="w-4 h-4 text-slate-500" />
                            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Power Configuration</span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Solar Toggle */}
                            <div className={cn(
                                "p-5 rounded-[1.5rem] border transition-all duration-300 space-y-4",
                                formData.has_solar ? "bg-emerald-500/10 border-emerald-500/20" : "bg-white/5 border-white/5 opacity-60"
                            )}>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={cn("p-2 rounded-xl bg-slate-900/50", formData.has_solar ? "text-emerald-400" : "text-slate-500")}>
                                            <Sun className="w-4 h-4" />
                                        </div>
                                        <span className="text-sm font-black text-white uppercase tracking-tight">Solar PV</span>
                                    </div>
                                    <button 
                                        type="button"
                                        onClick={() => setFormData({...formData, has_solar: !formData.has_solar})}
                                    >
                                        {formData.has_solar ? <ToggleRight className="w-8 h-8 text-emerald-500" /> : <ToggleLeft className="w-8 h-8 text-slate-600" />}
                                    </button>
                                </div>
                                {formData.has_solar && (
                                    <div className="space-y-1 animate-in zoom-in-95 duration-200">
                                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest pl-1">Max Output (kW)</label>
                                        <input
                                            type="number"
                                            step="0.1"
                                            value={formData.solar_capacity}
                                            onChange={(e) => setFormData({ ...formData, solar_capacity: e.target.value })}
                                            className="w-full bg-slate-900/50 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-emerald-500/30 font-mono"
                                        />
                                    </div>
                                )}
                            </div>

                            {/* Battery Toggle */}
                            <div className={cn(
                                "p-5 rounded-[1.5rem] border transition-all duration-300 space-y-4",
                                formData.has_battery ? "bg-amber-500/10 border-amber-500/20" : "bg-white/5 border-white/5 opacity-60"
                            )}>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={cn("p-2 rounded-xl bg-slate-900/50", formData.has_battery ? "text-amber-400" : "text-slate-500")}>
                                            <Battery className="w-4 h-4" />
                                        </div>
                                        <span className="text-sm font-black text-white uppercase tracking-tight">Storage</span>
                                    </div>
                                    <button 
                                        type="button"
                                        onClick={() => setFormData({...formData, has_battery: !formData.has_battery})}
                                    >
                                        {formData.has_battery ? <ToggleRight className="w-8 h-8 text-amber-500" /> : <ToggleLeft className="w-8 h-8 text-slate-600" />}
                                    </button>
                                </div>
                                {formData.has_battery && (
                                    <div className="space-y-1 animate-in zoom-in-95 duration-200">
                                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest pl-1">Capacity (kWh)</label>
                                        <input
                                            type="number"
                                            step="0.1"
                                            value={formData.battery_capacity_kwh}
                                            onChange={(e) => setFormData({ ...formData, battery_capacity_kwh: e.target.value })}
                                            className="w-full bg-slate-900/50 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-amber-500/30 font-mono"
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Operational Limits */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 px-1">
                            <Activity className="w-4 h-4 text-slate-500" />
                            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Operational Limits</span>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2 p-4 bg-white/5 rounded-2xl border border-white/5">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.15em] pl-1">Min Load (kW)</label>
                                <input
                                    type="number"
                                    step="0.01"
                                    value={formData.min_load_kw}
                                    onChange={(e) => setFormData({ ...formData, min_load_kw: e.target.value })}
                                    className="w-full bg-slate-950 border border-white/5 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500/30 transition-all font-mono"
                                />
                            </div>
                            <div className="space-y-2 p-4 bg-white/5 rounded-2xl border border-white/5">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.15em] pl-1">Max Load (kW)</label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={formData.max_load_kw}
                                    onChange={(e) => setFormData({ ...formData, max_load_kw: e.target.value })}
                                    className="w-full bg-slate-950 border border-white/5 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500/30 transition-all font-mono"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Network Identity */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 px-1">
                            <Wallet className="w-4 h-4 text-slate-500" />
                            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Network Identity</span>
                        </div>
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-1">Custom Meter ID (Optional)</label>
                                <input
                                    type="text"
                                    value={formData.custom_id}
                                    onChange={(e) => setFormData({ ...formData, custom_id: e.target.value })}
                                    placeholder="e.g. SIM-NODE-404"
                                    className="w-full bg-slate-950 border border-white/5 rounded-2xl p-4 text-sm text-white outline-none focus:border-indigo-500/50 transition-all font-mono"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-1">Solana Wallet (Optional)</label>
                                <input
                                    type="text"
                                    value={formData.wallet_address}
                                    onChange={(e) => setFormData({ ...formData, wallet_address: e.target.value })}
                                    placeholder="Auto-generate"
                                    className="w-full bg-slate-950 border border-white/5 rounded-2xl p-4 text-sm text-white outline-none focus:border-indigo-500/50 transition-all font-mono"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-4 mt-12 pt-6 border-t border-white/5">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 py-4 rounded-2xl font-black text-xs uppercase tracking-widest text-slate-500 hover:bg-white/5 transition-all active:scale-[0.98]"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-[2] py-4 rounded-2xl font-black text-xs uppercase tracking-widest bg-emerald-500 text-white hover:bg-emerald-400 transition-all shadow-xl shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 active:scale-[0.98]"
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
    );
};

export default AddMeterModal;
