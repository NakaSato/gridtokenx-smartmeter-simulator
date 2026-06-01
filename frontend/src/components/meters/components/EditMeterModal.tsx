import React, { useState, useEffect } from 'react';
import { X, Save, Loader2, Sun, Battery, Zap, Settings, Cpu, ToggleLeft, ToggleRight, Activity } from 'lucide-react';
import { useNetwork } from '@/components/providers/NetworkProvider';
import type { Reading } from '@/lib/types';
import { cn } from '@/lib/common';

interface EditMeterModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (data: any) => void;
    meter: Reading | null;
}

const EV_TYPES = [
    "EV_Charger",
    "DC_Fast_Charger"
];

const EditMeterModal = ({ isOpen, onClose, onSuccess, meter }: EditMeterModalProps) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { getApiUrl } = useNetwork();

    const [formData, setFormData] = useState({
        meter_type: "",
        has_solar: false,
        solar_capacity: "",
        has_battery: false,
        battery_capacity: "",
        ev_battery_capacity: "",
        min_load_kw: "",
        max_load_kw: ""
    });

    useEffect(() => {
        if (meter) {
            setFormData({
                meter_type: meter.meter_type || "",
                has_solar: (meter as any).has_solar ?? (meter.energy_generated > 0),
                solar_capacity: (meter as any).solar_capacity?.toString() || "",
                has_battery: (meter as any).has_battery ?? (meter.battery_level > 0),
                battery_capacity: (meter as any).battery_capacity?.toString() || "",
                ev_battery_capacity: (meter as any).ev_battery_capacity?.toString() || "",
                min_load_kw: meter.min_load_kw?.toString() || "",
                max_load_kw: meter.max_load_kw?.toString() || ""
            });
        }
    }, [meter]);

    if (!isOpen || !meter) return null;

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
            const payload: any = {
                has_solar: formData.has_solar,
                has_battery: formData.has_battery
            };
            
            if (formData.solar_capacity !== "") payload.solar_capacity = parseFloat(formData.solar_capacity);
            if (formData.battery_capacity !== "") payload.battery_capacity = parseFloat(formData.battery_capacity);
            if (formData.min_load_kw !== "") payload.min_load_kw = parseFloat(formData.min_load_kw);
            if (formData.max_load_kw !== "") payload.max_load_kw = parseFloat(formData.max_load_kw);

            if (meter.meter_type.includes('EV') || meter.meter_type.includes('Charger')) {
                payload.meter_type = formData.meter_type;
                if (formData.ev_battery_capacity !== "") {
                    payload.ev_battery_capacity = parseFloat(formData.ev_battery_capacity);
                }
            }

            const res = await fetch(getApiUrl(`/api/v1/meters/${meter.meter_id}`), {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || 'Failed to update meter');
            }

            onSuccess(data);
            onClose();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const isEV = meter.meter_type.includes('EV') || meter.meter_type.includes('Charger');

    return (
        <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
            <div className="bg-slate-900 border border-white/10 rounded-[2rem] w-full max-w-xl p-8 shadow-2xl scale-100 animate-in zoom-in-95 duration-300 max-h-[90vh] overflow-y-auto custom-scrollbar">
                <div className="flex justify-between items-start mb-8">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-indigo-500/20 rounded-2xl border border-indigo-500/20">
                            <Cpu className="w-6 h-6 text-indigo-400" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-white tracking-tight uppercase">Meter Configuration</h2>
                            <p className="text-xs text-slate-500 font-mono mt-1 tracking-wider opacity-60">{meter.meter_id}</p>
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
                    {/* Device Identity Section */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 px-1">
                            <Settings className="w-4 h-4 text-slate-500" />
                            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Device Identity</span>
                        </div>
                        
                        {isEV ? (
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest pl-1">Charger Type</label>
                                <select
                                    value={formData.meter_type}
                                    onChange={(e) => setFormData({ ...formData, meter_type: e.target.value })}
                                    className="w-full bg-slate-950 border border-white/5 rounded-2xl p-4 text-sm text-white outline-none focus:border-indigo-500/50 transition-all ring-offset-0 focus:ring-4 focus:ring-indigo-500/10"
                                >
                                    {EV_TYPES.map(type => (
                                        <option key={type} value={type}>{type.replace(/_/g, ' ')}</option>
                                    ))}
                                </select>
                            </div>
                        ) : (
                            <div className="p-4 bg-white/5 border border-white/5 rounded-2xl flex items-center justify-between">
                                <span className="text-sm font-bold text-slate-400">Current Profile</span>
                                <span className="text-sm font-black text-white px-3 py-1 bg-white/5 rounded-lg border border-white/5">
                                    {(meter.meter_type || 'Residential').replace(/_/g, ' ')}
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Hardware Capabilities */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 px-1">
                            <Zap className="w-4 h-4 text-slate-500" />
                            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Hardware & Capacity</span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Solar Block */}
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
                                        className="transition-colors"
                                    >
                                        {formData.has_solar ? <ToggleRight className="w-8 h-8 text-emerald-500" /> : <ToggleLeft className="w-8 h-8 text-slate-600" />}
                                    </button>
                                </div>
                                {formData.has_solar && (
                                    <div className="space-y-1 animate-in slide-in-from-top-2 duration-300">
                                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest pl-1">Max Output (kW)</label>
                                        <input
                                            type="number"
                                            step="0.1"
                                            value={formData.solar_capacity}
                                            onChange={(e) => setFormData({ ...formData, solar_capacity: e.target.value })}
                                            className="w-full bg-slate-900/50 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-emerald-500/30 transition-colors"
                                            placeholder="e.g. 5.0"
                                        />
                                    </div>
                                )}
                            </div>

                            {/* Battery Block */}
                            <div className={cn(
                                "p-5 rounded-[1.5rem] border transition-all duration-300 space-y-4",
                                formData.has_battery ? "bg-amber-500/10 border-amber-500/20" : "bg-white/5 border-white/5 opacity-60"
                            )}>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={cn("p-2 rounded-xl bg-slate-900/50", formData.has_battery ? "text-amber-400" : "text-slate-500")}>
                                            <Battery className="w-4 h-4" />
                                        </div>
                                        <span className="text-sm font-black text-white uppercase tracking-tight">{isEV ? 'EV Battery' : 'BESS'}</span>
                                    </div>
                                    <button 
                                        type="button"
                                        onClick={() => setFormData({...formData, has_battery: !formData.has_battery})}
                                        className="transition-colors"
                                    >
                                        {formData.has_battery ? <ToggleRight className="w-8 h-8 text-amber-500" /> : <ToggleLeft className="w-8 h-8 text-slate-600" />}
                                    </button>
                                </div>
                                {formData.has_battery && (
                                    <div className="space-y-1 animate-in slide-in-from-top-2 duration-300">
                                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest pl-1">Storage Cap (kWh)</label>
                                        <input
                                            type="number"
                                            step="0.1"
                                            value={isEV ? formData.ev_battery_capacity : formData.battery_capacity}
                                            onChange={(e) => setFormData({ 
                                                ...formData, 
                                                [isEV ? 'ev_battery_capacity' : 'battery_capacity']: e.target.value 
                                            })}
                                            className="w-full bg-slate-900/50 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-amber-500/30 transition-colors"
                                            placeholder="e.g. 10.0"
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
                                    placeholder="0.1"
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
                                    placeholder="500.0"
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
                            className="flex-[2] py-4 rounded-2xl font-black text-xs uppercase tracking-widest bg-indigo-500 text-white hover:bg-indigo-400 transition-all shadow-xl shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 active:scale-[0.98]"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>Syncing Config...</span>
                                </>
                            ) : (
                                <>
                                    <Save className="w-4 h-4" />
                                    <span>Save Configuration</span>
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default EditMeterModal;
