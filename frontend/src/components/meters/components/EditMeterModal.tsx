import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { X, Save, Loader2, Sun, Battery, Zap, Settings, Cpu, ToggleLeft, ToggleRight, Activity, AlertCircle, Gauge } from 'lucide-react';
import { useSimulatorApi } from '@/hooks/useSimulatorApi';
import { useSimulator } from '@/components/providers/SimulatorProvider';
import type { Reading } from '@/lib/types';
import { cn } from '@/lib/common';
import { getMeterTheme } from './MeterTheme';

interface EditMeterModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (data: unknown) => void;
    meter: Reading | null;
}

interface MeterFormData {
    meter_type: string;
    has_solar: boolean;
    solar_capacity: string;
    has_battery: boolean;
    battery_capacity: string;
    ev_battery_capacity: string;
    min_load_kw: string;
    max_load_kw: string;
}

interface PatchMeterPayload {
    has_solar: boolean;
    has_battery: boolean;
    solar_capacity?: number;
    battery_capacity?: number;
    ev_battery_capacity?: number;
    min_load_kw?: number;
    max_load_kw?: number;
    meter_type?: string;
    [key: string]: unknown;
}

const EV_TYPES = [
    "EV_Charger",
    "DC_Fast_Charger"
];

const EMPTY_FORM: MeterFormData = {
    meter_type: "",
    has_solar: false,
    solar_capacity: "",
    has_battery: false,
    battery_capacity: "",
    ev_battery_capacity: "",
    min_load_kw: "",
    max_load_kw: ""
};

// Map a meter record onto editable form fields. Falls back to live readings
// when explicit capability flags are absent (older backends).
function meterToForm(meter: Reading): MeterFormData {
    return {
        meter_type: meter.meter_type || "",
        has_solar: meter.has_solar ?? (meter.energy_generated > 0),
        solar_capacity: meter.solar_capacity?.toString() || "",
        has_battery: meter.has_battery ?? (meter.battery_level > 0),
        battery_capacity: meter.battery_capacity?.toString() || "",
        ev_battery_capacity: (meter.ev_battery_capacity as number | undefined)?.toString() || "",
        min_load_kw: meter.min_load_kw?.toString() || "",
        max_load_kw: meter.max_load_kw?.toString() || ""
    };
}

const EditMeterModal = ({ isOpen, onClose, onSuccess, meter }: EditMeterModalProps) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const api = useSimulatorApi();
    const { updateMeterReading, overrideMeterReading } = useSimulator();

    const [formData, setFormData] = useState<MeterFormData>(EMPTY_FORM);
    const [initialData, setInitialData] = useState<MeterFormData>(EMPTY_FORM);

    useEffect(() => {
        if (meter) {
            const next = meterToForm(meter);
            setFormData(next);
            setInitialData(next);
            setError(null);
        }
    }, [meter]);

    // Esc to close + lock body scroll while the modal is open.
    useEffect(() => {
        if (!isOpen) return;
        const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
        window.addEventListener('keydown', onKey);
        const prevOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        return () => {
            window.removeEventListener('keydown', onKey);
            document.body.style.overflow = prevOverflow;
        };
    }, [isOpen, onClose]);

    const isEV = !!meter && (meter.meter_type.includes('EV') || meter.meter_type.includes('Charger'));
    const isDirty = useMemo(
        () => JSON.stringify(formData) !== JSON.stringify(initialData),
        [formData, initialData]
    );

    const handleSubmit = useCallback(async (e: React.FormEvent) => {
        e.preventDefault();
        if (!meter) return;

        // Validate every populated numeric field: must parse and be non-negative.
        const fields: [string, string][] = [
            ['Min Load', formData.min_load_kw],
            ['Max Load', formData.max_load_kw],
        ];
        if (formData.has_solar) fields.push(['Solar capacity', formData.solar_capacity]);
        if (formData.has_battery) {
            fields.push(isEV
                ? ['EV battery capacity', formData.ev_battery_capacity]
                : ['Battery capacity', formData.battery_capacity]);
        }
        for (const [label, val] of fields) {
            if (val === "") continue;
            const n = parseFloat(val);
            if (isNaN(n)) { setError(`${label} must be a number`); return; }
            if (n < 0) { setError(`${label} cannot be negative`); return; }
        }

        const minVal = parseFloat(formData.min_load_kw);
        const maxVal = parseFloat(formData.max_load_kw);
        if (!isNaN(minVal) && !isNaN(maxVal) && minVal > maxVal) {
            setError("Max Load must be greater than Min Load");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const payload: PatchMeterPayload = {
                has_solar: formData.has_solar,
                has_battery: formData.has_battery
            };

            if (formData.solar_capacity !== "") payload.solar_capacity = parseFloat(formData.solar_capacity);
            if (formData.battery_capacity !== "") payload.battery_capacity = parseFloat(formData.battery_capacity);
            if (formData.min_load_kw !== "") payload.min_load_kw = parseFloat(formData.min_load_kw);
            if (formData.max_load_kw !== "") payload.max_load_kw = parseFloat(formData.max_load_kw);

            if (isEV) {
                payload.meter_type = formData.meter_type;
                if (formData.ev_battery_capacity !== "") {
                    payload.ev_battery_capacity = parseFloat(formData.ev_battery_capacity);
                }
            }

            const data = await api.patchMeter(meter.meter_id, payload);

            onSuccess(data);
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to update meter');
        } finally {
            setLoading(false);
        }
    }, [meter, formData, isEV, api, onSuccess, onClose]);

    if (!isOpen || !meter) return null;

    // Live snapshot for read-only context (prefer instantaneous power).
    const liveGen = meter.generation_kw ?? meter.energy_generated ?? 0;
    const liveCons = meter.consumption_kw ?? meter.energy_consumed ?? 0;
    const liveVolt = meter.voltage;
    const liveSoc = meter.battery_level ?? 0;
    const theme = getMeterTheme(meter.meter_type);

    return (
        <div
            className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60 backdrop-blur-md animate-in fade-in duration-300"
            onClick={onClose}
        >
            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby="meter-config-title"
                onClick={(e) => e.stopPropagation()}
                className="relative bg-slate-900 border border-white/10 rounded-[2rem] w-full max-w-xl p-8 shadow-2xl scale-100 animate-in zoom-in-95 duration-300 max-h-[90vh] overflow-y-auto custom-scrollbar"
            >
                {/* Type-themed glow */}
                <div aria-hidden className={cn("pointer-events-none absolute inset-x-0 -top-32 h-48 bg-gradient-to-b blur-3xl opacity-50", theme.gradient)} />

                <div className="relative flex justify-between items-start mb-8">
                    <div className="flex items-center gap-4">
                        <div className={cn("p-3 rounded-2xl border bg-white/5 shadow-lg", theme.border, theme.glow)}>
                            <Cpu className={cn("w-6 h-6", theme.icon)} />
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <h2 id="meter-config-title" className="text-2xl font-black text-white tracking-tight uppercase">Meter Configuration</h2>
                                {isDirty && (
                                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-500/30" title="Unsaved changes">
                                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                                        <span className="text-[8px] font-black uppercase tracking-widest text-amber-400">Edited</span>
                                    </span>
                                )}
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                                <span className={cn("px-2 py-0.5 rounded-md text-[9px] font-black uppercase tracking-widest bg-white/5 border", theme.border, theme.icon)}>
                                    {(meter.meter_type || 'Residential').replace(/_/g, ' ')}
                                </span>
                                <p className="text-xs text-slate-500 font-mono tracking-wider opacity-60">{meter.meter_id}</p>
                            </div>
                        </div>
                    </div>
                    <button type="button" onClick={onClose} aria-label="Close" className="p-2 hover:bg-white/5 rounded-xl transition-colors">
                        <X className="w-6 h-6 text-slate-500" />
                    </button>
                </div>

                {/* Live Readings (read-only context) */}
                <div className="mb-8 grid grid-cols-4 gap-3">
                    {[
                        { label: 'Gen', value: `${liveGen.toFixed(2)}`, unit: 'kW', tone: 'text-emerald-400', Icon: Sun },
                        { label: 'Cons', value: `${liveCons.toFixed(2)}`, unit: 'kW', tone: 'text-rose-400', Icon: Zap },
                        { label: 'Volt', value: liveVolt != null ? `${liveVolt.toFixed(0)}` : '—', unit: 'V', tone: 'text-sky-400', Icon: Gauge },
                        { label: 'SoC', value: `${liveSoc.toFixed(0)}`, unit: '%', tone: 'text-amber-400', Icon: Battery },
                    ].map(({ label, value, unit, tone, Icon }) => (
                        <div key={label} className="p-3 rounded-2xl bg-white/5 border border-white/5 flex flex-col gap-1">
                            <div className="flex items-center gap-1.5">
                                <Icon className={cn("w-3 h-3", tone)} />
                                <span className="text-[8px] font-black uppercase tracking-widest text-slate-600">{label}</span>
                            </div>
                            <div className="text-sm font-black text-white tracking-tighter">
                                {value} <span className="text-[9px] opacity-40 uppercase">{unit}</span>
                            </div>
                        </div>
                    ))}
                </div>

                {error && (
                    <div role="alert" className="mb-6 p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl text-sm text-rose-300 font-bold flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-rose-500" />
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-8">
                    {/* Device Identity Section (EV only — profile shown in header badge otherwise) */}
                    {isEV && (
                        <div className="space-y-4">
                            <div className="flex items-center gap-2 px-1">
                                <Settings className="w-4 h-4 text-slate-500" />
                                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Device Identity</span>
                            </div>
                            <div className="space-y-2">
                                <label htmlFor="charger-type" className="text-xs font-bold text-slate-400 uppercase tracking-widest pl-1">Charger Type</label>
                                <select
                                    id="charger-type"
                                    value={formData.meter_type}
                                    onChange={(e) => setFormData({ ...formData, meter_type: e.target.value })}
                                    className="w-full bg-slate-950 border border-white/5 rounded-2xl p-4 text-sm text-white outline-none focus:border-indigo-500/50 transition-all ring-offset-0 focus:ring-4 focus:ring-indigo-500/10"
                                >
                                    {EV_TYPES.map(type => (
                                        <option key={type} value={type}>{type.replace(/_/g, ' ')}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    )}

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
                                        aria-pressed={formData.has_solar}
                                        aria-label="Toggle Solar PV"
                                        onClick={() => setFormData({...formData, has_solar: !formData.has_solar})}
                                        className="transition-colors"
                                    >
                                        {formData.has_solar ? <ToggleRight className="w-8 h-8 text-emerald-500" /> : <ToggleLeft className="w-8 h-8 text-slate-600" />}
                                    </button>
                                </div>
                                {formData.has_solar && (
                                    <div className="space-y-1 animate-in slide-in-from-top-2 duration-300">
                                        <label htmlFor="solar-cap" className="text-[10px] font-bold text-slate-500 uppercase tracking-widest pl-1">Max Output (kW)</label>
                                        <input
                                            id="solar-cap"
                                            type="number"
                                            step="0.1"
                                            min="0"
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
                                        aria-pressed={formData.has_battery}
                                        aria-label="Toggle battery storage"
                                        onClick={() => setFormData({...formData, has_battery: !formData.has_battery})}
                                        className="transition-colors"
                                    >
                                        {formData.has_battery ? <ToggleRight className="w-8 h-8 text-amber-500" /> : <ToggleLeft className="w-8 h-8 text-slate-600" />}
                                    </button>
                                </div>
                                {formData.has_battery && (
                                    <div className="space-y-1 animate-in slide-in-from-top-2 duration-300">
                                        <label htmlFor="batt-cap" className="text-[10px] font-bold text-slate-500 uppercase tracking-widest pl-1">Storage Cap (kWh)</label>
                                        <input
                                            id="batt-cap"
                                            type="number"
                                            step="0.1"
                                            min="0"
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
                                <label htmlFor="min-load" className="text-[10px] font-black text-slate-500 uppercase tracking-[0.15em] pl-1">Min Load (kW)</label>
                                <input
                                    id="min-load"
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    value={formData.min_load_kw}
                                    onChange={(e) => setFormData({ ...formData, min_load_kw: e.target.value })}
                                    className="w-full bg-slate-950 border border-white/5 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500/30 transition-all font-mono"
                                    placeholder="0.1"
                                />
                            </div>
                            <div className="space-y-2 p-4 bg-white/5 rounded-2xl border border-white/5">
                                <label htmlFor="max-load" className="text-[10px] font-black text-slate-500 uppercase tracking-[0.15em] pl-1">Max Load (kW)</label>
                                <input
                                    id="max-load"
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    value={formData.max_load_kw}
                                    onChange={(e) => setFormData({ ...formData, max_load_kw: e.target.value })}
                                    className="w-full bg-slate-950 border border-white/5 rounded-xl p-3 text-sm text-white outline-none focus:border-indigo-500/30 transition-all font-mono"
                                    placeholder="500.0"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Reading Override Section */}
                    <div className="space-y-4 pt-6 border-t border-white/5">
                        <div className="flex items-center gap-2 px-1">
                            <AlertCircle className="w-4 h-4 text-rose-500" />
                            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-rose-500">Reading Override (Testing)</span>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <button
                                type="button"
                                onClick={() => overrideMeterReading(meter.meter_id, { value: 0, field: 'consumption', duration_ticks: 10 })}
                                className="p-3 rounded-xl bg-rose-950/30 border border-rose-900 text-[10px] font-black text-rose-400 uppercase tracking-widest hover:bg-rose-950 transition-all"
                            >
                                Zero Cons
                            </button>
                            <button
                                type="button"
                                onClick={() => overrideMeterReading(meter.meter_id, { value: 100, field: 'consumption', duration_ticks: 10 })}
                                className="p-3 rounded-xl bg-rose-950/30 border border-rose-900 text-[10px] font-black text-rose-400 uppercase tracking-widest hover:bg-rose-950 transition-all"
                            >
                                Max Cons
                            </button>
                            <button
                                type="button"
                                onClick={() => updateMeterReading(meter.meter_id, { consumption: 50 })}
                                className="p-3 rounded-xl bg-indigo-950/30 border border-indigo-900 text-[10px] font-black text-indigo-400 uppercase tracking-widest hover:bg-indigo-950 transition-all"
                            >
                                Set Cons: 50
                            </button>
                        </div>
                    </div>

                    <div className="sticky bottom-0 -mx-8 -mb-8 px-8 pt-6 pb-8 flex gap-4 mt-12 border-t border-white/5 bg-slate-900/80 backdrop-blur-xl">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 py-4 rounded-2xl font-black text-xs uppercase tracking-widest text-slate-500 hover:bg-white/5 transition-all active:scale-[0.98]"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading || !isDirty}
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
                                    <span>{isDirty ? 'Save Configuration' : 'No Changes'}</span>
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
