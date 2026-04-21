# Thai Grid Tariffs (MEA/PEA)

The **GridTokenX Smart Meter Simulator** incorporates energy pricing models inspired by the **Metropolitan Electricity Authority (MEA)** and **Provincial Electricity Authority (PEA)** of Thailand.

## 💰 Residential Tariff Structure

For simulation consistency, the default pricing follows a simplified version of the Thai residential progressive rate:

| Monthly Consumption (kWh) | Description | Base Rate (Baht/kWh) |
| :--- | :--- | :--- |
| **0 - 150** | Base Tier | ~3.24 |
| **151 - 400** | Mid Tier | ~4.22 |
| **> 400** | High Tier | ~4.42 |

> [!NOTE]
> The simulator's `GRID_PURCHASE_RATE` environment variable (default: `0.28` GXT or `3.5 - 4.5` Baht equivalent) allows for global overrides of these values.

## 📉 Standard Load Profiles (SLP)

The simulator uses standardized consumption patterns to fill data gaps and provide realistic baselines when specific historical data is missing.

### 1. Residential (H0)
-   **Characteristics**: Peak demand in the evening (18:00 - 22:00) and early morning (06:00 - 08:00).
-   **Usage**: Default profile for `consumer` and `prosumer` meter types.

### 2. Commercial / Industrial (G0)
-   **Characteristics**: Sustained high demand during business hours (09:00 - 17:00).
-   **Usage**: Used for larger commercial entities or school buildings in the grid model.

## ☀️ Net Metering & Feed-in Tariffs

Thailand currently adopts a **Net Billing** or **Feed-in Tariff (FiT)** model for rooftop solar:

-   **Self-Consumption**: Solar generation first offsets local consumption (Savings = Retail Rate).
-   **Surplus Export**: Excess energy exported to the grid is typically valued lower than the purchase rate (e.g., ~2.20 Baht/kWh for residential solar).
-   **GridTokenX Override**: In the simulator, surplus energy can be automatically converted into **GTNX tokens** on the Solana blockchain, bypassing traditional utility billing constraints in specialized microgrid scenarios.

## ⏰ Time-of-Use (TOU) Scaling

The engine supports a dynamic multiplier to simulate TOU pricing:
-   **On-Peak (09:00 - 22:00, Mon-Fri)**: 1.2x Multiplier.
-   **Off-Peak (All other times)**: 0.8x Multiplier.

This functionality is critical for testing the VPP's ability to perform **Charge/Discharge optimization** (charging batteries during off-peak and discharging to offset on-peak costs).

### Detailed 2026 TOU Rates (Base Rates)

| Category | Voltage Level | On-Peak (Baht/kWh) | Off-Peak (Baht/kWh) | Service Charge (Baht/Month) |
| :--- | :--- | :--- | :--- | :--- |
| **Residential (Type 1.2)** | < 22 kV | 5.7982 | 2.6369 | 33.29 |
| **Residential (Type 1.2)** | ≥ 22 - 33 kV | 5.1135 | 2.6037 | 312.24 |
| **Small Business (Type 2.2)** | < 22 kV | 5.7982 | 2.6369 | 33.29 |
| **Small Business (Type 2.2)** | ≥ 22 - 33 kV | 5.1135 | 2.6037 | 312.24 |

### TOU Time Schedule

| Period | Days and Times |
| :--- | :--- |
| **On-Peak** | Monday – Friday: 09:00 – 22:00 |
| **Off-Peak** | Monday – Friday: 22:00 – 09:00 |
| **Off-Peak** | Sat, Sun, and Public Holidays (All Day) |

---
_Next: [Thai Market Dynamics](thai-market.md)_
