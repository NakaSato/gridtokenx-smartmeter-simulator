import React, { useState } from 'react';
import { X, Plus, Loader2 } from 'lucide-react';
import { useNetwork } from '@/components/providers/NetworkProvider';

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
        solar_capacity: "5.0",
        trading_preference: "moderate",
        custom_id: "",
        wallet_address: ""
    });

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const payload = {
                ...formData,
                latitude: formData.latitude ? parseFloat(formData.latitude) : undefined,
                longitude: formData.longitude ? parseFloat(formData.longitude) : undefined,
                solar_capacity: formData.solar_capacity ? parseFloat(formData.solar_capacity) : 0,
            };

            const res = await fetch(getApiUrl('/api/v1/meters'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (!res.ok) {
                let errorMsg = data.detail || data.message || 'Failed to add meter';
                if (data.suggestion) {
                    errorMsg += `. Suggestion: ${data.suggestion}`;
                }
                throw new Error(errorMsg);
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
        <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-lg p-6 shadow-2xl scale-100 animate-in zoom-in-95 duration-200">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold text-white">Add New Meter</h2>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
                        <X className="w-5 h-5 text-slate-400" />
                    </button>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 font-bold">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-1">
                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Meter Type</label>
                        <select
                            value={formData.meter_type}
                            onChange={(e) => setFormData({ ...formData, meter_type: e.target.value })}
                            className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors"
                        >
                            {METER_TYPES.map(type => (
                                <option key={type} value={type}>{type.replace('_', ' ')}</option>
                            ))}
                        </select>
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Location</label>
                        <input
                            type="text"
                            value={formData.location}
                            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                            placeholder="e.g. Zone_1_Building_A"
                            className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Latitude (Optional)</label>
                            <input
                                type="number"
                                step="any"
                                value={formData.latitude}
                                onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                                placeholder="e.g. 13.7563"
                                className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors"
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Longitude (Optional)</label>
                            <input
                                type="number"
                                step="any"
                                value={formData.longitude}
                                onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                                placeholder="e.g. 100.5018"
                                className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors"
                            />
                        </div>
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Solar Capacity (kW)</label>
                        <input
                            type="number"
                            step="0.1"
                            value={formData.solar_capacity}
                            onChange={(e) => setFormData({ ...formData, solar_capacity: e.target.value })}
                            className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors"
                        />
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Trading Preference</label>
                        <select
                            value={formData.trading_preference}
                            onChange={(e) => setFormData({ ...formData, trading_preference: e.target.value })}
                            className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors"
                        >
                            <option value="conservative">Conservative (High Reserves)</option>
                            <option value="moderate">Moderate (Balanced)</option>
                            <option value="aggressive">Aggressive (Max Profit)</option>
                        </select>
                    </div>

                    <div className="pt-2 border-t border-white/5 mt-4">
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">Identity Settings</p>

                        <div className="space-y-3">
                            <div className="space-y-1">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Custom Meter ID (Optional)</label>
                                <input
                                    type="text"
                                    value={formData.custom_id}
                                    onChange={(e) => setFormData({ ...formData, custom_id: e.target.value })}
                                    placeholder="e.g. SIM-METER-001"
                                    className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Wallet Address (Optional)</label>
                                <input
                                    type="text"
                                    value={formData.wallet_address}
                                    onChange={(e) => setFormData({ ...formData, wallet_address: e.target.value })}
                                    placeholder="e.g. Sol..."
                                    className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-3 mt-6 pt-4 border-t border-white/10">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 py-3 rounded-xl font-bold text-sm text-slate-400 hover:bg-white/5 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 py-3 rounded-xl font-bold text-sm bg-emerald-500 text-white hover:bg-emerald-400 transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                            Add Meter
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AddMeterModal;
