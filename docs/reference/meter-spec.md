# Meter Specifications

The **Smart Meter Model** in the GridTokenX simulator is designed to be a high-fidelity representation of a physical AMI (Advanced Metering Infrastructure) device. It supports professional industrial standards, including **DLMS/COSEM** (IEC 62056) and **ANSI C12.20**.

## 📊 Data Model

Every `SmartMeter` generates an `EnergyReading` object during each simulation tick. The following fields are captured:

### 1. Energy Metrics (kWh)
-   **`energy_generated`**: Total solar energy produced in the interval.
-   **`energy_consumed`**: Total energy consumed by the building/load.
-   **`surplus_energy`**: Net energy exported to the grid (Generation > Consumption).
-   **`deficit_energy`**: Net energy imported from the grid (Consumption > Generation).

### 2. Electrical Parameters
-   **Voltage (`v`)**: Measured in Volts (RMS). Supports per-unit (pu) normalization for grid analysis.
-   **Current (`i`)**: Measured in Amperes (RMS).
-   **Active Power (`p`)**: Measured in kW.
-   **Reactive Power (`q`)**: Measured in kVar.
-   **Frequency (`f`)**: System frequency in Hz (Nominal 50.0 Hz).
-   **Power Factor**: Ratio of active to apparent power (0.0 - 1.0).

### 3. Battery & DER State
-   **`battery_level`**: Current State-of-Charge (SoC) as a percentage (0-100%).
-   **`temperature`**: Internal device temperature in Celsius.

## 🔒 Industrial Features & Security

### DLMS/COSEM (IEC 62056)
The simulator includes a `DlmsEncoder` that translates internal Python objects into OBIS-coded binary telegrams. This allows for direct integration with industrial head-end systems (HES).

### Cryptographic Signing
All readings are signed using **Ed25519** digital signatures.
-   **Private Key**: Stored securely within the `SmartMeter` instance.
-   **Public Key**: Registered with the GridTokenX Oracle Bridge for verification.
-   **Payload Integrity**: The `meter_signature` field protects against False Data Injection (FDI) attacks.

## 🔗 Grid & Blockchain Integration

-   **Location**: Geospatial coordinates (Lat/Lon) assigned via PostGIS.
-   **Wallet Address**: Each meter is linked to a **Solana** wallet for real-time GTNX token minting based on `surplus_energy`.
-   **Accuracy Class**: Supports Class 0.2, 0.5, and 1.0 as per industrial standards, which dictates the Gaussian noise applied to measurements.

---
_Next: [Pandapower Implementation](pandapower.md)_
