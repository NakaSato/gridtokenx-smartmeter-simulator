# Smart Meter Simulation Specification

## Document Status & Roadmap

**Current Implementation Status:** Phase 22 (Advanced Grid Intelligence)  
**Specification Coverage:** Phases 1-22 (Full Grid Orchestration Framework)

### Implementation Roadmap (Completed)

| Phase | Section | Description | Status |
|---|---|---|---|
| **1-2** | 4-5, 7-8 | AMI Foundation, Pandapower integration, basic SE | ✅ Complete |
| **3** | 9 | Grid Integration, Geo-SAM, Bad Data Detection | ✅ Complete |
| **4** | 6 | Efficient Data Handling (Polars & SLP) | ✅ Complete |
| **5** | 9 | Interoperability (CIM Import/Export & Mosaik) | ✅ Complete |
| **6-22** | 10+ | Advanced Intelligence (LMP, VPP, Carbon, Healing) | ✅ Complete |

### Summary of Capability
The simulator now provides a complete cyber-physical modeling environment for:
- ✅ **Grid Resilience:** Islanding detection, black start, and frequency regulation.
- ✅ **Market Dynamics:** Nodal Marginal Pricing (LMP) and VPP cluster balancing.
- ✅ **Data Interop:** Full CIM round-trip and multi-domain co-simulation.
- ✅ **Cyber-Security:** Real-time FDI (False Data Injection) detection.
ompt.md) for implementation plan.

---

## 3. Theoretical Foundations of Smart Metering in Simulation

### 3.1 Physics vs. Cyber-Physical Modeling

To specify a smart meter model accurately, one must distinguish between the physical measurement and the reported data.

**The Physical Truth:** In a simulation, the "true" state of the system is the result of the power flow calculation ($\mathbf{x}_{true}$). This represents the actual physics of the grid—voltage magnitudes and angles at every bus, and power flows through every branch.

**The Cyber-Physical Measurement:** The smart meter does not report $\mathbf{x}_{true}$. It reports a measured value $z$ that is corrupted by sensor inaccuracy, analog-to-digital conversion errors, and potentially communication noise.

$$z = h(\mathbf{x}_{true}) + \epsilon$$

Where $h(\cdot)$ is the measurement function (e.g., extracting the voltage at a bus) and $\epsilon$ is the error term.

A high-fidelity simulator must generate $z$ from $\mathbf{x}_{true}$ by applying specific error models. It implies that the simulator must effectively run two parallel layers:
- **Ground Truth layer** where ideal physics are calculated
- **Measurement layer** where these truths are sampled and distorted to mimic reality

### 3.2 Measurement Theory and Uncertainty

The error term $\epsilon$ is typically modeled as a random variable following a Gaussian (Normal) distribution with zero mean and standard deviation $\sigma$:

$$\epsilon \sim \mathcal{N}(0, \sigma^2)$$

This assumption is foundational for the Weighted Least Squares (WLS) algorithm used in State Estimation. The "weight" assigned to a measurement is the inverse of its variance ($W = 1/\sigma^2$). Therefore, the specification of $\sigma$ is the single most critical parameter in smart meter modeling. It defines the "trustworthiness" of the meter relative to other data sources (such as SCADA measurements or pseudo-measurements).

However, real-world errors are not always Gaussian. They can include:

- **Systematic Errors (Bias):** Calibration drift in the voltage transformer (VT) or current transformer (CT)
- **Gross Errors (Bad Data):** Spikes caused by faulty electronics or packet corruption
- **Synchronization Errors:** Mismatches caused by meters reporting data at slightly different times (skew)

While the baseline specification assumes Gaussian noise for WLS compatibility, an advanced simulator specification should include modules to inject non-Gaussian errors to test the robustness of "Bad Data Detection" algorithms.

### 3.3 The Role of Pseudo-Measurements

In distribution grids, it is economically unfeasible to place high-precision meters at every node. To solve the State Estimation problem (which requires the system to be observable, i.e., the Jacobian matrix to be full rank), the simulator must generate "pseudo-measurements." These are statistical estimates of load or generation based on historical profiles or standard load profiles (SLPs).

Mathematically, a pseudo-measurement is treated exactly like a real measurement but with a significantly larger standard deviation (lower weight). This ensures that the solver can converge even with sparse real telemetry, but the resulting state estimate will be "pulled" towards the few trusted smart meter readings available.

## 4. Pandapower Architecture for AMI

### 4.1 The Tabular Data Structure

Pandapower organizes grid data into separate DataFrames for each element type: `net.bus`, `net.line`, `net.load`, `net.trafo`, etc. The simulation of smart meters relies on a specific auxiliary DataFrame: `net.measurement`.

The specification for a smart meter in pandapower is, fundamentally, a specification for a row (or set of rows) in this `net.measurement` table. There is no `net.smart_meter` table. Instead, the smart meter is a logical concept that aggregates multiple measurement entries pointing to the same physical location.

**Table 1: Detailed Schema of the Pandapower Measurement Table for AMI**

| Column Name | Data Type | Description | AMI Implementation Detail |
|---|---|---|---|
| `meas_type` | string | Physical quantity measured (v, p, q, i, ia, va) | AMI typically provides v (Voltage), p (Active Power), q (Reactive Power). i (Current) is less common in residential meters but standard in commercial/industrial meters |
| `element_type` | string | The grid element being measured (bus, line, trafo) | Residential meters usually measure a load or sgen. Grid-side meters measure line or trafo. Voltage is always measured at a bus |
| `element` | integer | The index of the element in its respective table | The Foreign Key linking the measurement to the grid topology (e.g., load.index) |
| `value` | float | The measured value | The noisy value $z$ generated by the simulator. Units: p.u. for V, MW/MVar for P/Q, kA for I |
| `std_dev` | float | Standard deviation of the measurement error | Derived from the meter's accuracy class. Units must match value |
| `side` | string | Location on branch (from, to) | Mandatory for line and trafo measurements. A meter at the substation measures the "from" side of the feeder head line |
| `name` | string | Arbitrary label | Essential for mapping. Should contain the unique AMI ID (e.g., "SM_100234") |

### 4.2 Element-Based Modeling vs. Bus-Branch Models

In many power flow solvers (like MATPOWER), loads are aggregated at the bus level. Pandapower maintains individual load and sgen elements connected to a bus. This distinction is crucial for AMI modeling. A single bus in a detailed LV model might represent a distribution pillar feeding four different houses. In pandapower, this bus would have four distinct load elements connected to it.

**Correct Specification:** A residential smart meter should be modeled as measuring the power flow of a specific load element (`element_type='load'`), NOT the net injection at the bus (unless it is a bulk metering point). This allows the simulator to capture the individual behavior of customers.

**Voltage Measurement:** Conversely, voltage is a nodal property. The voltage measurement from the smart meter is associated with the bus to which the load is connected (`element_type='bus'`, `meas_type='v'`).

### 4.3 Handling Sign Conventions and Reference Frames

One of the most frequent sources of error in Smart Grid simulation is the sign convention for power.

**Pandapower Convention:**
- **Loads:** Positive $P$ means consumption (active power flow out of the grid)
- **Generators (sgen/gen):** Positive $P$ means generation (active power flow into the grid)
- **Bus Injections:** In the power flow kernel, generation is usually treated as positive injection, load as negative injection

**Measurement Convention:**

When defining a measurement of type p or q on a bus, pandapower assumes the "Generator Reference Frame" by default in some contexts, but strictly speaking, `create_measurement` documents that "Generation is a positive bus power injection, consumption negative".

**Critical Spec:** If a smart meter measures a load consuming 2 kW, the `net.load` table shows `p_mw = 0.002`. However, if this is modeled as a bus injection measurement, the value must be `-0.002`. If it is modeled as a specific element measurement (`element_type='load'`), the sign must match the element definition (positive). The simulator logic must enforce this consistency to prevent State Estimation divergence.

## 5. Detailed Smart Meter Object Specification

To manage the complexity of thousands of measurements, the simulator should not interact directly with the `net.measurement` table for configuration. Instead, it requires an object-oriented abstraction layer—a SmartMeter class—that programmatically manages the lower-level pandapower entries.

### 5.1 Smart Meter Class Architecture

The SmartMeter class serves as the digital twin of the physical device. It encapsulates the device's configuration, metrological properties, and topological location.

**Class Attributes Specification:**

- `meter_id` (String): The unique identifier (e.g., UUID or Serial Number)
- `connection_point` (Tuple): `(bus_index, element_index, element_type)`. Defines where the meter is physically installed
- `meter_type` (Enum): RESIDENTIAL, COMMERCIAL, INDUSTRIAL, FEEDER, SUBSTATION. This determines the available measurement channels
- `accuracy_class` (Enum): CLASS_0_2, CLASS_0_5, CLASS_1_0, CLASS_2_0. This maps to the standard deviation values
- `sampling_rate` (Integer): Time in minutes (e.g., 15, 30, 60). Defines the temporal resolution for time-series aggregation
- `channels` (List): A list of active measurement channels

### 5.2 Measurement Set Definitions

A single smart meter instance translates into multiple pandapower measurements. The specification must define this mapping rigorously.

#### 5.2.1 Residential Meter (Single Phase / Three Phase)

**Context:** Installed at a customer premise.

**Pandapower Mapping:**

- **Voltage:** One measurement of type v at the connected bus
  - Value: $V_{bus}$
  - Std Dev: Derived from Accuracy Class (typically 1.0%)

- **Active Power:** One measurement of type p at the connected load
  - Value: $P_{load}$
  - Std Dev: Derived from Accuracy Class (typically 2.0%)

- **Reactive Power:** One measurement of type q at the connected load
  - Value: $Q_{load}$
  - Std Dev: Typically higher than P (e.g., 3.0%)

#### 5.2.2 Prosumer Meter (with PV)

**Context:** Customer with rooftop solar.

**Pandapower Mapping:**

If the PV and Load are modeled as separate elements (recommended for detail), the smart meter effectively measures the net flow at the connection point.

**Implementation:** The simulator must calculate the net power $P_{net} = P_{load} - P_{gen}$.

**Alternative:** Create two separate logical meters if the physical installation has separate metering for generation (feed-in tariff) and consumption.

**Constraint:** If modeling the net flow as a single bus injection measurement, the uncertainty $\sigma$ must be carefully calculated, as the relative error can be huge when $P_{load} \approx P_{gen}$.

#### 5.2.3 Feeder Head Meter (Data Concentrator)

**Context:** Installed at the secondary side of the MV/LV transformer.

**Pandapower Mapping:**

- **Current:** Measurement of type i on the transformer or the outgoing line. This is critical for thermal loading analysis
- **Power:** Measurements of p, q on the line (side='from')
- **Voltage:** Measurement of v at the substation bus
- **Accuracy:** These are typically high-precision devices (Class 0.2 or 0.5), yielding very low $\sigma$ values (e.g., 0.2% - 0.5%)

### 5.3 Measurement Accuracy Specification

The translation of "Accuracy Class" to "Standard Deviation" ($\sigma$) is a statistical process. The Accuracy Class typically represents the maximum error $E_{max}$ (e.g., Class 1.0 means $\pm 1\%$ error) at full scale or nominal load.

Assuming the error is normally distributed and $E_{max}$ represents the $3\sigma$ bound (99.7% confidence) or $2\sigma$ bound (95% confidence), the spec must define the conversion factor.

**Common Practice:** Assume $E_{max} = 3\sigma$.

$$\sigma = \frac{\text{Accuracy Class}}{300} \times \text{Nominal Value}$$

**Example:** Class 1.0 meter measuring voltage at 1.0 p.u.

$$\sigma_v = \frac{1.0}{300} \times 1.0 = 0.0033 \text{ p.u.}$$

**Pandapower Implementation:** The simulator must allow the user to configure this "Sigma Factor" (2 or 3). Using a factor of 3 is more conservative and prevents the State Estimator from discarding valid measurements as outliers.

## 6. Data Ingestion and Management

### 6.1 Data Sources and Formats

The simulator must ingest massive amounts of temporal data to drive the load and sgen elements. While pandapower supports direct DataFrame inputs, a robust simulator spec requires a defined schema for interoperability.

#### 6.1.1 The Standard CSV Schema

A standardized CSV format is required for the DataSource.

- **Header:** `timestamp, meter_id_1, meter_id_2, ... meter_id_n`
- **Rows:** Each row represents a timestep
- **Content:** Active power values (kW). Reactive power is often provided in a separate file or derived via a Power Factor assumption

**Pandas Optimization:** For large datasets (e.g., 10,000 meters @ 15-min intervals for a year = 350 million points), CSV is inefficient. The spec should recommend HDF5 or Parquet formats for the storage of time-series data, utilizing `pandas.read_hdf` or `pandas.read_parquet` for fast I/O.

### 6.2 Profile Management Logic

The simulator must handle two types of data profiles:

**Deterministic Profiles (Historical):** Recorded AMI data used for forensic analysis or model validation.
- Logic: Direct mapping of timestamped values to load elements

**Stochastic Profiles (Synthetic):** Generated profiles for planning studies (e.g., Monte Carlo simulations).
- Logic: The simulator must include a "Profile Generator" module that takes annual consumption (kWh) and applies standard load profiles (SLP) such as the H0 profile for households or G0 for business. This module scales the normalized SLP to match the target energy consumption.

### 6.3 The Controller Pattern

In pandapower, time-dependent variables are managed by Controllers. The SmartMeter spec relies heavily on the ConstControl class.

**Implementation:** The simulator instantiates a ConstControl for each column in the DataSource.

```python
ds = DFData(df_measurement_data)
ConstControl(net, element='load', variable='p_mw', element_index=load_indices,
             data_source=ds, profile_name=meter_ids)
```

**Optimization:** Creating thousands of individual ConstControl objects is computationally expensive. The spec must mandate the use of vectorized controllers. A single ConstControl instance should map a matrix of profiles to an array of load indices. This leverages the underlying numpy optimizations in pandapower.

### 6.4 Handling Missing Data and Alignment

Real-world data is messy. The simulator must implement a "Data Pre-processing" stage:

- **Timestamp Alignment:** Ensure all meter data is resampled to the simulation timestep (e.g., `df.resample('15T').mean()`)
- **Gap Filling:** Linear interpolation for short gaps (1-2 intervals); substitution with SLP data for long gaps
- **Unit Conversion:** Conversion from kW (typical AMI output) to MW (Pandapower internal unit)

## 7. State Estimation Implementation Specification

The integration of smart meters into State Estimation (SE) is the primary use case for high-fidelity AMI modeling. This section specifies how the simulator executes the SE loop.

### 7.1 Algorithm Selection and Configuration

Pandapower offers multiple estimation algorithms. The choice depends on the network characteristics.

**Newton-Raphson (NR) WLS:** The standard approach. It iteratively solves for the state update $\Delta x$ by minimizing the weighted residuals.
- Pros: Robust for well-conditioned networks
- Cons: Can diverge in distribution grids with high R/X ratios or very low impedances (short lines)

**Iwamoto NR:** An estimation method with a dampening factor.
- Spec: The simulator should include an "Auto-Fallback" mechanism. It attempts standard NR first; if convergence fails (detected by `success=False`), it retries with Iwamoto.

**Current-Based SE:** Formulates the problem in terms of currents rather than power. This makes the problem more linear and is often superior for distribution grids. This should be an exposed option in the simulator configuration.

### 7.2 Pseudo-Measurement Generation Strategy

This is a critical component for observability. The simulator must include a PseudoMeasurementGenerator class.

**Logic:**

1. Identify unobservable nodes (buses with no voltage measurement and no connected measured injections)
2. For each unobserved load, retrieve its Annual Average Consumption (AAC) or a default SLP
3. Generate a P and Q value for the current timestep
4. Assign a high Standard Deviation. The spec recommends $\sigma_{pseudo} = 50\%$ to $100\%$ of the value
5. Inject this into the measurement set

**Impact:** This ensures the SE gain matrix $G = H^T W H$ is non-singular, allowing a solution to be found even with sparse AMI coverage.

### 7.3 Bad Data Detection and Processing

The simulator must emulate the Control Center's ability to detect faulty meters.

**Chi-Squared Test:** A global test to check if the sum of weighted squared residuals exceeds a threshold (related to the degrees of freedom).
- Implementation: `pandapower.estimation.chi2_analysis(net)`

**Normalized Residuals (rN):** A local test to identify specific bad measurements.
- Logic: After estimation, calculate $r_N$ for every measurement. If $\max(r_N) > 3.0$ (typical threshold), the measurement is flagged as "Bad Data"

**Simulator Workflow:** The simulator should offer a "Sanitization Mode" where it iteratively removes the measurement with the highest $r_N$ and re-runs estimation until no bad data remains. This effectively models the filtering of erroneous smart meter packets.

### 7.4 Virtual Measurements for Zero Injections

Distribution grids have many "transit" nodes (buses with no load/gen, just line connections). These provide exact information: Sum of currents is zero (KCL).

**Spec:** The simulator must automatically identify unconnected buses and generate "Virtual Measurements" for $P=0$ and $Q=0$.

**Accuracy:** These are mathematical certainties, not physical measurements. Therefore, they should be assigned a very low standard deviation (e.g., $10^{-6}$ p.u.).

**Importance:** Including these virtual measurements significantly improves the redundancy and accuracy of the estimation without requiring additional physical hardware.

## 8. Time-Series and Quasi-Dynamic Simulation

For analyzing the impact of AMI on grid operations over time (e.g., daily voltage regulation), the simulator uses the `pandapower.timeseries` module.

### 8.1 The Simulation Loop

The core execution engine follows a specific sequence, defined in the `run_timeseries` function.

**Time Step Initialization:** The loop advances to time $t$.

**Controller Action:** ConstControl reads data from DataSource and updates `net.load.p_mw`.

**Smart Meter Feedback (Optional):** If the simulation involves closed-loop control (e.g., a Volt/Var optimization agent relying on AMI), the simulator must execute an intermediate "Measurement & Estimation" step before calculating the final state.

**Advanced Loop:**

1. Set Loads (Physical Reality)
2. Solve Power Flow (Physical Reality)
3. Generate Measurements (AMI feedback)
4. Run State Estimation (Controller view)
5. Adjust Controls (e.g., Trafo Tap) based on Estimated State
6. Re-solve Power Flow (Final State)

**Result Storage:** OutputWriter saves variables to disk.

### 8.2 Performance Considerations

Simulating a year of 15-minute data (35,040 steps) for a large grid is computationally intensive.

**Numba Compilation:** The simulator must enable the numba backend for the Jacobian construction in pandapower. This typically yields a 10x-50x speedup.

**Recycling:** If the topology is static (only loads change), the structure of the Jacobian and Y-bus matrices remains constant. The spec should utilize `pp.runpp(..., recycle={'Ybus': True, 'trafo': True})` to avoid redundant recalculations.

## 9. Co-Simulation Architectures

Smart Grid analysis often requires simulating the communication network alongside the power grid. Pandapower focuses on physics; frameworks like Mosaik and OPEN orchestrate the co-simulation.

### 9.1 Integration with Mosaik

Mosaik connects independent simulators (step-based execution). The mosaik-pandapower adapter is the bridge.

**Architecture:** The smart meter is modeled as an entity in the Mosaik scenario definition.

**Attribute Mapping:**
- **Input to Pandapower:** P, Q[MVar] (driven by a household demand simulator like a CSV reader or a thermal model)
- **Output from Pandapower:** Vm[pu], Va[deg], Loading[%]. The smart meter entity "reads" these values from the grid solution

**Synchronization:** Mosaik handles the `step()` coordination. The simulator spec must define the "step size" (e.g., 900 seconds). If the communication simulator runs at a faster rate (e.g., 1 second for packet routing), Mosaik handles the data exchange scheduling.

### 9.2 Integration with OPEN

The Open Platform for Energy Networks (OPEN) provides a higher-level abstraction for Smart Local Energy Systems (SLES).

**Asset Class:** In OPEN, the smart meter is not a standalone element but an interface of the Asset class.

**Functionality:** The Asset class manages the time-series profile (`self.P_profile`). The simulator uses the EnergySystem class to coordinate the PandapowerNet object.

**Market Integration:** OPEN allows the smart meter data to drive market models (e.g., peer-to-peer trading). The simulator spec for OPEN integration requires defining Market objects that read the Asset's metered power to settle financial transactions.

### 9.3 Cyber-Security Simulation Specification

A complete Smart Grid Simulator must handle cyber-threats.

**False Data Injection (FDI):** The simulator must support an "Attacker Agent."

**Mechanism:** The agent intercepts the measurement array passed to the State Estimator.

**Attack Vector:** $z_{attack} = z_{true} + a$, where $a$ is the attack vector.

**Stealth:** The agent calculates $a$ such that it aligns with the system topology (state attack), attempting to bypass the Chi-squared test.

**Simulator Requirement:** The architecture must expose the measurement array as a writable buffer between the generation step and the estimation step to allow the Attacker Agent to modify it.

## 10. Use Case Specifications

This section defines standard test procedures to validate the smart meter implementation.

### 10.1 Voltage Violation Analysis

**Objective:** Validate that smart meter data correctly identifies over/under-voltage conditions.

**Procedure:**
1. Introduce a high PV generation scenario causing voltage rise
2. Simulate smart meters with varying accuracy classes (0.5 vs 2.0)
3. Run SE and compare the estimated max voltage against the limit (1.05 p.u.)

**Metric:** False Positive/Negative Rate of violation detection. A Class 2.0 meter might miss a violation that is marginally above the limit (1.051 p.u.) due to negative error bias.

### 10.2 Technical Loss Calculation

**Objective:** Estimate grid losses using AMI data.

**Challenge:** Losses are the difference between substation injection and the sum of all load meters.

$$P_{loss} = P_{sub} - \sum P_{meters}$$

**Error Propagation:** Small errors in individual meters accumulate. If $\sum P_{meters}$ has a large cumulative error, the calculated loss can be wildly inaccurate (even negative).

**Spec:** The simulator must provide a statistical "Loss Confidence Interval" calculation based on the $\sigma$ of the meters, demonstrating why high-precision meters are required for loss analysis.

## 11. Future Trends and Standards

### 11.1 CIM Interoperability

The Common Information Model (IEC 61970/61968) is the global standard for grid data exchange.

**Requirement:** The simulator should support CIM import/export.

**Mapping:**
- CIM UsagePoint $\leftrightarrow$ Pandapower Logical Smart Meter
- CIM Analog measurement $\leftrightarrow$ Pandapower measurement row
- CIM EnergyConsumer $\leftrightarrow$ Pandapower load

**Tools:** Use `pandapower.converter.cim` or external tools like CIMpy to facilitate this translation.

### 11.2 PMU Integration

While this report focuses on AMI, the future grid includes Phasor Measurement Units (PMUs). PMUs measure Voltage Angle (va) directly and precisely. The SE algorithm should support "Hybrid State Estimation" for these high-speed streams.

## 12. Advanced Grid Intelligence (Phase 6-22)

The simulator is now equipped with orchestration logic for high-penetration renewable grids.

### 12.1 Nodal Marginal Pricing (LMP)
Locational Marginal Pricing is calculated based on:
1. **Energy Component:** System-wide clearing price.
2. **Congestion Component:** Marginal cost of active constraints (line loading).
3. **Loss Component:** Nodal loss sensitivities derived from the Jacobian.

### 12.2 Virtual Power Plant (VPP) Orchestration
The VPP logic coordinates distributed assets (Smart Meters, Batteries, EV Chargers) to provide:
- **Frequency Response:** Fast active power adjustment based on frequency deviation.
- **Balancing Services:** Aggregated surplus/deficit offsets to maintain target exchange at the substation.

### 12.3 Carbon Intensity Tracking
Real-time environmental metrics are derived from:
- **Grid Mix:** Dynamic tracking of the "External Grid" carbon profile.
- **Imbalance Mixing:** Nodal carbon intensity calculation based on energy flow mixing from different sources.
