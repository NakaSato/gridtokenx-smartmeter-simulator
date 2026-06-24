# การออกแบบและพัฒนา GridTokenX Smart Meter Simulator

## บทคัดย่อส่วน

ส่วนนี้อธิบายสถาปัตยกรรมและการพัฒนาระบบ GridTokenX Smart Meter Simulator ซึ่งเป็นบริการจำลองมิเตอร์ไฟฟ้าอัจฉริยะ (Advanced Metering Infrastructure: AMI) แบบ GLM-backed ที่คำนวณ AC power flow จริงทุก simulation tick ผ่านเครื่องมือ pandapower [REF] พร้อมรองรับการควบคุมอินเวอร์เตอร์แบบ smart inverter ตามมาตรฐาน IEEE 1547 [REF] การแบ่งโซน microgrid การฉีดความผิดพลาด (fault injection) Demand Response (DR) และการส่งข้อมูลผ่านโปรโตคอล DLMS/COSEM (IEC 62056) [REF] ระบบพัฒนาด้วย Python 3.11 บนกรอบงาน FastAPI และจัดการ dependency ด้วย uv

---

## 1. ภาพรวมสถาปัตยกรรมระบบ

GridTokenX Smart Meter Simulator ทำหน้าที่เป็น back-end บริการ REST ที่จำลองพฤติกรรมมิเตอร์ไฟฟ้าอัจฉริยะบนโครงข่ายจริง โดยมีการไหลของข้อมูลในแต่ละ tick ดังต่อไปนี้

```
app.py (create_app)
  └── lifespan.py
        └── app_state.engine = SimulationEngine (Global Singleton)
              SimulationEngine.tick()
                ├── ReadingManager.generate_all()   ← device models (asyncio.to_thread)
                └── GridManager.update_grid_state() ← AC power flow (pandapower)
```

**SimulationEngine** (`core/engine.py`) เป็น singleton กลางที่ครอบครองรายชื่อมิเตอร์ โครงสร้างโครงข่าย ตัวจัดการการอ่านค่า วงเวียนเหตุการณ์แบบอะซิงโครนัส และสถานะเรียลไทม์ทั้งหมด ได้แก่ สถานะการทำงาน (running/paused) เวลาจำลอง (simulation clock) สภาพอากาศ (weather) และตัวคูณความเครียด (stress multiplier) ตัวเร้าเตอร์ทั้งหมดเข้าถึง engine ผ่าน `core/app_state.engine` โดยไม่มีการจัดเก็บสถานะต่อคำร้อง (per-request state)

ระบบออกแบบโดยแยก **การสร้างค่าวัด** (device models ที่ผูกกับ CPU) ออกจาก **การอัปเดตสถานะโครงข่าย** (power flow ที่ต้องการความแม่นยำสูง) โดยใช้ `asyncio.to_thread` เพื่อให้ event loop ไม่ถูกบล็อก

---

## 2. แบบจำลองโครงข่ายไฟฟ้า (Grid Modeling)

### 2.1 รูปแบบโทโพโลยี GridTopology

โครงสร้างโครงข่ายทั้งหมดแทนด้วย dataclass `GridTopology` (`core/topology.py`) ซึ่งประกอบด้วย:

- **`GridBus`** — จุดเชื่อมต่อไฟฟ้าที่มีแรงดันพิกัด เฟส และ zone_code สำหรับการแบ่งโซน microgrid
- **`GridLine`** — ขอบทิศทางระหว่าง bus สองจุด มีค่า R/X/ความจุ และแฟล็ก `is_switch`/`normally_open` สำหรับ tie-switch
- **`GridLoad`** — โหลดคงที่ที่ผูกกับ bus
- **`GridPV`** — แหล่งพลังงานโซลาร์เซลล์
- **`GridTransformer`** — หม้อแปลงไฟฟ้า (รวม OLTC)
- **`ZoneSpec`** — ข้อมูลโซน microgrid ได้แก่ PCC bus/transformer และ DER bus (bus ที่มี PV ขนาดใหญ่ที่สุดในโซน)

### 2.2 การแปลงไฟล์ GLM

ระบบอ่านโทโพโลยีจากไฟล์ GridLAB-D GLM ผ่าน `adapters/glm_converter.py` (tokenizer) และ `adapters/glm_topology_loader.py` (mapper) ซึ่งแปลง object ประเภท `node`, `overhead_line`, `underground_line`, `transformer`, `switch`, `load`, `solar` และ `inverter` ให้อยู่ในรูปแบบ `GridTopology` โดยดึง `groupid`/`zone` ของ GLM มาเป็น `zone_code` แบบตัวเลข (cascade: int groupid → ตัวเลขท้าย → ลำดับ load) และกำหนด PCC transformer กับ DER bus ต่อโซน ผ่านเมธอด `_build_zones`

### 2.3 AC Power Flow ด้วย pandapower

`GridManager` (`core/grid_manager.py`) สร้าง pandapower network จากโทโพโลยีแล้วแก้ไขทุก tick โดยใช้ลำดับดังนี้:

1. **Backward/Forward Sweep (bfsw)** — เหมาะสำหรับสายส่งแบบรัศมี (radial LV feeders) ซึ่งเป็นโครงสร้างปกติของระบบจำหน่ายแรงต่ำ
2. **Newton-Raphson (NR)** — ทดลองเป็นตัวเลือกที่สอง หากต้องการ seed จาก DC solution
3. **DistFlow fallback** — หาก pandapower ไม่ converge (เช่น voltage collapse ภายใต้โหลดสูงเกิน) ระบบจะสลับมาใช้ approximate DistFlow sweep บน NetworkX graph โดยอัตโนมัติ

**แบบจำลองหม้อแปลง:** เมื่อเปิดใช้งาน `TRANSFORMER_ENABLED` ระบบจะสร้างหม้อแปลงจำหน่ายที่หัวสาย (feeder head) ที่เชื่อมต่อ external grid แรงดันปานกลาง (MV 22 kV) กับ LV bus ผ่านอิมพีแดนซ์จริง ทำให้ LV voltage ตกภายใต้โหลดและสูงขึ้นเมื่อโซลาร์ export แทนที่จะเป็นแหล่งจ่าย stiff 1.0 pu หม้อแปลงที่ประกาศใน GLM จะถูกสร้างเสมอโดยไม่คำนึงถึง flag นี้

**On-Load Tap Changer (OLTC):** เมื่อเปิด `TRANSFORMER_OLTC_ENABLED` ระบบจะก้าวแตะ (tap) ฝั่ง HV ก่อน volt-watt pass เพื่อรักษา LV head voltage ให้อยู่ภายใน deadband รอบ `TRANSFORMER_OLTC_V_TARGET` โดยแก้ power flow ซ้ำจนอยู่ใน band หรือแตะถึงขีดจำกัด

### 2.4 Bus Mapping

มิเตอร์แต่ละตัวจะถูก map ไปยัง bus ในโครงข่ายผ่าน `_map_meters_to_topology_buses` การโหลดและการผลิตรวมกันต่อ bus จะถูกส่งเข้า pandapower ก่อนแก้สมการ

---

## 3. แบบจำลองอุปกรณ์พลังงานหมุนเวียน (DER Device Models)

### 3.1 มิเตอร์อัจฉริยะ (SmartMeter)

`SmartMeter` (`devices/ami.py`) แทนมิเตอร์หนึ่งตัว ซึ่งประกอบด้วยโมดูลย่อย:

- **`Load`** (`devices/load.py`) — สร้าง load profile ตาม ZIP model (constant impedance / constant current / constant power) ตามสัดส่วนที่กำหนดในการตั้งค่า
- **`Solar`** (`devices/solar.py`) — คำนวณกำลังผลิตโซลาร์ด้วย pvlib ตามมุมเอียง ทิศ อุณหภูมิ และสภาพอากาศจากการตั้งค่า
- **`electrical.py`** (`core/meter_logic/electrical.py`) — คำนวณแรงดัน กระแส กำลังไฟฟ้าเชิงรีแอกทีฟ power factor และความถี่โดยเพิ่ม noise ตาม accuracy class ของมิเตอร์ และใช้ ZIP voltage sensitivity

แต่ละมิเตอร์มีสตรีม RNG อิสระ (`_rng`) ที่ได้จาก SHA-256 digest ของ meter_id XOR กับ global seed ทำให้การเพิ่ม/ลบมิเตอร์ไม่ส่งผลต่อ noise stream ของมิเตอร์อื่น รับรองความ determinism ของการจำลอง

### 3.2 Frequency-Watt Droop Control (Primary Response)

`apply_droop_control` (`core/meter_logic/electrical.py`) ปรับกำลังส่งออกของ inverter ตามความเบี่ยงเบนความถี่ระบบ:

```
f_dev_pu = (f - 50.0) / 50.0
p_sadj_pu = -20.0 × f_dev_pu  (ในกรณีที่ |f_dev_pu| > 0.001)
```

Deadband อยู่ที่ ±50 mHz เพื่อหลีกเลี่ยงการตอบสนองต่อ noise ปกติ

`_update_grid_frequency` ใน engine คำนวณความถี่ระบบจาก supply/demand imbalance รายจำหน่าย และ frequency ของแต่ละโซนที่ island แยกตัวออกไปจะคำนวณจาก balance ของสมาชิกในโซนนั้นเอง

---

## 4. การควบคุม Smart Inverter ตามมาตรฐาน IEEE 1547

### 4.1 Volt-VAR Control (Q(V))

`GridManager` ดำเนิน **volt-VAR** ก่อน volt-watt ในแต่ละ tick โดย inverter แต่ละตัวติดตาม piecewise Q(V) curve ตามจุด breakpoint สี่ค่า:

| ช่วงแรงดัน | การตอบสนอง |
|---|---|
| V ≤ v1 (0.92 pu) | inject Q สูงสุด (−Q) |
| v1 < V ≤ v2 (0.98 pu) | ramp จาก −Q ถึง 0 |
| v2 < V ≤ v3 (1.02 pu) | deadband (Q = 0) |
| v3 < V ≤ v4 (1.08 pu) | ramp จาก 0 ถึง +Q |
| V > v4 | absorb Q สูงสุด (+Q) |

Q ถูกจำกัดด้วย headroom ของ inverter (`sqrt(sn² − p²)`) และ q_max_frac (IEEE 1547 Category B = 0.44 pu) การแก้ power flow ทำซ้ำจนถึง fixed point เนื่องจากการ inject Q ส่งผลต่อแรงดันที่ขับ Q เอง

### 4.2 Volt-Watt Control

หากแรงดัน bus เกิน `v_start` (ค่าเริ่มต้น 1.06 pu) หลังจาก volt-VAR pass ระบบจะลด real-power export ของ inverter เป็นเส้นตรงจนเป็นศูนย์ที่ `v_end` (1.10 pu) การ iterate ถึง fixed point เนื่องจากการลด P ส่งผลต่อแรงดันด้วย ค่า `total_curtailed_kw` รายงานใน tick summary

การควบคุมทั้งสองทำงาน **แบบลำดับ** (sequential): volt-VAR จัดการ reactive power ก่อน จากนั้น volt-watt จัดการ overvoltage ที่เหลืออยู่ ไม่ใช่ co-optimized

---

## 5. การจัดการ Microgrid และ Zone Islanding

### 5.1 โครงสร้างโซน

แต่ละโซนใน `GridTopology.zones` มี:
- สมาชิก bus (`members`)
- จุดเชื่อมต่อกับระบบหลัก (`pcc_bus`/`pcc_transformer`)
- DER bus (bus ที่มี PV ใหญ่ที่สุดในโซน ทำหน้าที่เป็น slack เมื่อ island)
- แฟล็ก `islandable` ที่ระบุว่าโซนสามารถแยกตัวได้

### 5.2 ZoneController

`ZoneController` (`core/zone_manager.py`) จัดการการ island/reconnect เป็น runtime control surface โดย:

- `island(code)` — เปิด PCC transformer ของโซน (ผ่าน `faulted_transformers`) โซนหัวยังคงเป็น live load bus ที่ DER สามารถจ่ายไฟได้
- `reconnect(code)` — นำ PCC transformer กลับเข้าบริการ
- สถานะ **derived live** จาก `grid.faulted_transformers` ไม่มี private state จึง consistent ผ่าน reset และ topology swap

### 5.3 Island Power Flow

เมื่อโซนถูก island ระบบจะสร้าง temporary local `ext_grid` slack ที่ DER bus (`_apply_island_slacks`) ทำให้โซนรักษาแรงดันได้ตลอดทั้งโซน โซนที่ไม่มี DER จะดับ (de-energize) `_island_ext_grid_idx` ติดตาม index และถูกลบทิ้ง/สร้างใหม่ทุก solve เพื่อให้โซนที่ reconnect แล้วสูญเสีย slack ทันที

### 5.4 Tie-Switch

`GridLine` ที่มี `is_switch=True` และ `normally_open=True` จะถูกนำออกนอกบริการโดยอัตโนมัติเหมือน fault API `set_switch`/`switch_status` (ผ่าน `/api/v1/simulation/switches/{name}/close|open`) ช่วยให้โอนโหลดหรือฟื้นฟูไฟฟ้าระหว่างโซน

### 5.5 Fault Injection

`GridManager` รองรับการฉีดความผิดพลาดสำหรับการศึกษา N-1 contingency และความยืดหยุ่นของโครงข่าย:

- **เส้น (line)** — นำออกนอกบริการก่อนแก้สมการ
- **Bus** — de-energize bus พร้อมโหลดที่เชื่อมต่อ
- **หม้อแปลง (transformer)** — นำออกนอกบริการ รวมถึง PCC transformer สำหรับ islanding

`islanded_buses` คำนวณใหม่ทุก tick: bus ที่เชื่อมต่ออยู่แต่สูญเสีย path ทั้งหมดไปยัง substation slack

---

## 6. Demand Response Controller

`DemandResponseController` (`core/demand_response.py`) จัดการเหตุการณ์ DR ที่กำหนดผ่าน API โดยแต่ละ event มี:

- ช่วงเวลา simulation clock แบบ half-open `[start, end)`
- `reduction_fraction` — สัดส่วนโหลดที่ลด (เช่น 0.30 = ลด 30%)
- `target_meter_types` — กรองตามประเภทมิเตอร์ (optional)
- `target_zones` — กรองตาม zone_code สำหรับการลดโหลดเฉพาะจุดในสายป้อน (optional)
- ตัวกรองทั้งสองทำงานแบบ AND

Event ที่ซ้อนทับกันรวมกันโดยใช้ค่า `reduction_fraction` **สูงสุด** (ไม่ใช่สะสม) engine แก้ไขค่า `dr_load_factor` ต่อ `(meter_type, zone_code)` ทุก tick และส่งผ่าน `generate_all` ไปยัง `SmartMeter.generate_reading(dr_load_factor=…)` ซึ่งปรับ consumption หลัง grid-stress

---

## 7. โปรโตคอล DLMS/COSEM (IEC 62056) และการส่งข้อมูล

### 7.1 OBIS Encoding

`AggregatorBridgeEmitter` (`transport/aggregator_bridge.py`) เข้ารหัสค่าวัดแต่ละตัวเป็น OBIS-code keyed JSON ตามมาตรฐาน IEC 62056 register ที่ส่งไปรวมถึง:

| OBIS Code | ความหมาย |
|---|---|
| `1.1.1.8.0.255` | Active energy import รวม (Wh) |
| `1.1.2.8.0.255` | Active energy export รวม (Wh) |
| `1.1.16.7.0.255` | Net active power (kW) — C=16 sum group |
| `1.1.1.6.0.255` | Maximum demand import rolling peak (kW) |
| `1.1.32.7.0.255` / `1.1.31.7.0.255` | Voltage L1 / Current L1 |
| `1.1.14.7.0.255` / `1.1.13.7.0.255` | Frequency / Power factor |
| `1.1.3.8.0.255` / `1.1.4.8.0.255` | Reactive energy import/export (varh) |
| `0.0.96.10.0.255` | DR status (1 = load-shed active) |
| `0.0.96.14.0.255` | Active tariff indicator (1=peak, 2=off-peak) |
| `1.1.1.8.1.255` / `1.1.1.8.2.255` | TOU import peak/off-peak (Wh) |

### 7.2 ลายมือชื่อ Ed25519

แต่ละการอ่านค่าลงนามด้วย Ed25519 private key ของมิเตอร์ตาม canonical string:

```
canonical = f"{device_id}:{kwh}:{timestamp_ms}"
```

bridge ตรวจสอบลายมือชื่อผ่าน public key ที่ลงทะเบียนไว้ใน Redis device registry ก่อน ingest

### 7.3 Time-of-Use (TOU) Metering

`TouSchedule` จัดประเภทเวลาตามตาราง MEA/PEA ไทย: **Peak** (จันทร์–ศุกร์ 09:00–22:00), **Off-peak** (นอกช่วง peak และวันหยุดสุดสัปดาห์) ระบบสะสมพลังงาน import/export แยกตาม rate register เพื่อการออกบิล TOU

---

## 8. อัตราค่าไฟฟ้าไทย (MEA/PEA Tariff Model)

`thai_tariff.py` (`pricing/thai_tariff.py`) จำลองโครงสร้างค่าไฟฟ้าขายปลีกของ MEA/PEA ในประเทศไทยสำหรับแรงดันต่ำ (<12 kV) ประกอบด้วย:

- **ค่าพลังงาน (Energy Charge)** — แบบขั้นบันได ตาม tariff class: residential_small (≤150 kWh/เดือน), residential_normal (>150 kWh/เดือน), residential_tou, small_business, small_business_tou
- **Ft (Fuel adjustment charge)** — config-driven (`TARIFF_FT_PER_KWH`) ค่าเริ่มต้น 0.3672 ฿/kWh (ม.ค.–เม.ย. 2568)
- **Service charge** — ค่าคงที่ต่อเดือนตาม tariff class
- **VAT** — 7% บน (energy + Ft + service)

ข้อมูลนี้ถูกใช้ร่วมกับ `cumulative_peak_import_kwh` / `cumulative_offpeak_import_kwh` ที่สะสมในแต่ละมิเตอร์เพื่อคำนวณบิลรายงวด

---

## 9. REST API

ระบบเปิดให้เข้าถึงผ่าน FastAPI (พอร์ต 8082 ค่าเริ่มต้น) โดยมี endpoint หลักดังนี้:

| กลุ่ม | Endpoint | คำอธิบาย |
|---|---|---|
| Simulation | `GET/POST /api/v1/simulation` | ดูสถานะ / ควบคุม (start/pause/reset) |
| Simulation | `POST /api/v1/simulation/faults` | ฉีด fault ที่ line/bus/transformer |
| Simulation | `GET/POST /api/v1/simulation/demand-response` | จัดการ DR events |
| Simulation | `GET/POST /api/v1/simulation/zones/{code}/island\|reconnect` | Island/reconnect โซน |
| Simulation | `GET/POST /api/v1/simulation/switches/{name}/close\|open` | ควบคุม tie-switch |
| Meters | `GET /api/v1/meters` | รายชื่อมิเตอร์พร้อม zone/zone_code |
| Grid | `GET /api/v1/grid` | สถานะโครงข่าย (แรงดัน, โหลด, losses) |
| History | `GET /api/v1/history/readings` | ค่าวัดในอดีต (เมื่อ PostGIS เปิด) |
| History | `GET /api/v1/history/network/geojson` | Asset network ในรูปแบบ GeoJSON |

เอกสาร API อัตโนมัติ (OpenAPI/Swagger UI) อยู่ที่ `/docs`

---

## 10. Persistence และ Observability

### 10.1 PostGIS

เมื่อเปิด `POSTGIS_ENABLED=true` ระบบ batch-insert ค่าวัดทุก tick ลงตาราง `grid.meter_readings` (PostGIS schema) ผ่าน `ReadingStore` (`persistence/reading_store.py`) โดยใช้ asyncpg pool และ drop tick หากชุดก่อนหน้ายังค้างอยู่ (back-pressure) รองรับการ replay ประวัติและการ query เชิง geo

### 10.2 Prometheus Metrics

`core/metrics.py` export Prometheus metrics ได้แก่ `ACTIVE_METERS` (gauge จำนวนมิเตอร์ที่ active) `SIMULATION_TICK_TIME` (histogram เวลาต่อ tick) และ `AGGREGATOR_EMIT_FAILED` / `POSTGIS_PERSIST_FAILED` (counter ความล้มเหลวในการส่งข้อมูล)

---

## 11. สรุป

GridTokenX Smart Meter Simulator นำเสนอแพลตฟอร์มจำลอง AMI ที่ครอบคลุมตั้งแต่ระดับ device model ไปถึงระดับ distribution grid ด้วย AC power flow จริง รองรับการควบคุม DER ตามมาตรฐาน IEEE 1547 การจัดการ microgrid และ islanding การฉีดความผิดพลาดเพื่อศึกษา contingency การจัดการ Demand Response แบบ zone-aware และการส่งข้อมูลผ่านโปรโตคอล DLMS/COSEM พร้อมลายมือชื่อ Ed25519 ระบบนี้ทำหน้าที่เป็นชั้นข้อมูล AMI ของ GridTokenX ecosystem ที่ส่งข้อมูลพลังงานเข้าสู่กระบวนการ settlement และ blockchain ผ่าน Aggregator Bridge

---

*[REF] ให้เติม citation จริงตาม IEEE Std 1547-2018, IEC 62056-6-2, pandapower documentation, และ pvlib documentation ตามรูปแบบ citation ของวารสารที่ส่ง*
