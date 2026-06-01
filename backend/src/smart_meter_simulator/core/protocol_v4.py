import struct
import zlib
from datetime import datetime
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from ..models.reading import EnergyReading


class ProtocolV4Tags:
    """TLV Tags for Protocol v4 (UTT-S+)."""
    ACTIVE_ENERGY_IMPORT = 0x01  # u64 BE (Watt-hours)
    ACTIVE_ENERGY_EXPORT = 0x02  # u64 BE (Watt-hours)
    L1_VOLTAGE = 0x03           # u32 BE (Centi-volts, 0.01V)
    L1_CURRENT = 0x04           # u32 BE (Milli-amps, 1mA)
    BATTERY_SOC = 0x05          # u32 BE (Basis Points, 0.01%)


class ProtocolV4Encoder:
    """
    Encoder for Protocol v4 (UTT-S+) - Unified Trusted Telemetry - Security Plus.
    """

    VERSION = 0x04

    @staticmethod
    def encode(reading: EnergyReading, device_key: bytes) -> bytes:
        """
        Encodes an EnergyReading into a Protocol v4 binary frame.
        
        Args:
            reading: The EnergyReading to encode.
            device_key: 32-byte AES key for encryption.
            
        Returns:
            bytes: The complete encrypted and signed binary frame.
        """
        # 1. Prepare Plaintext TLV Payload
        tlv_payload = bytearray()
        
        # Tag 0x01: Active Energy Import (u64 BE, Wh)
        val_import = int(reading.energy_consumed * 1000)
        tlv_payload.append(ProtocolV4Tags.ACTIVE_ENERGY_IMPORT)
        tlv_payload.append(8) # Length
        tlv_payload.extend(struct.pack(">Q", val_import))
        
        # Tag 0x02: Active Energy Export (u64 BE, Wh)
        val_export = int(reading.energy_generated * 1000)
        tlv_payload.append(ProtocolV4Tags.ACTIVE_ENERGY_EXPORT)
        tlv_payload.append(8) # Length
        tlv_payload.extend(struct.pack(">Q", val_export))
        
        # Tag 0x03: Voltage (u32 BE, 0.01V)
        if reading.voltage is not None:
            val_v = int(reading.voltage * 100)
            tlv_payload.append(ProtocolV4Tags.L1_VOLTAGE)
            tlv_payload.append(4) # Length
            tlv_payload.extend(struct.pack(">I", val_v))
            
        # Tag 0x04: Current (u32 BE, 1mA)
        if reading.current is not None:
            val_i = int(reading.current * 1000)
            tlv_payload.append(ProtocolV4Tags.L1_CURRENT)
            tlv_payload.append(4) # Length
            tlv_payload.extend(struct.pack(">I", val_i))
            
        # Tag 0x05: Battery SoC (u32 BE, 0.01%)
        val_soc = int(reading.battery_level * 100)
        tlv_payload.append(ProtocolV4Tags.BATTERY_SOC)
        tlv_payload.append(4) # Length
        tlv_payload.extend(struct.pack(">I", val_soc))

        # 2. Construct Header (21 bytes)
        manuf_id = reading.manufacturer_id[:3].encode("ascii").ljust(3, b"\0")
        ldn = reading.logical_device_name[:8].encode("ascii").ljust(8, b"\0")
        timestamp = int(reading.timestamp.timestamp())
        
        # Initial header without length
        header_base = struct.pack(">B", ProtocolV4Encoder.VERSION)
        header_middle = manuf_id + ldn + struct.pack(">Q", timestamp)
        
        # 3. Encryption (AES-256-GCM)
        nonce = manuf_id + struct.pack(">Q", timestamp) + struct.pack(">B", ProtocolV4Encoder.VERSION)
        
        aesgcm = AESGCM(device_key)
        
        # Calculate ciphertext length first to know total_len
        ciphertext_with_tag = aesgcm.encrypt(nonce, bytes(tlv_payload), b"") # Temporary AAD
        
        # total_len = bytes following the Length field
        # = Manuf(3) + LDN(8) + TS(8) + CiphertextWithTag(len) + CRC(4)
        total_len = 19 + len(ciphertext_with_tag) + 4
        
        header = struct.pack(">BB", ProtocolV4Encoder.VERSION, total_len) + header_middle
        
        # Re-encrypt with correct AAD (the header)
        ciphertext_with_tag = aesgcm.encrypt(nonce, bytes(tlv_payload), header)
        
        frame = header + ciphertext_with_tag
        
        # 5. CRC-32
        checksum = zlib.crc32(frame) & 0xFFFFFFFF
        frame += struct.pack(">I", checksum)
        
        # Verification: frame length MUST be total_len + 2
        # if len(frame) != total_len + 2:
        #    raise ValueError(f"Length mismatch: {len(frame)} != {total_len} + 2")
        
        return bytes(frame)


class ProtocolV4Decoder:
    """
    Decoder for Protocol v4 (UTT-S+).
    """
    
    @staticmethod
    def decode(frame: bytes, device_key: bytes) -> Dict[str, Any]:
        """
        Decodes a Protocol v4 binary frame.
        
        Args:
            frame: The raw binary frame.
            device_key: 32-byte AES key for decryption.
            
        Returns:
            Dict[str, Any]: Decoded metrics and metadata.
        """
        if len(frame) < 25: # Min header(21) + Tag(16) + CRC(4) is more than 25, actually 21+16+4 = 41 if empty payload
            # Actually payload can be empty? Spec says TLV Dictionary. 
            # Min frame with one 1-byte payload: 21 + 1 + 16 + 4 = 42
            # Let's just check length against Total Length field.
            raise ValueError("Frame too short")
            
        # 1. Check CRC-32
        received_checksum = struct.unpack(">I", frame[-4:])[0]
        calculated_checksum = zlib.crc32(frame[:-4]) & 0xFFFFFFFF
        if received_checksum != calculated_checksum:
            raise ValueError("CRC-32 mismatch")
            
        # 2. Parse Header
        version = frame[0]
        if version != 0x04:
            raise ValueError(f"Unsupported protocol version: {version}")
            
        total_len = frame[1]
        if len(frame) != total_len + 2:
            raise ValueError(f"Frame length mismatch: expected {total_len + 2}, got {len(frame)}")
            
        manuf_id = frame[2:5].decode("ascii").strip("\0")
        ldn = frame[5:13].decode("ascii").strip("\0")
        timestamp_raw = struct.unpack(">Q", frame[13:21])[0]
        timestamp = datetime.fromtimestamp(timestamp_raw)
        
        # 3. Decryption
        header = frame[0:21]
        ciphertext_with_tag = frame[21:-4]
        
        # Nonce: [Manuf ID (3b)] + [Timestamp (8b)] + [Version (1b)]
        nonce = frame[2:5] + frame[13:21] + frame[0:1]
        
        aesgcm = AESGCM(device_key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, header)
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
            
        # 4. Parse TLV Payload
        metrics = {
            "manufacturer_id": manuf_id,
            "logical_device_name": ldn,
            "timestamp": timestamp
        }
        
        i = 0
        while i < len(plaintext):
            tag = plaintext[i]
            length = plaintext[i+1]
            i += 2
            
            value_bytes = plaintext[i:i+length]
            
            if tag == ProtocolV4Tags.ACTIVE_ENERGY_IMPORT:
                metrics["energy_consumed"] = struct.unpack(">Q", value_bytes)[0] / 1000.0
            elif tag == ProtocolV4Tags.ACTIVE_ENERGY_EXPORT:
                metrics["energy_generated"] = struct.unpack(">Q", value_bytes)[0] / 1000.0
            elif tag == ProtocolV4Tags.L1_VOLTAGE:
                metrics["voltage"] = struct.unpack(">I", value_bytes)[0] / 100.0
            elif tag == ProtocolV4Tags.L1_CURRENT:
                metrics["current"] = struct.unpack(">I", value_bytes)[0] / 1000.0
            elif tag == ProtocolV4Tags.BATTERY_SOC:
                metrics["battery_level"] = struct.unpack(">I", value_bytes)[0] / 100.0
            else:
                # Unknown tag, skip it using the length field
                pass
                
            i += length
                
        return metrics
