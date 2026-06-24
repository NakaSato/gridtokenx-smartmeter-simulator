# Discussion and Limitations

## 6.x ข้อจำกัดของ GridTokenX Simulator

การออกแบบ simulator ในงานนี้มีข้อจำกัดที่ต้องรับทราบในการตีความผลลัพธ์ดังต่อไปนี้

### 6.x.1 ไม่มีแบบจำลอง Battery และ EV

ระบบไม่มี device model สำหรับ battery energy storage system (BESS) และ electric vehicle (EV) charger ซึ่งในโครงข่ายจริงทั้งสองประเภทนี้มีผลต่อ voltage profile และ demand pattern อย่างมีนัยสำคัญ โดยเฉพาะในช่วง EV charging peak และ battery discharge ตอนเช้า ผลการศึกษา Volt-Watt curtailment ในงานนี้จึงอาจ underestimate กรณีที่มี BESS ทำหน้าที่ absorb excess PV แทน curtailment

### 6.x.2 One-Tick Governor Lag ใน Frequency-Watt Response

การควบคุม Frequency-Watt (primary response) มี lag หนึ่ง tick ระหว่าง frequency deviation กับการตอบสนองของ inverter เนื่องจาก frequency ถูก update ที่ต้น tick แล้ว droop control ถูก apply ใน tick ถัดไป ในโครงข่ายจริงที่มี inertia ต่ำ (เช่น island microgrid ขนาดเล็ก) lag ดังกล่าวอาจทำให้ผลการศึกษา frequency nadir มีความ optimistic กว่าความเป็นจริง

### 6.x.3 Sequential Control แทน Co-Optimized Control

Volt-VAR และ Volt-Watt ทำงานแบบ sequential (VAR ก่อน Watt) ไม่ใช่ co-optimized ภายใต้ objective function เดียว วิธีนี้ใกล้เคียงกับ implementation จริงของ smart inverter ทั่วไปแต่ไม่ได้ผลลัพธ์ที่ optimal เท่า MPC (Model Predictive Control) หรือ convex optimization approach งานที่ต้องการ optimal DER dispatch ควรพิจารณาขยาย grid_manager ด้วย optimization layer

### 6.x.4 DistFlow Approximation Error

เมื่อ pandapower ไม่ converge ระบบสลับมาใช้ DistFlow sweep ซึ่งเป็น linear approximation ของ AC power flow ที่ละเลย reactive losses และ second-order voltage terms ในโครงข่ายที่ R/X ratio สูง (เช่น LV cable) หรือโหลดหนักมาก error ของ DistFlow อาจสูงถึงหลาย percent pu ของแรงดัน ผลลัพธ์จาก tick ที่ใช้ DistFlow fallback จึงมีความแม่นยำต่ำกว่าและควรระบุในการรายงาน

### 6.x.5 OLTC กับ pandapower 3.3

pandapower 3.3 มีข้อจำกัดกับ `bfsw` solver บน transformer ที่มี non-neutral tap ทำให้การแก้ power flow ในโหมด OLTC ต้องสลับมาใช้ Newton-Raphson โดยอัตโนมัติ (transformer สร้างด้วย `tap_changer_type="Ratio"`) ซึ่งอาจ converge ช้ากว่าในบาง topology

### 6.x.6 Synthetic Telemetry กับ Real AMI Data

ค่าวัดที่ผลิตโดย simulator เป็น synthetic ซึ่งแม้จะผ่าน physics-based power flow แต่ไม่ได้สะท้อน non-modeled effects ที่พบในข้อมูลจริง เช่น meter clock drift, communication loss, tamper events, และ non-linear load harmonics การ validate ระบบ settlement ด้วยข้อมูล AMI จริงจาก MEA/PEA จะเพิ่มความน่าเชื่อถือของผลลัพธ์

## 6.x การขยายงานในอนาคต

ข้อจำกัดข้างต้นชี้ให้เห็นทิศทางการขยายงานที่ชัดเจน ได้แก่ การเพิ่ม BESS/EV device model ที่รองรับ State-of-Charge dynamics, การ implement co-optimized Volt-VAR/Volt-Watt ผ่าน convex relaxation, การพัฒนา hybrid solver ที่ quantify DistFlow error bound, และการ integrate ข้อมูล AMI จริงผ่าน telemetry replay path ที่มีอยู่แล้วใน simulator
