// Shared ISA-101 HMI derivations for MeterCard / MeterListItem.
// In-band electrical values stay neutral; color appears only on deviation.

import type { Reading } from '@/lib/types';

export type Flag = '' | 'warn' | 'alarm';

/** Voltage (pu): warn ±3%, alarm ±5% of nominal 1.0 pu. */
export function flagV(v: number): Flag {
    if (v < 0.95 || v > 1.05) return 'alarm';
    if (v < 0.97 || v > 1.03) return 'warn';
    return '';
}

/** Frequency (Hz): warn >0.1 Hz, alarm >0.2 Hz off 50 Hz. */
export function flagF(f: number): Flag {
    const d = Math.abs(f - 50);
    if (d > 0.2) return 'alarm';
    if (d > 0.1) return 'warn';
    return '';
}

/** Power factor (cosφ): warn <0.95, alarm <0.90. */
export function flagPF(p: number): Flag {
    if (p < 0.9) return 'alarm';
    if (p < 0.95) return 'warn';
    return '';
}

// Fallback grid carbon intensity (kgCO2/kWh) for readings that arrive without a
// server-computed carbon_offset. Mirrors the backend CARBON_GRID_INTENSITY default
// (config/settings.py) so a derived estimate matches the authoritative figure.
const GRID_CARBON_INTENSITY_FALLBACK = 0.4999;

const RANK: Flag[] = ['', 'warn', 'alarm'];
export function worst(...flags: Flag[]): Flag {
    return RANK[Math.max(...flags.map((x) => RANK.indexOf(x)))];
}

export interface MeterView {
    id: string;
    sub: string;
    typeLabel: string;
    isSolar: boolean;
    isBattery: boolean;
    isEV: boolean;
    /** Battery dispatch in kW: >0 discharging, <0 charging. */
    dispatchKw: number;
    /** EV charger draw in kW. */
    evLoadKw: number;
    gen: number;
    con: number;
    net: number;
    isExport: boolean;
    roleSub: string;
    soc: number;
    co2: number;
    v: number;
    f: number;
    pf: number;
    amb: number;
    fv: Flag;
    ff: Flag;
    fp: Flag;
    live: boolean;
    compromised: boolean;
    shed: boolean;
    abnormal: boolean;
    /** Net-flow bar fill 0–50 (% of half-track) against ±8 kW scale. */
    barPct: number;
    barScale: number;
}

const BAR_SCALE = 8; // ±kW full-scale for the net-flow bar

export function deriveMeter(reading: Reading): MeterView {
    const gen = reading.generation_kw ?? reading.energy_generated ?? 0;
    const con = reading.consumption_kw ?? reading.energy_consumed ?? 0;
    const net = +(gen - con).toFixed(2);

    const v = reading.voltage_pu ?? 1.0;
    const f = reading.freq_hz ?? reading.frequency ?? 50.0;
    const pf = reading.power_factor ?? 0.98;

    const fv = flagV(v);
    const ff = flagF(f);
    const fp = flagPF(pf);

    const compromised = Boolean(reading.is_compromised || (reading.norm_residual ?? 0) > 4.0);
    const shed = Boolean(reading.is_shed);
    const live = !shed;

    const isBattery =
        Boolean(reading.has_battery) ||
        reading.battery_soc_pct != null ||
        /bess|battery|storage/i.test(reading.meter_type || '');
    const isEV =
        Boolean(reading.has_ev_charger) ||
        reading.ev_charge_kw != null ||
        /ev[_ ]?charger|charging|fast_charger/i.test(reading.meter_type || '');

    const isSolar =
        !isBattery &&
        !isEV &&
        (Boolean(reading.has_solar) ||
            gen > 0 ||
            /solar|prosumer/i.test(reading.meter_type || ''));

    const co2 = reading.carbon_offset ?? (reading.energy_generated || 0) * GRID_CARBON_INTENSITY_FALLBACK;
    const isExport = net >= 0;
    const dispatchKw = reading.battery_dispatch_kw ?? 0;
    const socPct = reading.battery_soc_pct ?? reading.battery_level ?? 0;
    const evLoadKw = reading.ev_charge_kw ?? 0;

    // Storage/EV roles take precedence over the generic solar/grid label.
    const roleSub = isBattery
        ? dispatchKw > 0.001
            ? 'Discharging (reserve)'
            : dispatchKw < -0.001
                ? 'Charging'
                : 'Idle (holding SoC)'
        : isEV
            ? evLoadKw > 0.001
                ? 'Charging vehicles'
                : 'Idle'
            : isSolar
                ? (isExport ? 'Trading active' : 'Self-consuming')
                : 'Grid-fed';

    return {
        id: reading.location_name || reading.meter_id,
        sub: reading.location || reading.meter_id,
        typeLabel: (reading.meter_type || (isSolar ? 'Solar prosumer' : 'Grid consumer')).replace(/_/g, ' '),
        isSolar,
        isBattery,
        isEV,
        dispatchKw,
        evLoadKw,
        gen,
        con,
        net,
        isExport,
        roleSub,
        soc: socPct,
        co2,
        v,
        f,
        pf,
        amb: reading.temperature ?? 20.0,
        fv,
        ff,
        fp,
        live,
        compromised,
        shed,
        abnormal: worst(fv, ff, fp) !== '' || !live || compromised,
        barPct: Math.min((Math.abs(net) / BAR_SCALE) * 50, 50),
        barScale: BAR_SCALE,
    };
}
