"""
DLMS/COSEM (IEC 62056) Encoder for Energy Readings.
Translates high-level EnergyReading models into compact binary/hex payloads
using OBIS codes and AXDR encoding principles.
"""

import binascii
from enum import Enum
from typing import Dict, Any, List, Optional
from ..models.reading import EnergyReading


class DlmsUnit(int, Enum):
    W = 27
    VAR = 29
    WH = 30
    A = 33
    V = 35
    HZ = 44
    UNITLESS = 255


class ObisCode:
    """Standard OBIS (Object Identification System) codes."""

    ACTIVE_POWER_IMPORT = "1.0.1.7.0.255"  # +P (kW/W)
    ACTIVE_POWER_EXPORT = "1.0.2.7.0.255"  # -P (kW/W)
    REACTIVE_POWER_IMPORT = "1.0.3.7.0.255"  # +Q (kvar/var)
    REACTIVE_POWER_EXPORT = "1.0.4.7.0.255"  # -Q (kvar/var)
    CURRENT_L1 = "1.0.31.7.0.255"  # Phase 1 Current (A)
    CURRENT_L2 = "1.0.51.7.0.255"  # Phase 2 Current (A)
    CURRENT_L3 = "1.0.71.7.0.255"  # Phase 3 Current (A)
    VOLTAGE_L1 = "1.0.32.7.0.255"  # Phase 1 Voltage (V)
    VOLTAGE_L2 = "1.0.52.7.0.255"  # Phase 2 Voltage (V)
    VOLTAGE_L3 = "1.0.72.7.0.255"  # Phase 3 Voltage (V)
    FREQUENCY = "1.0.14.7.0.255"  # Frequency (Hz)
    POWER_FACTOR = "1.0.13.7.0.255"  # Power Factor
    BATTERY_SOC = "0.0.96.6.3.255"  # Custom/Extended SOC
    CLOCK = "0.0.1.0.0.255"  # Clock object

    # Retained for legacy/energy calculations
    ACTIVE_ENERGY_IMPORT = "1.0.1.8.0.255"  # +A Total
    ACTIVE_ENERGY_EXPORT = "1.0.2.8.0.255"  # -A Total
    REACTIVE_ENERGY_IMPORT = "1.0.3.8.0.255"  # +Q Total


class IC1Data:
    @staticmethod
    def encode(logical_name: str, value: Any) -> Dict[str, Any]:
        return {"class_id": 1, "logical_name": logical_name, "value": value}


class IC3Register:
    @staticmethod
    def encode(logical_name: str, value: Any, scaler: int, unit: int) -> Dict[str, Any]:
        return {
            "class_id": 3,
            "logical_name": logical_name,
            "value": value,
            "scaler_unit": {"scaler": scaler, "unit": unit},
        }


class IC4ExtendedRegister:
    @staticmethod
    def encode(
        logical_name: str,
        value: Any,
        scaler: int,
        unit: int,
        capture_time: str,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "class_id": 4,
            "logical_name": logical_name,
            "value": value,
            "scaler_unit": {"scaler": scaler, "unit": unit},
            "status": status,
            "capture_time": capture_time,
        }


class IC8Clock:
    @staticmethod
    def encode(
        logical_name: str, time: str, time_zone: int = 0, status: str = "ok"
    ) -> Dict[str, Any]:
        return {
            "class_id": 8,
            "logical_name": logical_name,
            "time": time,
            "time_zone": time_zone,
            "status": status,
        }


class IC7ProfileGeneric:
    @staticmethod
    def encode(
        logical_name: str,
        buffer: List[Any],
        capture_objects: List[Dict[str, Any]],
        capture_period: int,
    ) -> Dict[str, Any]:
        return {
            "class_id": 7,
            "logical_name": logical_name,
            "buffer": buffer,
            "capture_objects": capture_objects,
            "capture_period": capture_period,
        }


class DlmsEncoder:
    """
    Encoder to transform EnergyReading into a hex-encoded DLMS/COSEM frame.
    Note: This is a simplified AXDR-like encoding for industrial simulation.
    """

    @staticmethod
    def encode_reading(reading: EnergyReading) -> bytes:
        """
        Encodes an EnergyReading into a binary DLMS-like payload.
        Format: [Header][OBIS:Value][OBIS:Value]...[CRC/Checksum]
        """
        # 1. Header (Manufacturer ID + Logical Device Name)
        # Manufacturer ID (3 bytes) + LDN (padded to 8 bytes)
        system_title = reading.manufacturer_id[
            :3
        ].encode() + reading.logical_device_name[:8].encode().ljust(8, b"\0")

        payload = bytearray(system_title)

        # 2. Add Timestamp (8 bytes - Octet String format)
        ts = int(reading.timestamp.timestamp())
        payload.extend(ts.to_bytes(8, byteorder="big"))

        # 3. Add OBIS-coded values
        # Format for each entry: [OBIS_INDEX (1 byte)][VALUE (4-8 bytes)]

        # Import Energy (+A)
        # Map: 1 -> ACTIVE_ENERGY_IMPORT
        val_import = int(reading.energy_consumed * 1000)  # Wh
        payload.append(1)
        payload.extend(val_import.to_bytes(8, byteorder="big"))

        # Export Energy (-A)
        # Map: 2 -> ACTIVE_ENERGY_EXPORT
        val_export = int(reading.energy_generated * 1000)  # Wh
        payload.append(2)
        payload.extend(val_export.to_bytes(8, byteorder="big"))

        # Voltage
        if reading.voltage is not None:
            # Map: 3 -> VOLTAGE_L1
            val_v = int(reading.voltage * 100)  # cV
            payload.append(3)
            payload.extend(val_v.to_bytes(4, byteorder="big"))

        # Current
        if reading.current is not None:
            # Map: 4 -> CURRENT_L1
            val_i = int(reading.current * 1000)  # mA
            payload.append(4)
            payload.extend(val_i.to_bytes(4, byteorder="big"))

        # Battery SOC
        # Map: 5 -> BATTERY_SOC
        val_soc = int(reading.battery_level * 100)  # Basis points
        payload.append(5)
        payload.extend(val_soc.to_bytes(4, byteorder="big"))

        # Active Power
        hours = reading.interval_seconds / 3600.0
        power_gen = reading.energy_generated / hours if hours > 0 else 0.0
        power_cons = reading.energy_consumed / hours if hours > 0 else 0.0

        # Map: 6 -> ACTIVE_POWER_IMPORT
        val_p_imp = int(power_cons * 1000)  # W
        payload.append(6)
        payload.extend(val_p_imp.to_bytes(4, byteorder="big"))

        # Map: 7 -> ACTIVE_POWER_EXPORT
        val_p_exp = int(power_gen * 1000)  # W
        payload.append(7)
        payload.extend(val_p_exp.to_bytes(4, byteorder="big"))

        if reading.reactive_power_kvar is not None:
            # Map: 8 -> REACTIVE_POWER_IMPORT or Map: 9 -> REACTIVE_POWER_EXPORT
            val_q = int(abs(reading.reactive_power_kvar) * 1000)  # var
            if reading.reactive_power_kvar > 0:
                payload.append(8)
            else:
                payload.append(9)
            payload.extend(val_q.to_bytes(4, byteorder="big"))

        if reading.frequency is not None:
            # Map: 10 -> FREQUENCY
            val_f = int(reading.frequency * 1000)  # mHz
            payload.append(10)
            payload.extend(val_f.to_bytes(4, byteorder="big"))

        if reading.power_factor is not None:
            # Map: 11 -> POWER_FACTOR
            val_pf = int(reading.power_factor * 1000)  # per mille
            payload.append(11)
            payload.extend(val_pf.to_bytes(4, byteorder="big"))

        return bytes(payload)

    @staticmethod
    def encode_reading_to_obis_json(reading: EnergyReading) -> Dict[str, Any]:
        """
        Encodes an EnergyReading into a JSON dictionary structured via DLMS Interface Classes.
        """
        hours = reading.interval_seconds / 3600.0
        power_gen = reading.energy_generated / hours if hours > 0 else 0.0
        power_cons = reading.energy_consumed / hours if hours > 0 else 0.0

        ts_str = reading.timestamp.isoformat()

        payload = {
            ObisCode.CLOCK: IC8Clock.encode(ObisCode.CLOCK, ts_str),
            ObisCode.ACTIVE_ENERGY_IMPORT: IC4ExtendedRegister.encode(
                ObisCode.ACTIVE_ENERGY_IMPORT,
                int(reading.energy_consumed * 1000),
                0,
                DlmsUnit.WH.value,
                ts_str,
            ),
            ObisCode.ACTIVE_ENERGY_EXPORT: IC4ExtendedRegister.encode(
                ObisCode.ACTIVE_ENERGY_EXPORT,
                int(reading.energy_generated * 1000),
                0,
                DlmsUnit.WH.value,
                ts_str,
            ),
            ObisCode.ACTIVE_POWER_IMPORT: IC3Register.encode(
                ObisCode.ACTIVE_POWER_IMPORT,
                int(power_cons * 1000),
                0,
                DlmsUnit.W.value,
            ),
            ObisCode.ACTIVE_POWER_EXPORT: IC3Register.encode(
                ObisCode.ACTIVE_POWER_EXPORT, int(power_gen * 1000), 0, DlmsUnit.W.value
            ),
        }

        if reading.voltage is not None:
            val_v = int(round(reading.voltage, 1) * 10)
            payload[ObisCode.VOLTAGE_L1] = IC3Register.encode(
                ObisCode.VOLTAGE_L1, val_v, -1, DlmsUnit.V.value
            )

        if reading.current is not None:
            val_i = int(round(reading.current, 1) * 10)
            payload[ObisCode.CURRENT_L1] = IC3Register.encode(
                ObisCode.CURRENT_L1, val_i, -1, DlmsUnit.A.value
            )

        if reading.reactive_power_kvar is not None:
            val_var = int(abs(reading.reactive_power_kvar) * 1000)
            if reading.reactive_power_kvar > 0:
                payload[ObisCode.REACTIVE_POWER_IMPORT] = IC3Register.encode(
                    ObisCode.REACTIVE_POWER_IMPORT, val_var, 0, DlmsUnit.VAR.value
                )
            else:
                payload[ObisCode.REACTIVE_POWER_EXPORT] = IC3Register.encode(
                    ObisCode.REACTIVE_POWER_EXPORT, val_var, 0, DlmsUnit.VAR.value
                )

        if reading.frequency is not None:
            val_hz = int(round(reading.frequency, 2) * 100)
            payload[ObisCode.FREQUENCY] = IC3Register.encode(
                ObisCode.FREQUENCY, val_hz, -2, DlmsUnit.HZ.value
            )

        if reading.power_factor is not None:
            val_pf = int(round(reading.power_factor, 2) * 100)
            payload[ObisCode.POWER_FACTOR] = IC3Register.encode(
                ObisCode.POWER_FACTOR, val_pf, -2, DlmsUnit.UNITLESS.value
            )

        val_soc = int(round(reading.battery_level, 1) * 10)
        payload[ObisCode.BATTERY_SOC] = IC3Register.encode(
            ObisCode.BATTERY_SOC, val_soc, -1, DlmsUnit.UNITLESS.value
        )

        # Add fallback fields for signature verification
        payload["kwh"] = float(f"{max(0.0, reading.surplus_energy):.6f}")
        payload["timestamp"] = ts_str
        if reading.meter_signature:
            payload["signature"] = reading.meter_signature

        return payload

    @staticmethod
    def to_hex(binary_payload: bytes) -> str:
        """Helper to convert to hex string for easier debugging/MQTT transport."""
        return binascii.hexlify(binary_payload).decode()

    @staticmethod
    def get_obis_map() -> Dict[int, str]:
        """Provides mapping for the decoder on the other side."""
        return {
            1: ObisCode.ACTIVE_ENERGY_IMPORT,
            2: ObisCode.ACTIVE_ENERGY_EXPORT,
            3: ObisCode.VOLTAGE_L1,
            4: ObisCode.CURRENT_L1,
            5: ObisCode.BATTERY_SOC,
        }
