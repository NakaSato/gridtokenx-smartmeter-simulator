"""
DLMS/COSEM (IEC 62056) Encoder for Energy Readings.
Translates high-level EnergyReading models into compact binary/hex payloads
using OBIS codes and AXDR encoding principles.
"""

import binascii
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..models.reading import EnergyReading

class ObisCode:
    """Standard OBIS (Object Identification System) codes."""
    ACTIVE_ENERGY_IMPORT = "1.0.1.8.0"   # +A Total
    ACTIVE_ENERGY_EXPORT = "1.0.2.8.0"   # -A Total
    VOLTAGE_L1 = "1.0.32.7.0"           # Voltage Phase 1
    CURRENT_L1 = "1.0.31.7.0"           # Current Phase 1
    REACTIVE_ENERGY_IMPORT = "1.0.3.8.0" # +Q Total
    FREQUENCY = "1.0.14.7.0"            # Frequency
    BATTERY_SOC = "0.0.96.6.3"          # Custom/Extended SOC

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
        system_title = reading.manufacturer_id[:3].encode() + reading.logical_device_name[:8].encode().ljust(8, b"\0")
        
        payload = bytearray(system_title)
        
        # 2. Add Timestamp (8 bytes - Octet String format)
        ts = int(reading.timestamp.timestamp())
        payload.extend(ts.to_bytes(8, byteorder='big'))

        # 3. Add OBIS-coded values
        # Format for each entry: [OBIS_INDEX (1 byte)][VALUE (4-8 bytes)]
        
        # Import Energy (+A)
        # Map: 1 -> ACTIVE_ENERGY_IMPORT
        val_import = int(reading.energy_consumed * 1000) # Wh
        payload.append(1)
        payload.extend(val_import.to_bytes(8, byteorder='big'))
        
        # Export Energy (-A)
        # Map: 2 -> ACTIVE_ENERGY_EXPORT
        val_export = int(reading.energy_generated * 1000) # Wh
        payload.append(2)
        payload.extend(val_export.to_bytes(8, byteorder='big'))
        
        # Voltage
        if reading.voltage is not None:
            # Map: 3 -> VOLTAGE_L1
            val_v = int(reading.voltage * 100) # cV
            payload.append(3)
            payload.extend(val_v.to_bytes(4, byteorder='big'))
            
        # Current
        if reading.current is not None:
            # Map: 4 -> CURRENT_L1
            val_i = int(reading.current * 1000) # mA
            payload.append(4)
            payload.extend(val_i.to_bytes(4, byteorder='big'))

        # Battery SOC
        # Map: 5 -> BATTERY_SOC
        val_soc = int(reading.battery_level * 100) # Basis points
        payload.append(5)
        payload.extend(val_soc.to_bytes(4, byteorder='big'))

        return bytes(payload)

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
            5: ObisCode.BATTERY_SOC
        }
