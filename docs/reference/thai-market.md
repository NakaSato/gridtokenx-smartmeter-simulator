# Thai Market Dynamics

The **GridTokenX Smart Meter Simulator** is designed to model the evolving landscape of the Thai energy market, from the traditional "single-buyer" model to the new era of decentralized **Peer-to-Peer (P2P)** trading.

## 🏛️ Traditional Market Players

The electricity sector in Thailand is traditionally dominated by three state-owned enterprises:

1.  **EGAT (Electricity Generating Authority of Thailand)**: Responsible for generation and high-voltage transmission (the "bulk" market).
2.  **MEA (Metropolitan Electricity Authority)**: Distributes electricity to Bangkok, Nonthaburi, and Samut Prakan.
3.  **PEA (Provincial Electricity Authority)**: Distributes electricity to the rest of the 74 provinces in Thailand.

### Simulator Integration
The simulator's **PostGIS** integration and **Pandapower** configurations are optimized for **MEA/PEA 22kV distribution feeder topologies**, which are the primary endpoints for residential and commercial solar (DERs).

## 🔄 Peer-to-Peer (P2P) Trading Model

The simulator demonstrates the feasibility of P2P energy sharing, allowing neighbors to trade excess solar generation directly.

### 🏘️ Trading Mechanism
-   **Local Energy Exchange**: Solar generation first offsets local consumption.
-   **Surplus Discovery**: The `MarketEngine` identifies prosumers with excess kWh and consumers with deficit energy.
-   **Nodal Pricing**: In the simulator, the price of energy can vary by node, incentivizing trading in congested parts of the feeder to maintain local voltage stability.

### 💰 Tokenization & Settlement
-   **Solana Integration**: Settlements are performed on the Solana blockchain using a high-throughput **GTNX token** model.
-   **Instant Clear**: Unlike traditional utilities that bill monthly, the simulator models a near-instant settlement at every 15-minute interval.

## ⚡ Ancillary Services & the VPP Role

As the Thai market deregulates, Virtual Power Plants (VPPs) are expected to play a critical role in grid stability. The simulator models the following services:

1.  **aFRR (Automatic Frequency Restoration Reserve)**: VPP clusters respond to grid-wide frequency drops, providing support at the distribution level to prevent upstream instabilities.
2.  **Peak Shaving**: Coordinated discharge of hundreds of residential batteries to reduce the peak demand on the distribution transformer.
3.  **ERC Sandboxing**: The simulator acts as a digital sandbox for the **Energy Regulatory Commission (ERC) of Thailand** to test new P2P and VPP regulations.

## 🌏 Carbon-Aware Dispatch

Thailand's **Power Development Plan (PDP)** emphasizes a transition to renewable energy. The simulator's **Carbon Intensity tracking** allows users to see the real-time displacement of fossil-fuel-based grid power with clean distributed solar.

---
_Next: [Economic Models](economic-models.md)_
