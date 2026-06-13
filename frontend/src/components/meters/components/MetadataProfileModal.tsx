import React, { useState } from 'react';
import { X, Save, Plus, Trash2, Loader2, Info } from 'lucide-react';
import { useSimulatorApi } from '@/hooks/useSimulatorApi';
import type { Reading } from '@/lib/types';

interface MetadataProfileModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (data: any) => void;
    meter: Reading | null;
}

interface MetadataItem {
    id: string;
    key: string;
    value: string;
}

const blankItem = (): MetadataItem => ({ id: crypto.randomUUID(), key: '', value: '' });

/** Derive the editable rows from a meter's metadata (always >=1 blank row). */
function metadataToItems(meter: Reading | null): MetadataItem[] {
    const meta = meter && (meter as any).metadata;
    if (meta) {
        const rows = Object.entries(meta).map(([key, value]) => ({ id: crypto.randomUUID(), key, value: String(value) }));
        if (rows.length > 0) return rows;
    }
    return [blankItem()];
}

const MetadataProfileModal = ({ isOpen, onClose, onSuccess, meter }: MetadataProfileModalProps) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const api = useSimulatorApi();
    const [items, setItems] = useState<MetadataItem[]>(() => metadataToItems(meter));

    // Reset the rows when a different meter is shown — adjusted during render
    // (not in an effect) so the form never flashes the previous meter's values.
    const [prevMeterId, setPrevMeterId] = useState(meter?.meter_id);
    if (meter?.meter_id !== prevMeterId) {
        setPrevMeterId(meter?.meter_id);
        setItems(metadataToItems(meter));
    }

    if (!isOpen || !meter) return null;

    const handleAddItem = () => {
        setItems([...items, blankItem()]);
    };

    const handleRemoveItem = (index: number) => {
        const newItems = items.filter((_, i) => i !== index);
        setItems(newItems.length > 0 ? newItems : [blankItem()]);
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
        <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60">
            <div className="hmi-panel w-full max-w-xl max-h-[90vh] flex flex-col">
                <div className="hmi-panel-hd">
                    <div className="flex items-center gap-3">
                        <div className="p-2 border border-[var(--line-2)] bg-[var(--panel-2)]">
                            <Info className="w-5 h-5 text-[var(--txt-val)]" />
                        </div>
                        <div>
                            <h2 className="text-base font-semibold text-[var(--txt-val)] tracking-wide uppercase">Metadata Profile</h2>
                            <p className="hmi-meta mono mt-0.5">{meter.meter_id}</p>
                        </div>
                    </div>
                    <button type="button" onClick={onClose} aria-label="Close" className="hmi-btn">
                        <X className="w-4 h-4" />
                    </button>
                </div>

                <div className="hmi-panel-bd flex-1 overflow-hidden flex flex-col">
                    {error && (
                        <div className="mb-4 p-3 border border-[var(--alarm-bd)] bg-[var(--alarm-bg)] text-xs text-[var(--alarm)] font-semibold">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="flex-1 overflow-hidden flex flex-col">
                        <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                            <p className="hmi-lbl mb-4 px-1">Attribute Mapping</p>

                            {items.map((item, index) => (
                                <div key={item.id} className="flex gap-3">
                                    <div className="flex-1">
                                        <input
                                            type="text"
                                            value={item.key}
                                            onChange={(e) => handleChange(index, 'key', e.target.value)}
                                            placeholder="Property (e.g. Owner)"
                                            className="hmi-input w-full"
                                        />
                                    </div>
                                    <div className="flex-[1.5]">
                                        <input
                                            type="text"
                                            value={item.value}
                                            onChange={(e) => handleChange(index, 'value', e.target.value)}
                                            placeholder="Value"
                                            className="hmi-input w-full mono"
                                        />
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveItem(index)}
                                        className="hmi-btn alarm"
                                        title="Remove property"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}

                            <button
                                type="button"
                                onClick={handleAddItem}
                                className="hmi-btn w-full mt-2"
                            >
                                <Plus className="w-3.5 h-3.5" />
                                Add Property
                            </button>
                        </div>

                        <div className="flex gap-3 mt-6 pt-4 border-t border-[var(--line)]">
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
                                className="hmi-btn primary flex-1"
                            >
                                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                Save Profile
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default MetadataProfileModal;
