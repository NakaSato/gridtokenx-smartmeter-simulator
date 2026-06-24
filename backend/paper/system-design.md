# System Design

## 4.x The AMI Simulator as a Settlement-Data Source

<!-- บ้านหลักของ simulator — section อื่นอ้างกลับมาที่นี่ -->

GridTokenX Simulator ถูกออกแบบให้ทำหน้าที่สองประการพร้อมกัน: เป็น **แหล่งข้อมูล telemetry** ที่ผ่าน physical validation สำหรับ settlement pipeline และเป็น **แพลตฟอร์มทดสอบแบบ reproducible** สำหรับการประเมินสถานการณ์ต่าง ๆ ทั้งสองบทบาทใช้ implementation เดียวกัน ความแตกต่างอยู่ที่ egress path เท่านั้น

### 4.x.1 สถาปัตยกรรมภาพรวม

ระบบพัฒนาด้วย Python 3.11 บน FastAPI (พอร์ต 8082) จัดการ dependency ด้วย uv การไหลของข้อมูลในแต่ละ tick:

```
SimulationEngine.tick()
  ├── ReadingManager.generate_all()     [asyncio.to_thread — CPU-bound]
  │     └── SmartMeter.generate_reading()
  │           ├── Load (ZIP model)
  │           ├── Solar (pvlib)
  │           └── electrical.py (Volt-Watt droop, ZIP sensitivity, noise)
  └── GridManager.update_grid_state()  [pandapower AC power flow]
        ├── Volt-VAR pass (Q(V) iterate to fixed point)
        ├── Volt-Watt pass (P curtailment iterate to fixed point)
        ├── OLTC tap adjustment (if enabled)
        └── Fault / islanding / switch state applied before solve
```

`SimulationEngine` (`core/engine.py`) เป็น process-global singleton ที่ router ทั้งหมดเข้าถึงผ่าน `core/app_state.engine` ไม่มี per-request state

### 4.x.2 โมเดลโทโพโลยี: GridTopology

โครงสร้างโครงข่ายแทนด้วย dataclass `GridTopology` (`core/topology.py`) ที่ประกอบด้วย `GridBus`, `GridLine`, `GridLoad`, `GridPV`, `GridTransformer` และ `ZoneSpec` โทโพโลยีอ่านจากไฟล์ GridLAB-D GLM ผ่าน adapter (`adapters/glm_topology_loader.py`) ซึ่งแปลง object ประเภท `node`, `overhead_line`, `transformer`, `switch`, `load`, `solar` และ `inverter` ให้อยู่ในรูปแบบ neutral `GridTopology`

`GridBus` ถือ `zone_code` (integer) สำหรับการแบ่งโซน microgrid ซึ่งถูกกำหนดจาก `groupid` ของ GLM (cascade: int groupid → trailing digits → load-order counter) ค่านี้ถูกส่งใน OBIS payload และใช้ใน bridge เพื่อ route telemetry ไปยัง Redis Stream `gridtokenx:events:zone_<n>`

### 4.x.3 Physics-Based Power Flow

`GridManager` (`core/grid_manager.py`) สร้าง pandapower network จาก `GridTopology` แล้วแก้ไขทุก tick ตามลำดับ:

**ขั้นที่ 1 — Backward/Forward Sweep (bfsw):** เหมาะสำหรับสายส่งแบบรัศมี (radial LV feeders) ซึ่งเป็นโครงสร้างปกติของระบบจำหน่ายในไทย

**ขั้นที่ 2 — Newton-Raphson fallback:** ทดลองหาก bfsw ไม่ converge หรือมี non-neutral tap (pandapower 3.3 มีข้อจำกัดกับ bfsw บน tapped transformer — ดูหัวข้อ Discussion)

**ขั้นที่ 3 — DistFlow approximation:** หาก pandapower ไม่ converge ในทั้งสองวิธี (เช่น voltage collapse ภายใต้โหลดสูงเกิน) ระบบสลับมาใช้ DistFlow sweep บน NetworkX graph โดยอัตโนมัติ

**หม้อแปลงจำหน่าย:** เมื่อ `TRANSFORMER_ENABLED=true` ระบบสร้าง MV/LV distribution transformer ที่หัวสาย (MV 22 kV → LV bus) ทำให้ LV voltage ตกภายใต้โหลดและสูงขึ้นเมื่อ PV export ผ่านอิมพีแดนซ์จริง

**On-Load Tap Changer (OLTC):** เมื่อ `TRANSFORMER_OLTC_ENABLED=true` ระบบก้าว tap ฝั่ง HV ก่อน Volt-Watt pass เพื่อรักษา LV head voltage ภายใน deadband รอบ target ทำให้ OLTC จัดการ bulk voltage และ curtailment จัดการ residual local overvoltage เท่านั้น

### 4.x.4 IEEE 1547 Smart Inverter Control

ระบบ implement การควบคุม inverter สองชั้นตาม IEEE Std 1547-2018 [REF] โดยทำงานแบบ **sequential** ไม่ใช่ co-optimized:

**Volt-VAR (Q(V) Control) — ชั้นแรก:**

Inverter แต่ละตัวติดตาม piecewise Q(V) curve ตามจุด breakpoint สี่ค่า (v1=0.92, v2=0.98, v3=1.02, v4=1.08 pu) โดย:

$$Q_i(V) = \begin{cases} -Q_{\max,i} & V \leq v_1 \\ -Q_{\max,i}\cdot\frac{v_2 - V}{v_2 - v_1} & v_1 < V \leq v_2 \\ 0 & v_2 < V \leq v_3 \\ Q_{\max,i}\cdot\frac{V - v_3}{v_4 - v_3} & v_3 < V \leq v_4 \\ Q_{\max,i} & V > v_4 \end{cases}$$

โดย $Q_{\max,i} = \min\!\bigl(q\_\text{max\_frac}\cdot S_{n,i},\;\sqrt{S_{n,i}^2 - P_i^2}\bigr)$ และ $S_{n,i}$ คือ apparent rating ของ inverter (IEEE 1547 Category B: $q\_\text{max\_frac} = 0.44$)

**Volt-Watt (P(V) Control) — ชั้นที่สอง:**

หากแรงดัน bus ยังเกิน $V_{\text{start}}$ (1.06 pu) หลัง Volt-VAR ระบบลด real-power export เป็นเส้นตรง:

$$P_{\text{export},i}(V) = P_{\text{rated},i} \cdot \max\!\left(0,\; \frac{V_{\text{end}} - V}{V_{\text{end}} - V_{\text{start}}}\right)$$

ทั้งสองชั้น iterate ถึง fixed point ภายใน tick เดียวกัน (`PV_VOLTWATT_MAX_ITER` รอบ)

### 4.x.5 Device Models

**SmartMeter** (`devices/ami.py`) ประกอบด้วย:

- **Load (ZIP model):** $P_{\text{load}} = P_0\bigl(Z\cdot V^2 + I\cdot V + P\bigr)$ ตามสัดส่วน ZIP fraction ที่กำหนดในการตั้งค่า แสดงถึง voltage sensitivity ของโหลดจริง
- **Solar (pvlib):** คำนวณกำลังผลิตจาก plane-of-array irradiance โดยคำนึงถึงมุมเอียง (tilt=15°) ทิศ (azimuth=180°) อุณหภูมิ temperature coefficient และ DC/AC ratio
- **Frequency-Watt Droop:** ปรับ export ตาม frequency deviation: $\Delta P = -20 \cdot \frac{f - 50}{50} \cdot P_{\text{rated}}$ โดยมี deadband ±50 mHz

per-meter noise stream สร้างจาก $\text{seed}_i = s_{\text{global}} \oplus \text{SHA-256}(\text{meter\_id})_{[:8]}$ รับประกัน determinism และความเป็นอิสระระหว่างมิเตอร์

### 4.x.6 Microgrid Zone Control และ Fault Injection

**ZoneController** (`core/zone_manager.py`) จัดการการ island/reconnect โซน microgrid ผ่าน runtime API:

- `island(code)` — เปิด PCC transformer ของโซน (ผ่าน `faulted_transformers`) โซนที่มี DER bus ได้รับ temporary local `ext_grid` slack ทำให้รักษาแรงดันได้ตลอดโซน โซนที่ไม่มี DER จะดับ
- `reconnect(code)` — นำ PCC transformer กลับเข้าบริการ island slack ถูกลบทันที
- **Per-zone frequency:** โซนที่ island decouples ความถี่ไปยัง balance ของสมาชิกเอง ส่วนโซนที่ connect อยู่ใช้ system frequency (backward-compatible)

**Fault injection** รองรับ `line`, `bus`, และ `transformer` สำหรับ N-1 contingency study `islanded_buses` คำนวณใหม่ทุก tick จาก graph reachability

**Tie-switch** (`GridLine` ที่มี `is_switch=True`) ควบคุมผ่าน `/api/v1/simulation/switches/{name}/close|open` สำหรับการโอนโหลดระหว่างโซน

### 4.x.7 Demand Response Controller

`DemandResponseController` (`core/demand_response.py`) จัดการ load-shed events ที่กำหนดผ่าน API แต่ละ event มีช่วงเวลา `[start, end)` บน simulation clock, `reduction_fraction`, และ optional `target_meter_types` + `target_zones` (AND filter) Event ที่ซ้อนทับกันใช้ค่า reduction **สูงสุด** ไม่ใช่สะสม โหลดที่ลดลงส่งผล power flow solve ของ tick เดียวกัน

### 4.x.8 Thai MEA/PEA Tariff Engine

`thai_tariff.py` (`pricing/thai_tariff.py`) implement โครงสร้างค่าไฟฟ้าขายปลีก MEA/PEA สำหรับแรงดันต่ำ (<12 kV) ประกอบด้วย tariff class ห้าประเภท ได้แก่ `residential_small` (≤150 kWh/เดือน), `residential_normal` (>150 kWh/เดือน), `residential_tou`, `small_business`, และ `small_business_tou`

บิลรวม: $\text{Bill} = \bigl(E_{\text{charge}} + F_t \cdot E_{\text{total}} + \text{Service}\bigr) \times (1 + \text{VAT})$

โดย $F_t$ คือ fuel adjustment charge (ค่าเริ่มต้น 0.3672 ฿/kWh ตาม ERC ม.ค.–เม.ย. 2568) TOU period: Peak = จันทร์–ศุกร์ 09:00–22:00, Off-peak = นอกช่วง peak และวันหยุดสุดสัปดาห์

### 4.x.9 DLMS/COSEM Transport และ Ed25519 Signing

`AggregatorBridgeEmitter` (`transport/aggregator_bridge.py`) เข้ารหัส reading แต่ละตัวเป็น OBIS-code keyed JSON ตาม IEC 62056 register หลักที่ส่ง:

| OBIS Code | Register |
|---|---|
| `1.1.1.8.0.255` / `1.1.2.8.0.255` | Active energy import/export รวม (Wh) |
| `1.1.16.7.0.255` | Net active power — C=16 sum group (kW) |
| `1.1.1.6.0.255` | Max demand import rolling peak (kW) |
| `1.1.1.8.1.255` / `1.1.1.8.2.255` | TOU import peak/off-peak (Wh) |
| `0.0.96.14.0.255` | Active tariff indicator (1=peak, 2=off-peak) |
| `0.0.96.10.0.255` | DR status (1 = load-shed active) |

ทุก reading เซ็นด้วย Ed25519 private key ของมิเตอร์ตาม canonical string `device_id:kwh:timestamp_ms` และส่งผ่าน HTTP POST ไปยัง `/v1/private-network/ingest` ของ Aggregator Bridge bridge ตรวจสอบลายมือชื่อผ่าน public key ใน Redis ก่อน ingest (ดู §3.x สำหรับ chain-of-custody link)

การส่ง retry หนึ่งครั้งพร้อม jittered backoff บน transport error / 5xx ไม่ retry บน 4xx tick ที่ส่งไม่ทันจะถูก drop โดยไม่บล็อก event loop
