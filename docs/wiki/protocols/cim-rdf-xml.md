---
title: "CIM RDF/XML"
category: protocols
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/adapters/cim_adapter.py"]
tags: [protocol, interop, iec, grid]
related: [[Pandapower Adapter]], [[Thai Grid Topology]], [[PostGIS Integration]]
---

# CIM RDF/XML

CIM (Common Information Model) RDF/XML is the IEC 61970 standard for power system data exchange. It provides a standardized semantic model for describing grid elements (substations, lines, transformers, loads, generators) in a vendor-neutral format.

## Summary

The Smart Meter Simulator includes a CIM adapter that can import/export grid topology in CIM RDF/XML format, enabling interoperability with other power system tools (EMS, DMS, planning software).

## CIM Model Hierarchy

```
Core (IEC 61970-301)
├── EquipmentContainer (Substation, Bay, VoltageLevel)
├── ConductingEquipment (Busbar, Breaker, Disconnector)
├── PowerTransformer
├── ACLineSegment
└── EnergyConsumer (Load)
└── SynchronousMachine / PowerElectronicsConnection (DER)
```

## RDF/XML Example

```xml
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:cim="http://iec.ch/TC57/CIM100#">

  <cim:Substation rdf:ID="_SUB001">
    <cim:IdentifiedObject.name>Samut_Prakan_Sub</cim:IdentifiedObject.name>
    <cim:EquipmentContainer.Equipment rdf:resource="#_TX001"/>
  </cim:Substation>

  <cim:PowerTransformer rdf:ID="_TX001">
    <cim:IdentifiedObject.name>TX_160kVA</cim:IdentifiedObject.name>
    <cim:PowerTransformerInfo.ratedS>160000</cim:PowerTransformerInfo.ratedS>
    <cim:TransformerEnd.endratedU>22000</cim:TransformerEnd.endratedU>
    <cim:TransformerEnd.endratedU>400</cim:TransformerEnd.endratedU>
  </cim:PowerTransformer>

  <cim:ACLineSegment rdf:ID="_LINE001">
    <cim:Conductor.phaseImpedance rdf:resource="#_Z001"/>
    <cim:ACLineSegment.length>500</cim:ACLineSegment.length>
  </cim:ACLineSegment>

</rdf:RDF>
```

## Import/Export Flow

### Import (CIM → Pandapower)
1. Parse RDF/XML using `rdflib`
2. Extract equipment instances and relationships
3. Map CIM classes to pandapower elements:
   - `cim:Substation` → Substation metadata
   - `cim:PowerTransformer` → `net.trafo`
   - `cim:ACLineSegment` → `net.line`
   - `cim:EnergyConsumer` → `net.load`
   - `cim:PowerElectronicsConnection` → `net.sgen`

### Export (Pandapower → CIM)
1. Iterate pandapower network elements
2. Create CIM RDF/XML entities
3. Write relationships (connectivity, ownership)
4. Serialize to RDF/XML file

## Mapping to Pandapower

| CIM Class | Pandapower Element | Notes |
|-----------|-------------------|-------|
| `cim:BusbarSection` | `net.bus` | Bus identifier |
| `cim:ACLineSegment` | `net.line` | R, X, C from impedance data |
| `cim:PowerTransformer` | `net.trafo` | Rated power, voltages |
| `cim:EnergyConsumer` | `net.load` | P, Q from load profile |
| `cim:PowerElectronicsConnection` | `net.sgen` | Inverter-based DER |
| `cim:Terminal` | Connectivity | Bus-to-element mapping |

## Supported Profiles

| Profile | Standard | Purpose |
|---------|----------|---------|
| Equipment (EQ) | IEC 61970-452 | Grid topology |
| Topology (TP) | IEC 61970-456 | Connectivity |
| Steady-State Hypothesis (SSH) | IEC 61970-457 | Operational state |

## Relationships

- **Adapter:** `src/smart_meter_simulator/adapters/cim_adapter.py`
- **Grid model:** [[Pandapower Adapter]]
- **Thai networks:** [[Thai Grid Topology]]
- **Spatial data:** [[PostGIS Integration]]

## Known Issues

- Not all CIM classes supported (only core distribution elements)
- No GLM (GridLAB-D) format conversion
- RDF namespace handling may conflict with non-CIM triples
- CIM version 100 (IEC 61970-501) — not latest CIM 16+
