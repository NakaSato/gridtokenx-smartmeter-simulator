-- Extend grid.meter_readings for full simulator replay fidelity.
-- GridTokenX Smart Meter Simulator
-- Adds the reading fields the simulator produces but 002's base schema omits, so
-- a persisted run can be replayed with the same detail the live API exposes
-- (surplus/deficit split, reactive power, power factor, sequence, interval).
-- Idempotent: safe to re-run. Requires 002_postgis_simple.sql first.

SET search_path TO grid, public;

ALTER TABLE grid.meter_readings
    ADD COLUMN IF NOT EXISTS surplus_energy_kwh NUMERIC(12, 6) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS deficit_energy_kwh NUMERIC(12, 6) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS reactive_power_kvar NUMERIC(12, 6),
    ADD COLUMN IF NOT EXISTS power_factor NUMERIC(6, 4),
    ADD COLUMN IF NOT EXISTS voltage_pu NUMERIC(8, 5),
    ADD COLUMN IF NOT EXISTS sequence_number BIGINT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS interval_seconds INTEGER DEFAULT 15;

COMMENT ON COLUMN grid.meter_readings.surplus_energy_kwh IS 'Net export over the interval (kWh)';
COMMENT ON COLUMN grid.meter_readings.deficit_energy_kwh IS 'Net import over the interval (kWh)';
COMMENT ON COLUMN grid.meter_readings.reactive_power_kvar IS 'Reactive power at sample (kVAr)';
COMMENT ON COLUMN grid.meter_readings.power_factor IS 'Power factor at sample (0..1)';
COMMENT ON COLUMN grid.meter_readings.voltage_pu IS 'Bus voltage at meter, per-unit';
COMMENT ON COLUMN grid.meter_readings.sequence_number IS 'Per-meter reading sequence number';
COMMENT ON COLUMN grid.meter_readings.interval_seconds IS 'Integration interval for this reading (s)';
