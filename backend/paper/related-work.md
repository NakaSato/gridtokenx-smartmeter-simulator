# Related Work

## ตัวจำลองโครงข่ายไฟฟ้า (Grid Simulation Tools)

เครื่องมือจำลองโครงข่ายไฟฟ้าที่ใช้กันแพร่หลาย ได้แก่ **GridLAB-D** [REF] ซึ่งรองรับการจำลองโครงข่ายจำหน่ายแบบ time-series และ **OpenDSS** [REF] ที่เน้น steady-state distribution analysis ทั้งสองเครื่องมือรองรับการจำลองพฤติกรรม DER และ smart inverter แต่ถูกออกแบบมาเพื่อวิเคราะห์โครงข่าย ไม่ใช่ผลิต telemetry ที่มีลายมือชื่อสำหรับ settlement layer นอกจากนี้ **pandapower** [REF] เป็น Python library สำหรับ AC power flow ที่ยืดหยุ่นและทดสอบได้ดี แต่ไม่มี device model ระดับ AMI หรือโครงสร้างค่าไฟฟ้าแบบขายปลีก

## Co-simulation Frameworks

กรอบงาน co-simulation เช่น **HELICS** [REF] และ **mosaik** [REF] ช่วยให้เชื่อมต่อ simulator หลายตัวเข้าด้วยกัน (เช่น รวม GridLAB-D กับ PyDER) แต่มีความซับซ้อนในการตั้งค่าสูงและไม่มีกลไก signature/chain-of-custody ในตัว การนำ co-simulation มาใช้กับ blockchain settlement จึงต้องพัฒนา adapter ขึ้นมาเองในชั้น transport

## AMI Simulation สำหรับ Blockchain

งานที่เกี่ยวข้องกับ peer-to-peer energy trading บน blockchain [REF] ส่วนใหญ่ใช้ข้อมูลสังเคราะห์อย่างง่าย (random walk หรือ historical replay) โดยไม่รัน power flow จริง ทำให้ไม่สามารถตรวจสอบ physical consistency ของข้อมูลก่อนเข้าสู่สัญญาอัจฉริยะได้ ส่งผลให้ผลลัพธ์ settlement ไม่สะท้อนข้อจำกัดของโครงข่ายจริง เช่น voltage violation หรือ congestion

## Gap ที่งานนี้เติมเต็ม

เครื่องมือที่มีอยู่ทั้งหมดไม่ได้รวมองค์ประกอบต่อไปนี้ไว้ในระบบเดียว:

- **AC power flow ครบวงจร** ที่ตรวจสอบ physical invariants ทุก tick (ไม่ใช่ approximation)
- **IEEE 1547 smart inverter control** (Volt-VAR + Volt-Watt) ที่โต้ตอบกับแรงดันจริงจาก power flow
- **โครงสร้างค่าไฟฟ้า MEA/PEA** ของไทยรวมถึง TOU tariff สำหรับ billing ที่ถูกต้องตามบริบทท้องถิ่น
- **Ed25519-signed telemetry** ที่ serialized ในรูปแบบ DLMS/COSEM (IEC 62056) พร้อม canonical string สำหรับ on-chain verification
- **Deterministic replay** ที่รับประกันว่าผลลัพธ์เหมือนกันทุก run เพื่อให้ settlement audit ได้

GridTokenX Simulator จึงเป็น contribution เชิงออกแบบที่เชื่อม gap ระหว่าง grid simulation accuracy กับ blockchain settlement trustworthiness โดยออกแบบมาให้ทำงานร่วมกันตั้งแต่แรก ไม่ใช่การ adapter ของเดิม
