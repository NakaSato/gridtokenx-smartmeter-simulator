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

    const [formData, setFormData] = useState<MeterFormData>(() => meter ? meterToForm(meter) : EMPTY_FORM);
    const [initialData, setInitialData] = useState<MeterFormData>(() => meter ? meterToForm(meter) : EMPTY_FORM);

    // Reload the form when a different meter is opened — adjusted during render
    // (not in an effect) so the fields never flash the previous meter's values.
    const [prevMeterId, setPrevMeterId] = useState(meter?.meter_id);
    if (meter && meter.meter_id !== prevMeterId) {
        setPrevMeterId(meter.meter_id);
        const next = meterToForm(meter);
        setFormData(next);
        setInitialData(next);
        setError(null);
    }

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
            className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60"
            onClick={onClose}
        >
            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby="meter-config-title"
                onClick={(e) => e.stopPropagation()}
                className="relative hmi-panel w-full max-w-xl max-h-[90vh] overflow-y-auto custom-scrollbar"
            >
                <div className="hmi-panel-hd">
                    <div className="flex items-center gap-3">
                        <div className={cn("p-2 border bg-[var(--panel-2)]", theme.border)}>
                            <Cpu className={cn("w-5 h-5", theme.icon)} />
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <h2 id="meter-config-title" className="text-base font-semibold text-[var(--txt-val)] tracking-wide uppercase">Meter Configuration</h2>
                                {isDirty && (
                                    <span className="hmi-chip warn" title="Unsaved changes">Edited</span>
                                )}
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                                <span className={cn("hmi-chip", theme.border, theme.icon)}>
                                    {(meter.meter_type || 'Residential').replace(/_/g, ' ')}
                                </span>
                                <p className="hmi-meta mono">{meter.meter_id}</p>
                            </div>
                        </div>
                    </div>
                    <button type="button" onClick={onClose} aria-label="Close" className="hmi-btn">
                        <X className="w-4 h-4" />
                    </button>
                </div>

                <div className="hmi-panel-bd">
                {/* Live Readings (read-only context) */}
                <div className="mb-6 grid grid-cols-4 gap-3">
                    {[
                        { label: 'Gen', value: `${liveGen.toFixed(2)}`, unit: 'kW', Icon: Sun },
                        { label: 'Cons', value: `${liveCons.toFixed(2)}`, unit: 'kW', Icon: Zap },
                        { label: 'Volt', value: liveVolt != null ? `${liveVolt.toFixed(0)}` : '—', unit: 'V', Icon: Gauge },
                        { label: 'SoC', value: `${liveSoc.toFixed(0)}`, unit: '%', Icon: Battery },
                    ].map(({ label, value, unit, Icon }) => (
                        <div key={label} className="p-3 bg-[var(--panel-2)] border border-[var(--line)] flex flex-col gap-1">
                            <div className="flex items-center gap-1.5">
                                <Icon className="w-3 h-3 text-[var(--lbl)]" />
                                <span className="hmi-lbl">{label}</span>
                            </div>
                            <div className="text-sm font-medium text-[var(--txt-val)] mono">
                                {value} <span className="hmi-unit">{unit}</span>
                            </div>
                        </div>
                    ))}
                </div>

                {error && (
                    <div role="alert" className="mb-6 p-3 border border-[var(--alarm-bd)] bg-[var(--alarm-bg)] text-sm text-[var(--alarm)] font-semibold flex items-center gap-3">
                        <span className="hmi-dot alarm" />
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Device Identity Section (EV only — profile shown in header badge otherwise) */}
                    {isEV && (
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 px-1">
                                <Settings className="w-4 h-4 text-[var(--lbl)]" />
                                <span className="hmi-lbl">Device Identity</span>
                            </div>
                            <div className="space-y-2">
                                <label htmlFor="charger-type" className="hmi-lbl block">Charger Type</label>
                                <select
                                    id="charger-type"
                                    value={formData.meter_type}
                                    onChange={(e) => setFormData({ ...formData, meter_type: e.target.value })}
                                    className="hmi-input w-full"
                                >
                                    {EV_TYPES.map(type => (
                                        <option key={type} value={type}>{type.replace(/_/g, ' ')}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    )}

                    {/* Hardware Capabilities */}
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 px-1">
                            <Zap className="w-4 h-4 text-[var(--lbl)]" />
                            <span className="hmi-lbl">Hardware & Capacity</span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Solar Block */}
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
                                        aria-pressed={formData.has_solar}
                                        aria-label="Toggle Solar PV"
                                        onClick={() => setFormData({...formData, has_solar: !formData.has_solar})}
                                    >
                                        {formData.has_solar ? <ToggleRight className="w-8 h-8 text-[var(--ok)]" /> : <ToggleLeft className="w-8 h-8 text-[var(--lbl-dim)]" />}
                                    </button>
                                </div>
                                {formData.has_solar && (
                                    <div className="space-y-1">
                                        <label htmlFor="solar-cap" className="hmi-lbl block">Max Output (kW)</label>
                                        <input
                                            id="solar-cap"
                                            type="number"
                                            step="0.1"
                                            min="0"
                                            value={formData.solar_capacity}
                                            onChange={(e) => setFormData({ ...formData, solar_capacity: e.target.value })}
                                            className="hmi-input w-full mono"
                                            placeholder="e.g. 5.0"
                                        />
                                    </div>
                                )}
                            </div>

                            {/* Battery Block */}
                            <div className={cn(
                                "p-4 border bg-[var(--panel-2)] border-[var(--line)] space-y-3",
                                !formData.has_battery && "opacity-60"
                            )}>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={cn("p-2 border border-[var(--line)] bg-[var(--canvas)]", formData.has_battery ? "text-[var(--txt-val)]" : "text-[var(--lbl-dim)]")}>
                                            <Battery className="w-4 h-4" />
                                        </div>
                                        <span className="text-sm font-semibold text-[var(--txt-val)] uppercase tracking-wide">{isEV ? 'EV Battery' : 'BESS'}</span>
                                    </div>
                                    <button
                                        type="button"
                                        aria-pressed={formData.has_battery}
                                        aria-label="Toggle battery storage"
                                        onClick={() => setFormData({...formData, has_battery: !formData.has_battery})}
                                    >
                                        {formData.has_battery ? <ToggleRight className="w-8 h-8 text-[var(--ok)]" /> : <ToggleLeft className="w-8 h-8 text-[var(--lbl-dim)]" />}
                                    </button>
                                </div>
                                {formData.has_battery && (
                                    <div className="space-y-1">
                                        <label htmlFor="batt-cap" className="hmi-lbl block">Storage Cap (kWh)</label>
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
                                            className="hmi-input w-full mono"
                                            placeholder="e.g. 10.0"
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
                                <label htmlFor="min-load" className="hmi-lbl block">Min Load (kW)</label>
                                <input
                                    id="min-load"
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    value={formData.min_load_kw}
                                    onChange={(e) => setFormData({ ...formData, min_load_kw: e.target.value })}
                                    className="hmi-input w-full mono"
                                    placeholder="0.1"
                                />
                            </div>
                            <div className="space-y-2 p-3 bg-[var(--panel-2)] border border-[var(--line)]">
                                <label htmlFor="max-load" className="hmi-lbl block">Max Load (kW)</label>
                                <input
                                    id="max-load"
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    value={formData.max_load_kw}
                                    onChange={(e) => setFormData({ ...formData, max_load_kw: e.target.value })}
                                    className="hmi-input w-full mono"
                                    placeholder="500.0"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Reading Override Section */}
                    <div className="space-y-3 pt-5 border-t border-[var(--line)]">
                        <div className="flex items-center gap-2 px-1">
                            <AlertCircle className="w-4 h-4 text-[var(--alarm)]" />
                            <span className="hmi-lbl" style={{ color: 'var(--alarm)' }}>Reading Override (Testing)</span>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <button
                                type="button"
                                onClick={() => overrideMeterReading(meter.meter_id, { value: 0, field: 'consumption', duration_ticks: 10 })}
                                className="hmi-btn alarm"
                            >
                                Zero Cons
                            </button>
                            <button
                                type="button"
                                onClick={() => overrideMeterReading(meter.meter_id, { value: 100, field: 'consumption', duration_ticks: 10 })}
                                className="hmi-btn alarm"
                            >
                                Max Cons
                            </button>
                            <button
                                type="button"
                                onClick={() => updateMeterReading(meter.meter_id, { consumption: 50 })}
                                className="hmi-btn"
                            >
                                Set Cons: 50
                            </button>
                        </div>
                    </div>

                    <div className="sticky bottom-0 -mx-[13px] -mb-[13px] px-[13px] pt-5 pb-[13px] flex gap-4 mt-8 border-t border-[var(--line)] bg-[var(--panel)]">
                        <button
                            type="button"
                            onClick={onClose}
                            className="hmi-btn flex-1"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading || !isDirty}
                            className="hmi-btn primary flex-[2]"
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
        </div>
    );
};

export default EditMeterModal;
