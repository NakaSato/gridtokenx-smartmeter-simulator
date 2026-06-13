# Mathematical Formulation of the GridTokenX Smart Meter Simulator

**A reference for the device, load, and power-flow models implemented in the backend.**

> Scope. This document gives the governing equations for every model the
> per-tick simulation evaluates: photovoltaic generation, ZIP load response,
> behind-the-meter storage, primary frequency response, the AC power-flow
> solver, IEEE 1547 inverter controls (volt-VAR / volt-watt), the distribution
> transformer with on-load tap changer, and the approximate DistFlow fallback.
> Each equation cites the source line that implements it
> (`file:line`), so the formulation is verifiable, not asserted.
> Notation is SI unless stated; per-unit (pu) quantities are dimensionless.
>
> Companion docs: [`data-pipeline-methodology.md`](data-pipeline-methodology.md)
> (how data flows through these models), [`data-pipeline-and-model-usage.md`](data-pipeline-and-model-usage.md)
> (running/configuring them), [`backend-core-features-academic-report.md`](backend-core-features-academic-report.md)
> (prose feature framing), [`references.bib`](references.bib) (citations). Index:
> [`README.md`](README.md).

---

## 1. Simulation model overview

The simulator advances a discrete tick of length $\Delta t$ (seconds), with
the per-tick interval in hours

$$
h = \frac{\Delta t}{3600}.
$$

At each tick $k$ the engine evaluates, in order:

1. per-meter device models → energy readings $(E^{\mathrm{gen}}_m, E^{\mathrm{con}}_m)$ for every meter $m$;
2. the feeder power flow → bus voltages $V_b$, line flows, losses;
3. the system frequency update $f_{k+1}$ from the aggregate imbalance, fed back to the meters for the next tick (one-tick governor lag).

Symbols used throughout:

| Symbol | Meaning | Unit |
| --- | --- | --- |
| $P^{\mathrm{gen}}, P^{\mathrm{con}}$ | meter generation / consumption power | kW |
| $V$ | voltage magnitude (per unit unless noted) | pu / V |
| $f$ | system frequency | Hz |
| $S_n$ | inverter apparent-power rating | kVA |
| $Q$ | reactive power | kvar |
| $\mathrm{SoC}$ | battery state of charge | kWh |
| $R, X$ | line series resistance / reactance | $\Omega$ |

---

## 2. Photovoltaic generation

The backend has two PV models: a physics-based `pvlib`/PVWatts chain (default,
`pv_model_enabled`) and a sinusoidal-profile fallback.

### 2.1 Physics-based model (PVWatts via `pvlib`)

*Source: `devices/solar.py:51`–`112`.*

Plane-of-array (POA) irradiance is computed from the Ineichen clear-sky model
and the solar position for the meter's latitude/longitude at the local
wall-clock time, then derated by a discrete weather factor $w$
(`devices/solar.py:10`–`18`):

$$
G_{\mathrm{POA}}^{\mathrm{eff}} = w \cdot G_{\mathrm{POA}}^{\mathrm{global}},
\qquad
w \in \{1.0,\ 0.72,\ 0.42,\ 0.18,\ 0.10,\ 0.05\}.
$$

Cell temperature uses the NOCT-style linear rise on POA
(`solar.py:94`):

$$
T_{\mathrm{cell}} = T_{\mathrm{amb}} + \frac{G_{\mathrm{POA}}^{\mathrm{eff}}}{800}\cdot 20\ \ [^\circ\mathrm{C}].
$$

DC power follows the PVWatts module model (`solar.py:95`–`107`) with nameplate
$P_{dc0}$ and temperature coefficient $\gamma_{pdc}$ (typ. $-0.004\,/^\circ\mathrm{C}$):

$$
P_{dc} = \frac{G_{\mathrm{POA}}^{\mathrm{eff}}}{1000}\, P_{dc0}
\left[\, 1 + \gamma_{pdc}\,(T_{\mathrm{cell}} - 25)\,\right].
$$

AC power applies the PVWatts inverter model with a DC/AC ratio $\rho$, clamped
to nameplate (`solar.py:108`–`112`):

$$
P^{\mathrm{gen}}_{\mathrm{PV}} = \min\!\Big(P_{dc0},\ \eta_{\mathrm{inv}}(P_{dc})\,\Big),
\qquad
P_{dc0,\mathrm{ac}} = \frac{P_{dc0}}{\rho}.
$$

A first-order autoregressive (AR(1)) measurement noise rides on the output
(`solar.py:40`–`42`):

$$
n_k = 0.8\,n_{k-1} + \varepsilon_k,\quad
\varepsilon_k \sim \mathcal N\!\big(0,\,(0.01\,P^{\mathrm{gen}})^2\big),
\qquad
\hat P^{\mathrm{gen}} = \max(0,\ P^{\mathrm{gen}} + n_k).
$$

### 2.2 Sinusoidal fallback profile

*Source: `core/meter_logic/profiles.py:8`–`34`.* For daylight hour
$t \in [6, 18]$ with capacity $C$:

$$
P^{\mathrm{gen}}_{\mathrm{PV}}(t)
= \max\!\Big(0,\ C\,\sin^2\!\Big(\tfrac{\pi (t-6)}{12}\Big)\, w \;+\; n_k\Big),
\qquad
n_k = 0.8\,n_{k-1} + \varepsilon_k,
$$

and zero outside daylight. The $\sin^2$ shape places the peak at solar noon
($t=12$).

---

## 3. Load model

### 3.1 Time-of-day demand profile

*Source: `profiles.py:37`–`88`.* Base demand $P_0$ is shaped by a
meter-type-dependent factor $\phi(t)$. For residential/prosumer meters a
double-Gaussian captures the morning and evening peaks, with a per-meter phase
offset $\delta \in [0,1)$ (deterministic hash of meter id):

$$
g_{\mathrm{m}}(t) = 0.8\,\exp\!\Big(-\tfrac{(t - (7.5 + 1.5\delta))^2}{2\cdot 1.2^2}\Big),
\qquad
g_{\mathrm{e}}(t) = 1.5\,\exp\!\Big(-\tfrac{(t - (18.5 + 2.0\delta))^2}{2\cdot 2.5^2}\Big),
$$

$$
\phi_{\text{weekday}}(t) = 0.6 + g_{\mathrm{m}}(t) + g_{\mathrm{e}}(t).
$$

Commercial meters use a business-hours plateau (`profiles.py:64`–`73`). AR(1)
noise (coefficient $0.85$, $\sigma = 0.015\,P$) is added and the result clamped
to $[P_{\min}, P_{\max}]$.

### 3.2 ZIP voltage dependence

*Source: `devices/load.py:45`–`63`.* The profile demand $P_0$ is the
nominal-voltage value; actual draw depends on bus voltage $V$ (pu) through the
**ZIP** model — a convex mix of constant-impedance ($Z\sim V^2$),
constant-current ($I\sim V$), and constant-power ($P\sim V^0$) components with
normalized fractions $a_Z + a_I + a_P = 1$:

$$
\boxed{\;P^{\mathrm{con}}(V) = P_0\,\big(a_Z V^2 + a_I V + a_P\big)\;}
\qquad V \in [0,\ 1.5].
$$

Setting $(a_Z, a_I, a_P) = (0,0,1)$ recovers a stiff constant-power load.

---

## 4. Behind-the-meter battery storage (BESS)

*Source: `devices/battery.py`.* A self-consumption strategy charges from PV
surplus and discharges to cover the household deficit. Let
$P_{\mathrm{net}} = P^{\mathrm{gen}} - P^{\mathrm{con}}$ be the pre-battery
balance and let the round-trip efficiency split evenly per leg,
$\eta = \sqrt{\eta_{\mathrm{rt}}}$ (`battery.py:40`).

**Charging** ($P_{\mathrm{net}} > 0$), bounded by C-rate $\bar P_c$ and headroom
(`battery.py:62`–`73`):

$$
P_c = \min\!\Big(\bar P_c,\ P_{\mathrm{net}},\ \frac{C - \mathrm{SoC}}{h\,\eta}\Big),
\qquad
\mathrm{SoC} \mathrel{+}= P_c\,h\,\eta.
$$

**Discharging** ($P_{\mathrm{net}} < 0$), bounded by C-rate $\bar P_d$ and usable
energy above the floor (`battery.py:75`–`87`):

$$
P_d = \min\!\Big(\bar P_d,\ -P_{\mathrm{net}},\ \frac{(\mathrm{SoC} - \mathrm{SoC}_{\min})\,\eta}{h}\Big),
\qquad
\mathrm{SoC} \mathrel{-}= \frac{P_d\,h}{\eta}.
$$

The asymmetric $\eta$ placement (multiply on charge, divide on discharge)
encodes that only $\eta$ of drawn energy is stored and $1/\eta$ must be drawn to
deliver a unit — total round-trip loss $1-\eta^2 = 1-\eta_{\mathrm{rt}}$.
Charge power adds to `energy_consumed`, discharge to `energy_generated`.

---

## 5. Primary frequency response

### 5.1 System frequency from imbalance

*Source: `core/engine.py:288`–`296`.* Each tick the aggregate generation and
load set a normalized imbalance ratio

$$
r = \mathrm{clip}\!\left(\frac{\sum_m E^{\mathrm{gen}}_m - \sum_m E^{\mathrm{con}}_m}{\max\!\big(\sum_m E^{\mathrm{gen}}_m,\ \sum_m E^{\mathrm{con}}_m,\ \epsilon\big)},\ -1,\ 1\right),
$$

and the system frequency swings about nominal by at most $\Delta f_{\max}$
(`FREQ_FULL_SWING_HZ`):

$$
f_{k+1} = f_{\mathrm{nom}} + \Delta f_{\max}\, r.
$$

External telemetry frequency, when present, is re-applied first each tick and
stays authoritative.

### 5.2 Frequency-watt droop (export throttle)

*Source: `core/meter_logic/electrical.py:6`–`16`.* With per-unit frequency
deviation $\Delta f_{\mathrm{pu}} = (f - 50)/50$ and a 50 mHz deadband, a droop
gain of 20 (i.e. 5% droop) scales generation, clamped to $\pm20\%$:

$$
P^{\mathrm{gen}} \leftarrow P^{\mathrm{gen}}\,\big(1 + \alpha\big),
\qquad
\alpha = \mathrm{clip}\!\big(-20\,\Delta f_{\mathrm{pu}},\ -0.2,\ 0.2\big),
\quad |\Delta f_{\mathrm{pu}}| > 0.001.
$$

Over-frequency ($\Delta f_{\mathrm{pu}}>0$, surplus) throttles export down;
under-frequency raises it — the frequency-watt primary-response loop. Note the
implementation references 50 Hz nominal in `electrical.py`; the engine's
`FREQ_NOMINAL_HZ` is configurable.

---

## 6. AC power flow (exact solver)

*Source: `core/grid_manager.py:375`–`614`.* Each tick the meter readings are
aggregated to per-bus net injections and a pandapower network is solved.

### 6.1 Bus injections

For bus $b$ aggregating meters $m \in b$ with interval $h$
(`grid_manager.py:298`–`315`):

$$
P_b = \sum_{m\in b}\frac{E^{\mathrm{con}}_m - E^{\mathrm{gen}}_m}{h},
\qquad
P^{\mathrm{gen}}_b = \sum_{m\in b}\frac{E^{\mathrm{gen}}_m}{h}.
$$

Reactive injection comes from the reading's reactive power if present, else from
the power factor $\mathrm{pf}$ (`grid_manager.py:367`–`373`):

$$
Q_b = \mathrm{sgn}(P_b)\,|P_b|\,\frac{\sqrt{1-\mathrm{pf}^2}}{\mathrm{pf}}.
$$

### 6.2 Network equations and solution algorithm

The solver enforces the standard AC power-flow balance at every bus,

$$
P_b = V_b \sum_{j} V_j\big(G_{bj}\cos\theta_{bj} + B_{bj}\sin\theta_{bj}\big),
\qquad
Q_b = V_b \sum_{j} V_j\big(G_{bj}\sin\theta_{bj} - B_{bj}\cos\theta_{bj}\big),
$$

where $\theta_{bj} = \theta_b - \theta_j$ and $Y = G + jB$ is the bus admittance
matrix. Because LV radial feeders at a 230 V base have high per-unit impedance
that diverges plain Newton-Raphson, the solver tries **backward/forward sweep
(`bfsw`)** first, then NR with a DC seed (`grid_manager.py:428`–`438`):

$$
\text{solve order: } \texttt{bfsw} \to \texttt{nr(init=dc)} \to \text{DistFlow fallback (§9)}.
$$

Line series loss is $P^{\mathrm{loss}}_\ell = I_\ell^2 R_\ell$ (pandapower
`res_line.pl_mw`), summed with the transformer loss for the system total
(`grid_manager.py:604`–`613`).

### 6.3 Three-phase base scaling

GLM nominal voltage is line-to-neutral; pandapower expects line-to-line. A
3-phase bus is scaled by $\sqrt 3$ (`grid_manager.py:170`–`173`):

$$
V_{n,\mathrm{LL}} = \begin{cases} \sqrt 3\, V_{n,\mathrm{LN}} & \text{3-phase (ABC)} \\ V_{n,\mathrm{LN}} & \text{otherwise.}\end{cases}
$$

---

## 7. IEEE 1547 inverter voltage controls

Two smart-inverter functions run **inside** the power-flow fixed-point loop,
reactive (volt-VAR) first, then real-power curtailment (volt-watt) — a
sequential, not co-optimized, control order.

### 7.1 Volt-VAR — $Q(V)$ reactive support

*Source: `grid_manager.py:269`–`285`, `479`–`520`.* Each PV inverter follows a
piecewise-linear $Q(V)$ curve with four pu breakpoints $v_1<v_2<v_3<v_4$ and a
$[v_2,v_3]$ deadband, returning a factor $\kappa \in [-1,1]$ (load convention:
$-1$ full injection, $+1$ full absorption):

$$
\kappa(V) =
\begin{cases}
-1 & V \le v_1 \\[2pt]
-\dfrac{v_2 - V}{v_2 - v_1} & v_1 < V < v_2 \\[6pt]
0 & v_2 \le V \le v_3 \quad(\text{deadband})\\[4pt]
\dfrac{V - v_3}{v_4 - v_3} & v_3 < V < v_4 \\[6pt]
+1 & V \ge v_4 .
\end{cases}
$$

The reactive command is bounded by inverter headroom and a fraction of the
apparent rating $S_n = P_{\mathrm{nameplate}}\cdot(\text{oversize})$
(`grid_manager.py:496`–`508`):

$$
Q^{\max}_b = \min\!\Big(\underbrace{\sqrt{S_n^2 - P_b^2}}_{\text{headroom}},\ q_{\mathrm{frac}}\,S_n\Big),
\qquad
Q_b^{\mathrm{VV}} = \kappa(V_b)\,Q^{\max}_b .
$$

Iterated to a fixed point: $Q_b^{\mathrm{VV}}$ is added to the bus reactive load,
the network re-solved, until $|\Delta Q| \le 10^{-3}$.

### 7.2 Volt-watt — $P(V)$ real-power curtailment

*Source: `grid_manager.py:522`–`563`.* An exporting bus above $v_{\mathrm{start}}$
linearly curtails its inverter real power to zero at $v_{\mathrm{end}}$:

$$
\beta(V) =
\begin{cases}
1 & V \le v_{\mathrm{start}} \\[2pt]
\dfrac{v_{\mathrm{end}} - V}{v_{\mathrm{end}} - v_{\mathrm{start}}} & v_{\mathrm{start}} < V < v_{\mathrm{end}} \\[6pt]
0 & V \ge v_{\mathrm{end}},
\end{cases}
\qquad
P^{\mathrm{curtail}}_b = P^{\mathrm{gen}}_b\,(1 - \beta(V_b)).
$$

Only the generation component is curtailed; the curtailed kW is added back to
net load $P_b$. The per-bus curtailment is **ratcheted** (monotone non-decreasing
within a tick) to damp the limit-cycle oscillation an undamped curve produces,
guaranteeing convergence to the settled operating point.

---

## 8. Distribution transformer and OLTC

*Source: `grid_manager.py:206`–`245`, `446`–`477`.* When `TRANSFORMER_ENABLED`,
an MV external-grid slack (22 kV) feeds the LV substation bus through a real
two-winding transformer characterized by its short-circuit and iron-loss
parameters $(S_n, v_k\%, v_{kr}\%, P_{fe}, i_0\%)$. The slack moves upstream, so
the LV head sags under load and rises on PV backfeed across the transformer
series impedance instead of being a stiff 1.0 pu source.

**On-load tap changer (OLTC).** Before the volt-watt pass, the HV-side tap
position $\tau$ is stepped to hold the LV head $V_{\mathrm{LV}}$ at target
$V^\*$ within deadband $\delta$ (`grid_manager.py:462`–`477`):

$$
\tau \leftarrow \mathrm{clip}\big(\tau + \mathrm{sgn}(V_{\mathrm{LV}} - V^\*),\ \tau_{\min},\ \tau_{\max}\big),
\qquad
\text{ratio } = 1 + \tau\,\frac{\Delta_{\mathrm{step}}\%}{100},
$$

re-solving until $|V_{\mathrm{LV}} - V^\*| \le \delta$ or the tap saturates. Tap
on the HV side: raising $\tau$ adds HV turns and lowers $V_{\mathrm{LV}}$. The
tap absorbs bulk voltage; curtailment (§7.2) then handles only residual local
overvoltage.

> Implementation note: pandapower 3.3 `bfsw` errors on a non-neutral tap, so a
> tapped solve transparently falls through to NR; the transformer is created
> with `tap_changer_type="Ratio"` so the tap ratio is actually applied
> (`grid_manager.py:239`).

---

## 9. Approximate DistFlow fallback

*Source: `grid_manager.py:622`–`674`.* When the exact solve fails to converge
(e.g. voltage collapse under overload), the simulator falls back to a linearized
**DistFlow** sweep over the radial tree rooted at the substation. Downstream
real/reactive power is accumulated by a reverse topological pass, then the
voltage drop across each branch $(p,c)$ with impedance $(R, X)$ uses the
LinDistFlow approximation:

$$
\Delta V_{\mathrm{pu}} = \frac{P_c R + Q_c X}{V_{\mathrm{nom}}^2},
\qquad
V_c = \mathrm{clip}\big(V_p - \Delta V_{\mathrm{pu}},\ 0.7,\ 1.2\big).
$$

Branch current-squared and series loss (`grid_manager.py:655`–`663`):

$$
I^2 = \frac{(P_c)^2 + (Q_c)^2}{(V_p V_{\mathrm{nom}})^2},
\qquad
P^{\mathrm{loss}} = \min\!\big(I^2 R,\ |P_c|\big).
$$

The $\min$ enforces the physical bound that series $I^2R$ loss cannot exceed the
power flowing through the branch — needed because the LV base inflates currents.

---

## 10. Fault / outage injection (N-1 contingency)

*Source: `grid_manager.py:353`–`365`, `385`–`398`, `565`–`577`.* Faulted lines
and buses are flagged out of service before each solve (and removed from the
DistFlow graph), so the radial feeder reroutes or **islands**. A bus with no
energized path to the slack is de-energized:

$$
V_b = 0 \quad \text{if } b \text{ faulted, or } b \notin \mathrm{Reach}(\text{slack}),
$$

and in-service de-energized buses are reported as `islanded_buses`. This models
resilience / N-1 contingency studies, recomputed every tick.

---

## 11. Measurement model (DLMS/COSEM egress)

*Source: `core/meter_logic/electrical.py:19`–`75`.* Voltage, current, power
factor, and reactive power surface on each reading with accuracy-class Gaussian
noise $\mathcal N(x, (\text{class}/300)\,|x|)$. Apparent power and current:

$$
S = \frac{|P_{\mathrm{net}}|}{\mathrm{pf}},
\qquad
I = \frac{1000\,S}{V},
\qquad
Q = P_{\mathrm{net}}\,\frac{\sqrt{1-\mathrm{pf}^2}}{\mathrm{pf}},
$$

with current signed negative on export ($P_{\mathrm{net}}<0$). These OBIS-coded
quantities are signed (Ed25519) and exported to the Aggregator Bridge over the
DLMS/COSEM (IEC 62056) REST contract.

---

## Appendix A — Model-to-code map

| Model | Equation(s) | Source |
| --- | --- | --- |
| PVWatts PV | §2.1 | `devices/solar.py:51`–`112` |
| Sinusoidal PV | §2.2 | `core/meter_logic/profiles.py:8`–`34` |
| Load profile | §3.1 | `core/meter_logic/profiles.py:37`–`88` |
| ZIP voltage response | §3.2 | `devices/load.py:45`–`63` |
| Battery dispatch | §4 | `devices/battery.py:51`–`89` |
| Frequency imbalance | §5.1 | `core/engine.py:288`–`296` |
| Frequency-watt droop | §5.2 | `core/meter_logic/electrical.py:6`–`16` |
| AC power flow | §6 | `core/grid_manager.py:375`–`614` |
| Volt-VAR $Q(V)$ | §7.1 | `core/grid_manager.py:269`–`285`, `479`–`520` |
| Volt-watt $P(V)$ | §7.2 | `core/grid_manager.py:522`–`563` |
| Transformer + OLTC | §8 | `core/grid_manager.py:206`–`245`, `446`–`477` |
| DistFlow fallback | §9 | `core/grid_manager.py:622`–`674` |
| Fault injection | §10 | `core/grid_manager.py:353`–`398` |
| Measurement / DLMS | §11 | `core/meter_logic/electrical.py:19`–`75` |

## Appendix B — Selected references

- M. E. Baran and F. F. Wu, "Network reconfiguration in distribution systems
  for loss reduction and load balancing," *IEEE Trans. Power Delivery*, 1989.
  (DistFlow, §9)
- IEEE Std 1547-2018, *IEEE Standard for Interconnection and Interoperability of
  Distributed Energy Resources*. (Volt-VAR / volt-watt, §7)
- A. P. Dobos, *PVWatts Version 5 Manual*, NREL/TP-6A20-62641, 2014. (§2.1)
- P. Ineichen and R. Perez, "A new airmass independent formulation for the
  Linke turbidity coefficient," *Solar Energy*, 2002. (clear-sky, §2.1)
- IEC 62056 (DLMS/COSEM) suite. (Measurement egress, §11)
- pandapower: L. Thurner et al., "pandapower — An Open-Source Python Tool for
  Convenient Modeling, Analysis, and Optimization of Electric Power Systems,"
  *IEEE Trans. Power Systems*, 2018. (§6)

---

*Generated from source. Citations are `file:line` into
`backend/src/smart_meter_simulator/`; re-verify against the tree before publishing.*
