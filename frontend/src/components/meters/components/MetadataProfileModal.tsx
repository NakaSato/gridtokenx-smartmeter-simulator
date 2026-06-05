import React, { useState, useEffect } from 'react';
import { X, Save, Plus, Trash2, Loader2, Info } from 'lucide-react';
import { useSimulatorApi } from '@/hooks/useSimulatorApi';
import { cn } from '@/lib/common';
import type { Reading } from '@/lib/types';

interface MetadataProfileModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (data: any) => void;
    meter: Reading | null;
}

interface MetadataItem {
    key: string;
    value: string;
}

const MetadataProfileModal = ({ isOpen, onClose, onSuccess, meter }: MetadataProfileModalProps) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const api = useSimulatorApi();
    const [items, setItems] = useState<MetadataItem[]>([]);

    useEffect(() => {
        if (meter && (meter as any).metadata) {
            const meta = (meter as any).metadata;
            const initialItems = Object.entries(meta).map(([key, value]) => ({
                key,
                value: String(value)
            }));
            setItems(initialItems.length > 0 ? initialItems : [{ key: '', value: '' }]);
        } else {
            setItems([{ key: '', value: '' }]);
        }
    }, [meter]);

    if (!isOpen || !meter) return null;

    const handleAddItem = () => {
        setItems([...items, { key: '', value: '' }]);
    };

    const handleRemoveItem = (index: number) => {
        const newItems = items.filter((_, i) => i !== index);
        setItems(newItems.length > 0 ? newItems : [{ key: '', value: '' }]);
    };

    const handleChange = (index: number, field: 'key' | 'value', value: string) => {
        const newItems = [...items];
        newItems[index][field] = value;
        setItems(newItems);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            // Convert items array back to object
            const metadata: Record<string, string> = {};
            items.forEach(item => {
                if (item.key.trim()) {
                    metadata[item.key.trim()] = item.value;
                }
            });

            const data = await api.patchMeter(meter.meter_id, { metadata });

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
            <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-xl p-6 shadow-2xl scale-100 animate-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col">
                <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
                            <Info className="w-5 h-5 text-indigo-400" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">Metadata Profile</h2>
                            <p className="text-xs text-slate-500 font-mono mt-0.5">{meter.meter_id}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
                        <X className="w-5 h-5 text-slate-400" />
                    </button>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 font-bold">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="flex-1 overflow-hidden flex flex-col">
                    <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-4 px-1">Attribute Mapping</p>
                        
                        {items.map((item, index) => (
                            <div key={index} className="flex gap-3 animate-in slide-in-from-left-2 duration-200">
                                <div className="flex-1">
                                    <input
                                        type="text"
                                        value={item.key}
                                        onChange={(e) => handleChange(index, 'key', e.target.value)}
                                        placeholder="Property (e.g. Owner)"
                                        className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-700"
                                    />
                                </div>
                                <div className="flex-[1.5]">
                                    <input
                                        type="text"
                                        value={item.value}
                                        onChange={(e) => handleChange(index, 'value', e.target.value)}
                                        placeholder="Value"
                                        className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-700"
                                    />
                                </div>
                                <button
                                    type="button"
                                    onClick={() => handleRemoveItem(index)}
                                    className="p-3 text-slate-600 hover:text-rose-400 hover:bg-rose-500/5 rounded-xl transition-all"
                                    title="Remove property"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        ))}

                        <button
                            type="button"
                            onClick={handleAddItem}
                            className="w-full py-3 mt-2 border border-dashed border-white/5 rounded-xl text-xs font-bold text-slate-500 hover:text-indigo-400 hover:border-indigo-500/30 hover:bg-indigo-500/5 transition-all flex items-center justify-center gap-2 group"
                        >
                            <Plus className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
                            Add Property
                        </button>
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
                            className="flex-1 py-3 rounded-xl font-bold text-sm bg-indigo-500 text-white hover:bg-indigo-400 transition-all shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            Save Profile
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default MetadataProfileModal;
