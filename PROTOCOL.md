# OBIS Code Reference — IEC 62056

> **Document type:** Technical reference / specification
> **Subject:** OBIS (OBject Identification System) code for the IEC 62056 standard protocol
> **Normative source:** IEC 62056-6-1:2023 (Edition 4.0) — OBIS object identification system

---

## 1. Overview

The **OBIS code** identifies a device value. It is a text string composed according to the OBIS standard (see **IEC 62056-61**). The OBIS code appears at the beginning of each row of a meter readout string.

An older, simpler variant is the **EDIS code**, which (for example) does not cover groups **A** and **B**.

In the PROMOTIC system this code is used by the `PmIEC62056` communication driver. After receiving a *Readout — Values readout* message, the driver stores the readout text into the `ResultList` variable, with the OBIS value code at the start of each row.

---

## 2. Code Structure

The code consists of up to **6 group sub-identifiers**, labelled **A** through **F**. Any of them may be omitted (groups **A** and **B** are frequently dropped). Groups are delimited by unique separators so the parser can determine which group each sub-identifier belongs to:

```
A-B:C.D.E*F
```

| Group | Meaning |
| ----- | ------- |
| **A** | Medium — `0` = abstract objects, `1` = electricity, `6` = heat, `7` = gas, `8` = water, … |
| **B** | Channel — separates measurement results from devices with multiple channels |
| **C** | Physical value — current, voltage, energy, level, temperature, … |
| **D** | Quantity / computation result of a specific algorithm |
| **E** | Measurement type — subdivides the value defined by A–D (e.g. tariff/switching ranges) |
| **F** | Billing-period separator — typically used to identify individual time ranges |

> **Note on sign convention:** "Positive" (A+) and "Negative" (A−) are defined relative to a chosen reference direction set in the meter configuration (CT orientation, parameterization). For a prosumer with rooftop PV, **import = A+** and **export = A−**. State the assumed reference direction explicitly in any downstream specification rather than treating a register as universally "import" or "export."

---

## 3. Register Reference Tables

### 3.1 Active Energy Registers

| OBIS code | Description |
| --------- | ----------- |
| `1.8.0` | Positive active energy (A+) total [kWh] |
| `1.8.1` | Positive active energy (A+) in tariff T1 [kWh] |
| `1.8.2` | Positive active energy (A+) in tariff T2 [kWh] |
| `1.8.3` | Positive active energy (A+) in tariff T3 [kWh] |
| `1.8.4` | Positive active energy (A+) in tariff T4 [kWh] |
| `2.8.0` | Negative active energy (A−) total [kWh] |
| `2.8.1` | Negative active energy (A−) in tariff T1 [kWh] |
| `2.8.2` | Negative active energy (A−) in tariff T2 [kWh] |
| `2.8.3` | Negative active energy (A−) in tariff T3 [kWh] |
| `2.8.4` | Negative active energy (A−) in tariff T4 [kWh] |
| `15.8.0` | Absolute active energy (\|A\|) total [kWh] |
| `15.8.1` | Absolute active energy (\|A\|) in tariff T1 [kWh] |
| `15.8.2` | Absolute active energy (\|A\|) in tariff T2 [kWh] |
| `15.8.3` | Absolute active energy (\|A\|) in tariff T3 [kWh] |
| `15.8.4` | Absolute active energy (\|A\|) in tariff T4 [kWh] |
| `16.8.0` | Sum active energy without reverse blockade (A+ − A−) total [kWh] |
| `16.8.1` | Sum active energy without reverse blockade (A+ − A−) in tariff T1 [kWh] |
| `16.8.2` | Sum active energy without reverse blockade (A+ − A−) in tariff T2 [kWh] |
| `16.8.3` | Sum active energy without reverse blockade (A+ − A−) in tariff T3 [kWh] |
| `16.8.4` | Sum active energy without reverse blockade (A+ − A−) in tariff T4 [kWh] |

> **Source note:** The vendor table labels the `2.8.x` rows "Negative active energy **(A+)**", which is internally inconsistent — the symbol should be **A−**. Corrected to A− above. The vendor row originally written `16.8.` is corrected to `16.8.1`.

### 3.2 Reactive Energy Registers

| OBIS code | Description |
| --------- | ----------- |
| `3.8.0` | Positive reactive energy (Q+) total [kvarh] |
| `3.8.1` | Positive reactive energy (Q+) in tariff T1 [kvarh] |
| `3.8.2` | Positive reactive energy (Q+) in tariff T2 [kvarh] |
| `3.8.3` | Positive reactive energy (Q+) in tariff T3 [kvarh] |
| `3.8.4` | Positive reactive energy (Q+) in tariff T4 [kvarh] |
| `4.8.0` | Negative reactive energy (Q−) total [kvarh] |
| `4.8.1` | Negative reactive energy (Q−) in tariff T1 [kvarh] |
| `4.8.2` | Negative reactive energy (Q−) in tariff T2 [kvarh] |
| `4.8.3` | Negative reactive energy (Q−) in tariff T3 [kvarh] |
| `4.8.4` | Negative reactive energy (Q−) in tariff T4 [kvarh] |
| `5.8.0` | Imported inductive reactive energy in 1st quadrant (Q1) total [kvarh] |
| `5.8.1` | Imported inductive reactive energy in 1st quadrant (Q1) in tariff T1 [kvarh] |
| `5.8.2` | Imported inductive reactive energy in 1st quadrant (Q1) in tariff T2 [kvarh] |
| `5.8.3` | Imported inductive reactive energy in 1st quadrant (Q1) in tariff T3 [kvarh] |
| `5.8.4` | Imported inductive reactive energy in 1st quadrant (Q1) in tariff T4 [kvarh] |
| `6.8.0` | Imported capacitive reactive energy in 2nd quadrant (Q2) total [kvarh] |
| `6.8.1` | Imported capacitive reactive energy in 2nd quadrant (Q2) in tariff T1 [kvarh] |
| `6.8.2` | Imported capacitive reactive energy in 2nd quadrant (Q2) in tariff T2 [kvarh] |
| `6.8.3` | Imported capacitive reactive energy in 2nd quadrant (Q2) in tariff T3 [kvarh] |
| `6.8.4` | Imported capacitive reactive energy in 2nd quadrant (Q2) in tariff T4 [kvarh] |
| `7.8.0` | Exported inductive reactive energy in 3rd quadrant (Q3) total [kvarh] |
| `7.8.1` | Exported inductive reactive energy in 3rd quadrant (Q3) in tariff T1 [kvarh] |
| `7.8.2` | Exported inductive reactive energy in 3rd quadrant (Q3) in tariff T2 [kvarh] |
| `7.8.3` | Exported inductive reactive energy in 3rd quadrant (Q3) in tariff T3 [kvarh] |
| `7.8.4` | Exported inductive reactive energy in 3rd quadrant (Q3) in tariff T4 [kvarh] |
| `8.8.0` | Exported capacitive reactive energy in 4th quadrant (Q4) total [kvarh] |
| `8.8.1` | Exported capacitive reactive energy in 4th quadrant (Q4) in tariff T1 [kvarh] |
| `8.8.2` | Exported capacitive reactive energy in 4th quadrant (Q4) in tariff T2 [kvarh] |
| `8.8.3` | Exported capacitive reactive energy in 4th quadrant (Q4) in tariff T3 [kvarh] |
| `8.8.4` | Exported capacitive reactive energy in 4th quadrant (Q4) in tariff T4 [kvarh] |

### 3.3 Apparent Energy Registers

| OBIS code | Description |
| --------- | ----------- |
| `9.8.0` | Apparent energy (S+) total [kVAh] |
| `9.8.1` | Apparent energy (S+) in tariff T1 [kVAh] |
| `9.8.2` | Apparent energy (S+) in tariff T2 [kVAh] |
| `9.8.3` | Apparent energy (S+) in tariff T3 [kVAh] |
| `9.8.4` | Apparent energy (S+) in tariff T4 [kVAh] |

### 3.4 Active Energy per Phase

| OBIS code | Description |
| --------- | ----------- |
| `21.8.0` | Positive active energy (A+) in phase L1 total [kWh] |
| `41.8.0` | Positive active energy (A+) in phase L2 total [kWh] |
| `61.8.0` | Positive active energy (A+) in phase L3 total [kWh] |
| `22.8.0` | Negative active energy (A−) in phase L1 total [kWh] |
| `42.8.0` | Negative active energy (A−) in phase L2 total [kWh] |
| `62.8.0` | Negative active energy (A−) in phase L3 total [kWh] |
| `35.8.0` | Absolute active energy (\|A\|) in phase L1 total [kWh] |
| `55.8.0` | Absolute active energy (\|A\|) in phase L2 total [kWh] |
| `75.8.0` | Absolute active energy (\|A\|) in phase L3 total [kWh] |

### 3.5 Maximum Demand Registers

| OBIS code | Description |
| --------- | ----------- |
| `1.6.0` | Positive active maximum demand (A+) total [kW] |
| `1.6.1` | Positive active maximum demand (A+) in tariff T1 [kW] |
| `1.6.2` | Positive active maximum demand (A+) in tariff T2 [kW] |
| `1.6.3` | Positive active maximum demand (A+) in tariff T3 [kW] |
| `1.6.4` | Positive active maximum demand (A+) in tariff T4 [kW] |
| `2.6.0` | Negative active maximum demand (A−) total [kW] |
| `2.6.1` | Negative active maximum demand (A−) in tariff T1 [kW] |
| `2.6.2` | Negative active maximum demand (A−) in tariff T2 [kW] |
| `2.6.3` | Negative active maximum demand (A−) in tariff T3 [kW] |
| `2.6.4` | Negative active maximum demand (A−) in tariff T4 [kW] |
| `15.6.0` | Absolute active maximum demand (\|A\|) total [kW] |
| `15.6.1` | Absolute active maximum demand (\|A\|) in tariff T1 [kW] |
| `15.6.2` | Absolute active maximum demand (\|A\|) in tariff T2 [kW] |
| `15.6.3` | Absolute active maximum demand (\|A\|) in tariff T3 [kW] |
| `15.6.4` | Absolute active maximum demand (\|A\|) in tariff T4 [kW] |
| `3.6.0` | Positive reactive maximum demand (Q+) total [kvar] |
| `4.6.0` | Negative reactive maximum demand (Q−) total [kvar] |
| `5.6.0` | Reactive maximum demand in Q1 total [kvar] |
| `6.6.0` | Reactive maximum demand in Q2 total [kvar] |
| `7.6.0` | Reactive maximum demand in Q3 total [kvar] |
| `8.6.0` | Reactive maximum demand in Q4 total [kvar] |
| `9.6.0` | Apparent maximum demand (S+) total [kVA] |

### 3.6 Cumulative Maximum Demand Registers

| OBIS code | Description |
| --------- | ----------- |
| `1.2.0` | Positive active cumulative maximum demand (A+) total [kW] |
| `1.2.1` | Positive active cumulative maximum demand (A+) in tariff T1 [kW] |
| `1.2.2` | Positive active cumulative maximum demand (A+) in tariff T2 [kW] |
| `1.2.3` | Positive active cumulative maximum demand (A+) in tariff T3 [kW] |
| `1.2.4` | Positive active cumulative maximum demand (A+) in tariff T4 [kW] |
| `2.2.0` | Negative active cumulative maximum demand (A−) total [kW] |
| `2.2.1` | Negative active cumulative maximum demand (A−) in tariff T1 [kW] |
| `2.2.2` | Negative active cumulative maximum demand (A−) in tariff T2 [kW] |
| `2.2.3` | Negative active cumulative maximum demand (A−) in tariff T3 [kW] |
| `2.2.4` | Negative active cumulative maximum demand (A−) in tariff T4 [kW] |
| `15.2.0` | Absolute active cumulative maximum demand (\|A\|) total [kW] |
| `15.2.1` | Absolute active cumulative maximum demand (\|A\|) in tariff T1 [kW] |
| `15.2.2` | Absolute active cumulative maximum demand (\|A\|) in tariff T2 [kW] |
| `15.2.3` | Absolute active cumulative maximum demand (\|A\|) in tariff T3 [kW] |
| `15.2.4` | Absolute active cumulative maximum demand (\|A\|) in tariff T4 [kW] |
| `3.2.0` | Positive reactive cumulative maximum demand (Q+) total [kvar] |
| `4.2.0` | Negative reactive cumulative maximum demand (Q−) total [kvar] |
| `5.2.0` | Reactive cumulative maximum demand in Q1 total [kvar] |
| `6.2.0` | Reactive cumulative maximum demand in Q2 total [kvar] |
| `7.2.0` | Reactive cumulative maximum demand in Q3 total [kvar] |
| `8.2.0` | Reactive cumulative maximum demand in Q4 total [kvar] |
| `9.2.0` | Apparent cumulative maximum demand (S+) total [kVA] |

### 3.7 Demand in Current Demand Period

| OBIS code | Description |
| --------- | ----------- |
| `1.4.0` | Positive active demand in current demand period (A+) [kW] |
| `2.4.0` | Negative active demand in current demand period (A−) [kW] |
| `15.4.0` | Absolute active demand in current demand period (\|A\|) [kW] |
| `3.4.0` | Positive reactive demand in current demand period (Q+) [kvar] |
| `4.4.0` | Negative reactive demand in current demand period (Q−) [kvar] |
| `5.4.0` | Reactive demand in current demand period in Q1 [kvar] |
| `6.4.0` | Reactive demand in current demand period in Q2 [kvar] |
| `7.4.0` | Reactive demand in current demand period in Q3 [kvar] |
| `8.4.0` | Reactive demand in current demand period in Q4 [kvar] |
| `9.4.0` | Apparent demand in current demand period (S+) [kVA] |

### 3.8 Demand in Last Completed Demand Period

| OBIS code | Description |
| --------- | ----------- |
| `1.5.0` | Positive active demand in last completed demand period (A+) [kW] |
| `2.5.0` | Negative active demand in last completed demand period (A−) [kW] |
| `15.5.0` | Absolute active demand in last completed demand period (\|A\|) [kW] |
| `3.5.0` | Positive reactive demand in last completed demand period (Q+) [kvar] |
| `4.5.0` | Negative reactive demand in last completed demand period (Q−) [kvar] |
| `5.5.0` | Reactive demand in last completed demand period in Q1 [kvar] |
| `6.5.0` | Reactive demand in last completed demand period in Q2 [kvar] |
| `7.5.0` | Reactive demand in last completed demand period in Q3 [kvar] |
| `8.5.0` | Reactive demand in last completed demand period in Q4 [kvar] |
| `9.5.0` | Apparent demand in last completed demand period (S+) [kVA] |

### 3.9 Instantaneous Power Registers

| OBIS code | Description |
| --------- | ----------- |
| `1.7.0` | Positive active instantaneous power (A+) [kW] |
| `21.7.0` | Positive active instantaneous power (A+) in phase L1 [kW] |
| `41.7.0` | Positive active instantaneous power (A+) in phase L2 [kW] |
| `61.7.0` | Positive active instantaneous power (A+) in phase L3 [kW] |
| `2.7.0` | Negative active instantaneous power (A−) [kW] |
| `22.7.0` | Negative active instantaneous power (A−) in phase L1 [kW] |
| `42.7.0` | Negative active instantaneous power (A−) in phase L2 [kW] |
| `62.7.0` | Negative active instantaneous power (A−) in phase L3 [kW] |
| `15.7.0` | Absolute active instantaneous power (\|A\|) [kW] |
| `35.7.0` | Absolute active instantaneous power (\|A\|) in phase L1 [kW] |
| `55.7.0` | Absolute active instantaneous power (\|A\|) in phase L2 [kW] |
| `75.7.0` | Absolute active instantaneous power (\|A\|) in phase L3 [kW] |
| `16.7.0` | Sum active instantaneous power (A+ − A−) [kW] |
| `36.7.0` | Sum active instantaneous power (A+ − A−) in phase L1 [kW] |
| `56.7.0` | Sum active instantaneous power (A+ − A−) in phase L2 [kW] |
| `76.7.0` | Sum active instantaneous power (A+ − A−) in phase L3 [kW] |
| `3.7.0` | Positive reactive instantaneous power (Q+) [kvar] |
| `23.7.0` | Positive reactive instantaneous power (Q+) in phase L1 [kvar] |
| `43.7.0` | Positive reactive instantaneous power (Q+) in phase L2 [kvar] |
| `63.7.0` | Positive reactive instantaneous power (Q+) in phase L3 [kvar] |
| `4.7.0` | Negative reactive instantaneous power (Q−) [kvar] |
| `24.7.0` | Negative reactive instantaneous power (Q−) in phase L1 [kvar] |
| `44.7.0` | Negative reactive instantaneous power (Q−) in phase L2 [kvar] |
| `64.7.0` | Negative reactive instantaneous power (Q−) in phase L3 [kvar] |
| `9.7.0` | Apparent instantaneous power (S+) [kVA] |
| `29.7.0` | Apparent instantaneous power (S+) in phase L1 [kVA] |
| `49.7.0` | Apparent instantaneous power (S+) in phase L2 [kVA] |
| `69.7.0` | Apparent instantaneous power (S+) in phase L3 [kVA] |

### 3.10 Electricity Network Quality Registers

| OBIS code | Description |
| --------- | ----------- |
| `11.7.0` | Instantaneous current (I) [A] |
| `31.7.0` | Instantaneous current (I) in phase L1 [A] |
| `51.7.0` | Instantaneous current (I) in phase L2 [A] |
| `71.7.0` | Instantaneous current (I) in phase L3 [A] |
| `91.7.0` | Instantaneous current (I) in neutral [A] |
| `11.6.0` | Maximum current (I max) [A] |
| `31.6.0` | Maximum current (I max) in phase L1 [A] |
| `51.6.0` | Maximum current (I max) in phase L2 [A] |
| `71.6.0` | Maximum current (I max) in phase L3 [A] |
| `91.6.0` | Maximum current (I max) in neutral [A] |
| `12.7.0` | Instantaneous voltage (U) [V] |
| `32.7.0` | Instantaneous voltage (U) in phase L1 [V] |
| `52.7.0` | Instantaneous voltage (U) in phase L2 [V] |
| `72.7.0` | Instantaneous voltage (U) in phase L3 [V] |
| `13.7.0` | Instantaneous power factor |
| `33.7.0` | Instantaneous power factor in phase L1 |
| `53.7.0` | Instantaneous power factor in phase L2 |
| `73.7.0` | Instantaneous power factor in phase L3 |
| `14.7.0` | Frequency [Hz] |

### 3.11 Tamper Registers (energy + elapsed time)

> **⚠ Vendor-specific — not normative OBIS.** The `C.53.x` tamper codes below are manufacturer/meter-vendor allocations within the abstract C-group, **not** registers fixed by IEC 62056-6-1. In standard OBIS the C-group (group A = abstract/`0`) is reserved for general/service objects, and the specific E-values here are vendor-assigned. Do **not** cite these as normative IEC codes; verify against the specific meter's COSEM object model.

| OBIS code | Description |
| --------- | ----------- |
| `C.53.1` | Tamper 1 energy register |
| `C.53.2` | Tamper 2 energy register |
| `C.53.3` | Tamper 3 energy register |
| `C.53.4` | Tamper 4 energy register |
| `C.53.11` | Tamper 5 energy register |
| `C.53.5` | Tamper 1 time counter register |
| `C.53.6` | Tamper 2 time counter register |
| `C.53.7` | Tamper 3 time counter register |
| `C.53.9` | Tamper 4 time counter register |
| `C.53.10` | Tamper 5 time counter register |

### 3.12 Event Registers (counters and timestamps)

> **⚠ Vendor-specific — not normative OBIS.** The `C.2.x` / `C.7.x` / `C.51.x` event codes below (cover-open, fraud start/stop, power up/down, etc.) are meter-vendor allocations in the abstract C-group, **not** IEC-fixed registers. Treat as orientation only; confirm against the target meter's documentation.

| OBIS code | Description |
| --------- | ----------- |
| `C.2.0` | Event parameters change — counter |
| `C.2.1` | Event parameters change — timestamp |
| `C.51.1` | Event terminal cover opened — counter |
| `C.51.2` | Event terminal cover opened — timestamp |
| `C.51.3` | Event main cover opened — counter |
| `C.51.4` | Event main cover opened — timestamp |
| `C.51.5` | Event magnetic field detection start — counter |
| `C.51.6` | Event magnetic field detection start — timestamp |
| `C.51.7` | Event reverse power flow — counter |
| `C.51.8` | Event reverse power flow — timestamp |
| `C.7.0` | Event power down — counter |
| `C.7.10` | Event power down — timestamp |
| `C.51.13` | Event power up — counter |
| `C.51.14` | Event power up — timestamp |
| `C.51.15` | Event RTC (Real Time Clock) set — counter |
| `C.51.16` | Event RTC (Real Time Clock) set — timestamp |
| `C.51.21` | Event terminal cover closed — counter |
| `C.51.22` | Event terminal cover closed — timestamp |
| `C.51.23` | Event main cover closed — counter |
| `C.51.24` | Event main cover closed — timestamp |
| `C.51.25` | Event log-book 1 erased — counter |
| `C.51.26` | Event log-book 1 erased — timestamp |
| `C.51.27` | Event fraud start — counter |
| `C.51.28` | Event fraud start — timestamp |
| `C.51.29` | Event fraud stop — counter |
| `C.51.30` | Event fraud stop — timestamp |

### 3.13 Miscellaneous Registers (used in sequences)

> **Note:** The `0.9.x` (clock/date), `0.0.x` (device address), `0.1.x`, `0.2.x`, `0.3.0`, `0.4.x` abstract objects are standard-aligned. The `C.1.x`, `C.6.x`, `C.60.9`, `C.87.0`, and `F.F.0` entries are vendor-allocated C-group / fatal-error objects — verify against the meter model before citing as normative.

| OBIS code | Description |
| --------- | ----------- |
| `0.9.1` | Current time (hh:mm:ss) |
| `0.9.2` | Date (YY.MM.DD or DD.MM.YY) |
| `0.9.4` | Date and time (YYMMDDhhmmss) |
| `0.8.0` | Demand period [min] |
| `0.8.4` | Load profile period [min] (option) |
| `0.0.0` | Device address 1 |
| `0.0.1` | Device address 2 |
| `0.1.0` | MD reset counter |
| `0.1.2` | MD reset timestamp |
| `0.2.0` | Firmware version |
| `0.2.2` | Tariff program ID |
| `C.1.0` | Meter serial number |
| `C.1.2` | Parameters file code |
| `C.1.4` | Parameters check sum |
| `C.1.5` | Firmware built date |
| `C.1.6` | Firmware check sum |
| `C.6.0` | Power down time counter |
| `C.6.1` | Battery remaining capacity |
| `F.F.0` | Fatal error meter status |
| `C.87.0` | Active tariff |
| `0.2.1` | Parameters scheme ID |
| `C.60.9` | Fraud flag |
| `0.3.0` | Active energy meter constant |
| `0.4.2` | Current transformer ratio |
| `0.4.3` | Voltage transformer ratio |

---

## 4. Editorial Notes (deviations from the vendor source)

The following corrections were applied during conversion. They matter for any academic or specification use:

1. **`2.8.x` symbol corrected `(A+)` → `(A−)`.** The vendor table labelled the negative-active-energy rows with the A+ symbol, which contradicts the row descriptions ("Negative active energy"). Corrected throughout.
2. **`16.8.` corrected to `16.8.1`.** The vendor table dropped the E sub-identifier for the tariff-T1 sum-active-energy row.
3. **Source authority.** PROMOTIC is a SCADA vendor reference and is suitable for orientation only. For citable specification work, reference the standard directly: **IEC 62056-6-1:2023 (Ed. 4.0)**, *Electricity metering data exchange — The DLMS®/COSEM suite — Part 6-1: Object Identification System (OBIS).* Note that the source document's "IEC 62056-61" citation is the legacy designation, now superseded.

---

## 5. References

- **IEC 62056-6-1:2023** (Edition 4.0, December 2023) — *Electricity metering data exchange — The DLMS®/COSEM suite — Part 6-1: Object Identification System (OBIS).* **Current normative edition — cite this.** Cancels and replaces the 2017 third edition.
- **Edition history (for completeness):** Ed. 1.0 (2013) → Ed. 2.0 (2015) → Ed. 3.0 (2017) → **Ed. 4.0 (2023, current)**.
- **`IEC 62056-61`** (no second hyphen) — *legacy designation only.* This is the pre-restructure numbering referenced by the source vendor document. Do **not** cite this form in current work; it is superseded by the `IEC 62056-6-1` part numbering above.
- PROMOTIC SCADA, `PmIEC62056` driver documentation, MICROSYS spol. s r.o. (PROMOTIC 9.0.34) — *vendor reference, orientation only — not citable as a primary standard.*

