# Evaluation

<!-- Simulator ทำหน้าที่เป็น methodology/platform ในส่วนนี้ — อ้างกลับไป §4.x -->

## 5.x การตั้งค่าสถานการณ์จำลอง (Simulation Setup)

การประเมินใช้ GridTokenX Simulator (§4.x) เป็นแพลตฟอร์มสร้างข้อมูลสำหรับสถานการณ์ต่อไปนี้ โทโพโลยีโครงข่ายใช้ไฟล์ GLM ของโครงข่ายจำหน่ายแรงต่ำสมมุติที่สอดคล้องกับโครงสร้างของ MEA/PEA โดยมีพารามิเตอร์ดังนี้:

| พารามิเตอร์ | ค่า |
|---|---|
| จำนวนมิเตอร์ | 80 |
| สัดส่วน PV penetration | 25% ของ bus |
| ขนาด PV ต่อ bus | 10 kW |
| Simulation interval | 15 นาที |
| Random seed | คงที่ (deterministic) |
| Tariff class | residential_tou (MEA) |

## 5.x.1 การตรวจสอบ Physical Invariants

**Determinism:** รัน simulation ซ้ำ 5 รอบด้วย seed เดียวกัน ตรวจสอบว่า reading แต่ละตัวทุก tick ได้ค่าเหมือนกันทุก byte ยืนยันว่า invariant ใน §3.x.1 เป็นจริงในทุก run

**Energy Conservation:** ตรวจสอบ $|\sum P_{\text{gen}} - \sum P_{\text{cons}} - P_{\text{losses}} - P_{\text{curtailed}}| < \epsilon$ ทุก tick โดย $\epsilon$ ตาม pandapower convergence tolerance ($10^{-8}$ pu)

**Voltage Bounds:** บันทึก bus voltage ทุก tick ยืนยันว่า Volt-VAR + Volt-Watt control รักษาแรงดันไว้ใน [0.94, 1.10] pu บน bus ทุกจุดตลอดช่วง peak PV injection

## 5.x.2 สถานการณ์ที่ทดสอบ

**สถานการณ์ A — High PV Penetration:** รัน simulation ในช่วง peak generation (10:00–14:00) เพื่อสังเกต Volt-VAR reactive injection ก่อน Volt-Watt curtailment kick in และวัด `total_curtailed_kw` vs `total_reactive_support_kvar` ต่อ tick

**สถานการณ์ B — Zone Islanding:** island โซนที่มี DER bus ผ่าน `/api/v1/simulation/zones/{code}/island` วัดเวลาที่ใช้ก่อนโซนรักษาแรงดันได้ด้วย local DER slack และสังเกต per-zone frequency decoupling

**สถานการณ์ C — N-1 Fault Injection:** ฉีด fault ที่สายหลัก (สาย feeder ต้นทาง) สังเกต islanded_bus_count และ DistFlow fallback activation rate เทียบกับ pandapower convergence rate

**สถานการณ์ D — Demand Response:** กำหนด DR event ที่ลด 30% ของ `residential_tou` meters ในโซน 2 ระหว่าง peak period วัด `total_dr_shed_kw` และผลต่อ LV bus voltage เทียบกับ baseline

**สถานการณ์ E — Settlement Validation:** รัน full pipeline (Simulator → Aggregator Bridge → settlement bins) ตรวจสอบ Ed25519 signature pass rate, TOU register accuracy เทียบกับ sim clock, และ settlement energy balance ต่อมิเตอร์

## 5.x.3 ผลลัพธ์ที่คาดหวัง

<!-- เติมตัวเลขจริงจากผลการรันหลังจากทำการทดสอบ -->

ผลลัพธ์ในแต่ละสถานการณ์จะถูกรายงานในรูปแบบ: voltage profile (pu ต่อ bus), power flow convergence rate (bfsw vs DistFlow fallback), curtailment volume (kWh ต่อช่วง), frequency deviation (Hz ต่อโซน), และ settlement accuracy (% deviation จาก true energy)

*[หมายเหตุ: ใส่ตัวเลขจริงจากการรัน simulation หลังจากทำการทดสอบ รูปแบบที่แนะนำ: ตาราง + กราฟ voltage profile + กราฟ curtailment timeline]*
