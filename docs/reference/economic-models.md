# Economic Models

The **GridTokenX Smart Meter Simulator** provides automated economic modeling for decentralizing Energy Markets. The goal is to provide a realistic financial landscape for residential and commercial DER investments.

## 📊 Core Pricing Components

The simulation's economy is driven by three primary variables:

### 1. Base Electricity Rate (`GRID_PURCHASE_RATE`)
-   **Default**: `0.28` GXT/kWh (~3.5 Baht/kWh).
-   **Usage**: The standard price of energy purchased from the utility (MEA/PEA).

### 2. Feed-in Rate (Net Billing)
-   **Logic**: Energy exported to the grid is typically valued at `~2.20` Baht.
-   **Simulator**: This is often superseded by P2P trading prices, which are more dynamic and reflective of local grid conditions.

### 3. Nodal Pricing (LMP)
-   **Definition**: **Locational Marginal Pricing (LMP)**.
-   **Logic**: The price of electricity varies by bus (node) based on the cost of delivery and local losses.
-   **VPP Impact**: VPP clusters are incentivized to discharge in high-LMP nodes to relieve congestion and capture higher revenues.

## 💰 VPP Revenue Streams

Virtual Power Plants generate revenue through multiple services:

-   **aFRR Payments**: Incentives paid for providing frequency restoration reserves.
-   **Peak Shaving Rebates**: Discounts or payments from the utility for reducing the transformer's peak load.
-   **P2P Commissions**: Small transaction fees collected for matching local buyers and sellers.
-   **Carbon Credits**: Payments for displacing dirty grid generation with local clean solar.

## 📈 ROI Modeling for DERs

The simulator allows for the calculation of **Return on Investment (ROI)** for residential solar and batteries:

### Solar ROI Calculation
$$ROI_{solar} = \frac{\sum_{t=1}^{n} (SelfConsume \times Price_{buy} + Export \times Price_{sell})}{Investment_{total}}$$

-   **Self-Consumption**: The "Savings" component of the investment.
-   **Export Revenue**: The "Earning" component, maximized through V2G/P2P trading.

### Battery Arbitrage
Batteries "buy" energy during low-price (off-peak) periods and "sell" it (or offset consumption) during high-price (peak) periods. The simulator models the degradation of round-trip efficiency (default: 90%) over time.

## 🌍 Carbon Offset Economy

The `EnergyReading` model tracks the **Carbon Offset** (kg CO2 saved) for every kWh of clean generation:
-   **Intensity Override**: Adjust the local grid's carbon intensity (e.g., 500 g/kWh for natural gas/coal mix).
-   **Incentivization**: Higher carbon intensity leads to higher VPP dispatch priority for solar/battery discharge.

---
_Next: [Thai Grid Topology](thai-grid-topology.md)_
