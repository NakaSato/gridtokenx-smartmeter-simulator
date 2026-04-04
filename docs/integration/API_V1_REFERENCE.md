# API v1 - Consolidated Reference

**Date:** 2026-04-04
**Status:** ✅ Complete — 65 v1 routes across 7 domains

---

## Route Map

```
/api/v1/
├── meters/                          # Meter management
│   ├── GET,POST /                   # List / create meters
│   ├── GET /nearby                  # Spatial query (?lat,?lon,?radius)
│   ├── GET,PUT /{id}/readings       # Get / update readings
│   ├── POST /{id}/readings/override  # Force simulation override
│   ├── GET /{id}/wallet             # Wallet balance
│   ├── POST /{id}/wallet/airdrop    # Airdrop tokens
│   ├── GET /{id}/bills              # List bills
│   ├── GET /{id}/bills/{bill_id}    # Bill details
│   └── GET /{id}/bills/history      # Billing history
│
├── grid/                            # Physical infrastructure
│   ├── GET /status                  # Grid status
│   ├── GET /topology                # Topology (?version=legacy)
│   ├── GET /telemetry               # Real-time sensor data
│   ├── GET /state-estimation        # State estimation results
│   ├── GET /snapshots               # Grid snapshots
│   ├── GET /export                  # Export (?format=geojson|cim|mvt)
│   ├── GET,POST /substations        # List / create substations
│   ├── GET /substations/{id}        # Substation details
│   ├── GET /transformers/nearest    # Nearest transformers
│   └── GET /stats                   # Grid statistics
│
├── billing/                         # Billing domain
│   └── GET /summary                 # Billing summary
│
├── vpp/                             # Virtual Power Plant
│   ├── GET /clusters                # Cluster status
│   └── POST /actions/dispatch       # Dispatch command
│
├── analytics/                       # Analytics
│   └── GET /summary                 # Dashboard summary
│
├── registry/                        # Reference data
│   └── thailand/
│       └── plants/                  # Power plants (?group_by=fuel|region)
│           ├── GET /stats           # Plant statistics
│           └── GET /{id}            # Plant details
│
└── quality/                         # Validation & QA
    ├── GET /health                  # Service health
    ├── validate/                    # Synchronous validation
    │   ├── GET,POST /infrastructure # All analysers
    │   ├── POST /substation         # Substations only
    │   ├── POST /power-line         # Power lines only
    │   ├── POST /duplicates         # Duplicates only
    │   ├── POST /meter-alignment    # Match meters to infra
    │   └── POST /power              # Custom power data
    ├── GET /issues                  # Issues (?analyser,?category,?level)
    ├── GET /issues/{id}             # Issue details
    ├── GET /rules                   # Validation rule definitions
    ├── GET /stats                   # Validation statistics
    ├── GET /quality-score           # Score (0-100)
    ├── GET /quality-summary         # Comprehensive summary
    ├── GET /dashboard               # Dashboard data
    ├── GET /categories              # Category definitions
    ├── GET,PATCH /monitor           # Monitoring ({enabled: bool})
    ├── analytics/
    │   ├── POST /daily              # Run daily analytics
    │   └── GET /daily/{date}        # Get daily analytics
    └── GET /config                  # Configuration
```

---

## Before → After (Consolidated)

| Before (6 routers, 29 quality routes + scattered) | After (1 router, 65 v1 routes) |
|---------------------------------------------------|--------------------------------|
| `/api/meters/` (8) | `/api/v1/meters/` (11) |
| `/api/grid/` (21) | `/api/v1/grid/` (10) |
| `/api/vpp/` (2) | `/api/v1/vpp/` (2) |
| `/api/dashboard/summary` (1) | `/api/v1/analytics/summary` (1) |
| `/api/thailand/` (6) | `/api/v1/registry/thailand/` (3) |
| `/api/v1/analysis/` (8) | |
| `/api/v1/grid-quality/` (11) | `/api/v1/quality/` (18) |
| `/api/power/` (5) | |
| `/api/quality/` (5) | |
| `/api/v1/price/` + `/api/v1/revenue/` | Preserved from existing routers |

**Eliminated:**
- `grid_analysis.py` → merged into `api_v1.py`
- `grid_quality_router.py` → merged into `api_v1.py`
- `power_validation.py` → merged into `api_v1.py`
- `quality.py` → merged into `api_v1.py`
- `quality_v1.py` → merged into `api_v1.py`
- `/api/grid/postgis/` paths → simplified to `/api/v1/grid/`
- `/api/grid/legacy-topology` → `/api/v1/grid/topology?version=legacy`
- `/api/grid/geojson` + `/api/grid/geojson/export` + `/api/grid/export/cim` → `/api/v1/grid/export?format=...`
- `/api/grid/measurements` → `/api/v1/grid/telemetry`
- `/api/grid/estimation` → `/api/v1/grid/state-estimation`
- `/api/dashboard/summary` → `/api/v1/analytics/summary`

**New routes:**
- `PUT /api/v1/meters/{id}/readings` — Manual reading update
- `GET /api/v1/meters/nearby` — Spatial query
- `GET /api/v1/grid/substations/{id}` — Individual substation lookup
- `GET /api/v1/meters/{id}/bills/{bill_id}` — Individual bill lookup
- `PATCH /api/v1/quality/monitor` — Toggle monitoring with body

---

## Tests: 22/22 Passing ✅
