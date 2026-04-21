# AI Implementation & Strategy for Smart Meter Simulator

This document provides a comprehensive overview of the AI and forecasting components within the GridTokenX Smart Meter Simulator project, specifically designed for AI agents to understand the architecture, models, and data flow.

## 1. Core Architecture

The project employs a dual-layer AI strategy:
1.  **Centralized Forecasting Engine (`AIForecastingEngine`):** Handles complex, multi-island constraints (Koh Samui, Koh Phangan, Koh Tao).
2.  **Edge-Optimized Engine (`EdgeForecastingEngine`):** A lightweight, decentralized forecaster for substation-level controllers.

### Centralized Engine (`backend/src/smart_meter_simulator/ai/`)
-   **Forecasting Engine (`forecasting_engine.py`):** Uses a hybrid approach combining **Gradient Boosting (LightGBM)** with **Dynamic Demographic Metrics**.
-   **Feature Engineering (`feature_engineering.py`):** Extracts cyclical temporal features (sin/cos encoding), weather data, and historical load lags.

### Edge Engine (`backend/src/smart_meter_simulator/core/`)
-   **Edge Forecaster (`forecaster.py`):** Designed for resource-constrained environments (blueprint for substation deployment). Uses quantized sequence logic to target **<10% MAPE** for 24-hour lookahead.

---

## 2. Models & Key Metrics

### Dual-Target Forecasting
The simulator predicts two critical "lines" to determine grid stability:
1.  **Load Tao (The Yellow Line):** The forecasted electrical demand on Koh Tao.
2.  **Capacity 115kV (The Blue Line):** The dynamic remaining capacity of the submarine cable from Koh Samui/Phangan to Koh Tao.

### Demographic Load Models (New Assumption)
Load is not just historical; it's calculated using real-world tourism and residency data:
-   **Koh Tao DAP (Daily Active Population):** $R_{base} + (T_{annual} \times W_m / D_m) \times L$.
-   **Koh Phangan Lunar Factor:** Incorporates "Full Moon Party" lunar spikes ($S_{lunar} = 8\text{ MW}$).
-   **Digital Nomad Baseload:** Fixed active population ($N_{active} = 5,000$) with high Energy Intensity ($3.5\text{ kW}$/person).

### Dynamic Line Rating (DLR)
The capacity calculation includes a **Thermal Derating Simulation**:
-   **Heat Accumulation:** Cable temperature rises when upstream load (Samui + Phangan) exceeds $18\text{ MW}$.
-   **Ambient Penalty:** High sea temperatures prevent cooling.
-   **Derating:** $150\text{ kW}$ reduction per unit of accumulated thermal stress.

## 3. Training Dataset & Feature Engineering

The training pipeline (`pea_lightgbm_trainer.py`) utilizes a time-series dataset with dual targets. Data is sourced from InfluxDB with a synthetic augmentation layer for development.

### Feature Vector Structure
The model uses a combination of temporal, historical, and rolling features:

| Feature Category | Symbols / Columns | Description |
|------------------|-------------------|-------------|
| **Temporal** | `hour`, `dayofweek`, `month` | Cyclical time markers (0-23, 0-6, 1-12). |
| **Indicator** | `is_weekend` | Binary flag for tourism-driven load spikes. |
| **Historical Lags** | `target_lag1h`, `2h`, `3h`, `24h`, `48h` | Capture short-term momentum and daily/weekly seasonality. |
| **Rolling Stats** | `target_roll24` | 24-hour moving average to capture baseline trends. |

### Target Variables
1.  **`load_tao_mw`**: Net demand on Koh Tao (Aggregated meter readings).
2.  **`capacity_115kv_mw`**: Remaining cable throughput after Samui/Phangan consumption.

### Data Ingestion Pipeline
1.  **InfluxDB Query**: Extracts hourly aggregates from the `meter_readings` bucket.
2.  **Missing Value Handling**: Forward-fill for short gaps; synthetic interpolation for long outages.
3.  **Normalization**: Standard scaling applied to lag features to ensure convergence.

---

## 4. Training & Validation (`backend/scripts/`)

### LightGBM Trainer (`pea_lightgbm_trainer.py`)
-   **Target:** Predicts both `load_tao_mw` and `capacity_115kv_mw`.
-   **Hyperparameters:**
    -   `n_estimators`: 500
    -   `learning_rate`: 0.03
    -   `num_leaves`: 15
-   **Validation:** Enforcement of **MAPE < 10.0%**. If MAPE exceeds this threshold, the training script fails.
-   **Data Sources:** InfluxDB (`meter_readings` bucket) for real historical data, with synthetic fallback for local development.

---

## 4. Integration & Optimization

### Optimal Dispatch Schedule
AI forecasts feed directly into the `StrategyService` to calculate:
-   **Constraint Triggers:** When $Capacity_{115kV} - Load_{Tao} < 0$.
-   **BESS Dispatch:** Required Battery Energy Storage System (BESS) output to bridge the "Yellow/Blue Line" gap.
-   **VPP (Virtual Power Plant) Commands:** Aggregated signals to distributed meters.

### Key Performance Indicators (KPIs)
-   **MAPE (Mean Absolute Percentage Error):** Primary accuracy metric.
-   **Thermal Recovery Time:** Time required for the 115kV cable to cool below derating thresholds.
-   **DAP Accuracy:** Correlation between predicted population and observed base load.

---

## 5. Development Roadmap for AI Agents
-   **TCN Implementation:** Transition from LightGBM to Temporal Convolutional Networks (TCN) for better sequence dependency capture.
-   **Federated Learning:** Blueprint for training on local substation data without moving raw meter data to the cloud.
-   **Real-time Weather Integration:** Connect `FeaturePipeline.get_weather_features` to live OpenWeatherMap API.
