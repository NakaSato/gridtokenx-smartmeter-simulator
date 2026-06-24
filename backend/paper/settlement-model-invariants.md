# Settlement Model Invariants

<!-- Section นี้พูดถึง simulator ในเชิง "คุณสมบัติเชิงคณิตศาสตร์ที่มันค้ำประกัน" ไม่ใช่สถาปัตยกรรม -->

## 3.x Physical Invariants ที่ Simulator รับประกัน

ก่อนที่ reading ใดจะได้รับการเซ็น Ed25519 และส่งเข้าสู่ Aggregator Bridge simulator ต้องรับประกัน invariants ต่อไปนี้:

### 3.x.1 Determinism (Reproducibility)

สำหรับ global seed $s$ ที่กำหนด ลำดับ input เดียวกัน (topology, simulation clock, weather sequence) จะได้ผลลัพธ์ที่เหมือนกันทุก run:

$$\forall t,\; \text{Reading}(t, s) = \text{Reading}(t, s)$$

รับประกันได้โดย: (i) seed RNG เดียวกันก่อนสร้าง fleet ทุกครั้ง (ii) per-meter noise stream อิสระที่ derive จาก SHA-256 digest ของ meter_id XOR global seed ทำให้การเพิ่ม/ลบมิเตอร์ไม่ shift stream ของตัวอื่น (iii) DR events และ fault injection ถูก index ด้วย monotonic counter ไม่ใช่ RNG

### 3.x.2 Energy Conservation

ผลรวมกำลังไฟฟ้าที่ผลิตได้ ลบด้วยผลรวมที่บริโภค ต้องเท่ากับ losses ที่คำนวณจาก power flow:

$$\sum_i P_{\text{gen},i} - \sum_j P_{\text{cons},j} = P_{\text{losses}} + P_{\text{curtailed}}$$

รับประกันได้โดย pandapower ที่แก้ power flow จนถึง convergence tolerance ($\leq 10^{-8}$ pu) ก่อน reading ใดจะถูกสร้าง ในกรณี DistFlow fallback ค่า losses คือ approximate แต่ยังอยู่ภายใต้ conservation bound

### 3.x.3 Physical Bounds ของ Bus Voltage

แรงดันของทุก bus ต้องอยู่ภายในขอบเขตที่ยอมรับได้ของโครงข่าย:

$$V_{\min} \leq V_i \leq V_{\max} \quad \forall i \in \text{buses}$$

โดย Volt-VAR control ทำงานก่อน (reactive support) และ Volt-Watt ตามหลัง (real-power curtailment) ทั้งคู่ iterate จนถึง fixed point ก่อน reading ถูก snapshot ทำให้แรงดันที่รายงานสะท้อนสถานะที่ converged ไม่ใช่สถานะระหว่างการ iterate

### 3.x.4 Monotonic Curtailment Ratchet

กำลัง export ที่ถูก curtail จะถูก ratchet ให้ stable ก่อนบันทึก ป้องกันการสลับกลับไปกลับมาระหว่าง tick:

$$P_{\text{export},i}(t) \leq P_{\text{export},i}(t-1) \quad \text{หากแรงดันยังสูงเกิน } V_{\text{end}}$$

### 3.x.5 Monotonic Energy Accumulators

ค่าสะสมพลังงาน import/export ของมิเตอร์ต้องไม่ลดลงระหว่าง tick:

$$E_{\text{import}}(t) \geq E_{\text{import}}(t-1), \quad E_{\text{export}}(t) \geq E_{\text{export}}(t-1)$$

รับประกันโดยโครงสร้าง `SmartMeter` ที่สะสมค่า `cumulative_import_kwh` / `cumulative_export_kwh` แบบ additive เท่านั้น ไม่มีการลบหรือ reset ระหว่างการทำงาน

## 3.x Chain-of-Custody Link: Ed25519 Source Authenticity

Simulator ผูก invariants ข้างต้นเข้ากับ cryptographic proof ผ่าน Ed25519 signature บน canonical string:

$$\sigma_i = \text{Sign}_{sk_i}\bigl(\texttt{device\_id}_i \| \texttt{:} \| \texttt{kwh}_i \| \texttt{:} \| \texttt{timestamp\_ms}_i\bigr)$$

โดย $sk_i$ คือ private key ของมิเตอร์ที่สร้างขึ้นก่อน ingest และ public key ลงทะเบียนไว้ใน Redis device registry ของ Aggregator Bridge ก่อนส่ง reading แรก

กลไกนี้สร้าง chain-of-custody: reading ที่ผ่าน invariants และ signed แล้วเท่านั้นจึงจะผ่านการตรวจสอบ `verify_rest_signature` ของ bridge และเข้าสู่ settlement pipeline — ทำให้ข้อมูลที่ออกจาก simulator สามารถ attributed ได้ถึงแหล่งที่มา (source authenticity) ตลอด chain
