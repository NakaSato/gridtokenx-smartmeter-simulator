# PEA HACKATHON — QUICK REFERENCE CARD

**Demo Date:** Wednesday, 2026-04-23  
**Status:** ✅ ALL SYSTEMS GO

---

## 🚀 Quick Start (30 seconds)

```bash
cd backend
uv run python scripts/test_pea_api.py
```

**Expected:** All green checkmarks + "Ready for Wednesday presentation!"

---

## 📊 Key Numbers (Memorize These)

| Metric | Value |
|--------|-------|
| **MAPE** | 4.08% (target: <10%) |
| **Daily Savings** | 4.8M THB |
| **Monthly Savings** | 144M THB ($4.1M USD) |
| **Annual Savings** | 1.76B THB ($50M USD) |
| **Cost Reduction** | 69.4% |
| **Payback Period** | 2.1 months |

---

## 🎯 3-Minute Demo Script

### 0:00-0:30 — The Problem
"Koh Tao runs on diesel at 13 THB/kWh. The submarine cable is a bottleneck. When it fails, blackout."

### 0:30-1:30 — The Solution
"Our AI forecasts load with 4% error. OPF optimizer saves 144M THB/month. EWS prevents blackouts."

**[DEMO: curl forecast endpoint]**

### 1:30-2:30 — The Impact
"Production-ready. 8 REST APIs. 2-month payback. Deploy tomorrow."

**[DEMO: curl savings endpoint]**

### 2:30-3:00 — The Ask
"Pilot on Koh Tao. Scale to all Thai islands. Make diesel obsolete."

---

## 🔧 Live Demo Commands

### Test 1: Forecast
```bash
curl "http://localhost:8082/api/v1/forecast/24h?node_id=SAMUI-HUB-01" | jq '.mape_pct'
```
**Expected:** `4.08`

### Test 2: Savings
```bash
curl "http://localhost:8082/api/v1/optimize/savings" | jq '.monthly_savings_thb'
```
**Expected:** `144393111`

### Test 3: EWS
```bash
curl -X POST "http://localhost:8082/api/v1/ews/simulate" \
  -H "Content-Type: application/json" \
  -d '{"loading_pct": 98}' | jq '.emergency_response.bess_dispatch_mw'
```
**Expected:** `20.0`

---

## 🎤 Talking Points

### Why 4% MAPE matters
"PEA requires <10%. We're at 4%. That's 2.5x better than the mandate."

### Why 144M THB matters
"That's $4.1M USD per month. For one island. Scale to 100 islands = $410M/year."

### Why 2.1 months matters
"BESS costs 200M THB. Pays back in 2 months. After that, pure profit."

### Why production-ready matters
"Not a prototype. 8 REST APIs. Swagger docs. Test suite. Deploy today."

---

## 🛡️ Backup Plan

If API fails:
1. Run `test_pea_api.py` → shows all metrics
2. Show model file → `ls -lh data/pea_lgbm_model.pkl`
3. Show code → `cat routers/forecast_v1.py`

---

## 📁 File Locations

```
backend/
├── scripts/
│   ├── pea_lightgbm_trainer.py    # Pillar 1
│   ├── pea_opf_optimizer.py       # Pillar 2
│   └── test_pea_api.py            # Test all
├── data/
│   └── pea_lgbm_model.pkl         # Trained model
└── src/smart_meter_simulator/
    └── routers/
        └── forecast_v1.py         # Pillar 3
```

---

## ✅ Pre-Demo Checklist

- [ ] Laptop charged
- [ ] WiFi/hotspot ready
- [ ] Terminal font size: 18pt
- [ ] Browser zoom: 150%
- [ ] Test API: `uv run python scripts/test_pea_api.py`
- [ ] Start server: `uv run uvicorn smart_meter_simulator.app:app --port 8082`
- [ ] Open Swagger: `http://localhost:8082/docs`
- [ ] Rehearse script (3 min)

---

## 🎯 Judging Criteria

| Criterion | Our Strength |
|-----------|--------------|
| **Feasibility** | Working API, proven MAPE |
| **Desirability** | 144M THB/month = clear ROI |
| **Viability** | 2.1 month payback |
| **Innovation** | Dual-target forecasting + EWS |

---

## 🚨 Emergency Contacts

- **Tech Lead:** [Your Name]
- **Backup:** [Teammate Name]
- **Repo:** `gridtokenx-smartmeter-simulator/backend`

---

## 💡 One-Liner

"We built an AI system that saves PEA 144 million THB per month by replacing diesel with smart BESS dispatch — and it pays back in 2 months."

---

**GOOD LUCK! 🚀**
