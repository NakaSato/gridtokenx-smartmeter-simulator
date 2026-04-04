# How to Adapt French Power Analysers for Thailand

## Step-by-Step Implementation Guide

This guide shows you exactly how to adapt the proven French electrical infrastructure analysers from OSMOSE backend for use in Thailand with MEA, PEA, and EGAT data.

---

## 📋 Overview

**What We're Adapting:**
- `analyser_merge_power_pole_FR_spec_enedis.py` → `analyser_merge_power_pole_TH_mea.py`
- `analyser_merge_power_line_FR.py` → `analyser_merge_power_line_TH_egat.py`
- `analyser_merge_power_substation_FR.py` → `analyser_merge_power_substation_TH.py`

**Key Changes:**
- French data sources → Thai data sources (EGAT/MEA/PEA)
- French administrative divisions → Thai provinces/districts
- European voltage standards → Thai voltage standards
- French operators (Enedis, RTE) → Thai operators (EGAT, MEA, PEA)

---

## 🔧 Step 1: Setup Thai Infrastructure Analyser

### Base Class Structure

```python
#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Thai Power Pole Analyser - MEA (Metropolitan Electricity Authority)

Adapted from: analyser_merge_power_pole_FR_spec_enedis.py
Copyright © 2025 GridTokenX Engineering Team

Validates power pole locations in Bangkok metropolitan area against MEA official data.
"""

from modules.OsmoseTranslation import T_
from .Analyser_Merge import Analyser_Merge_Point, SourceCSV, Load_XY, Conflate, Select, Mapping


class Analyser_Merge_power_pole_TH_MEA(Analyser_Merge_Point):
    def __init__(self, config, logger = None):
        Analyser_Merge_Point.__init__(self, config, logger)
        
        # Define issue classes (following OSMOSE pattern)
        classs = 1070
        self.def_class_missing_official(
            item = 8290, 
            id = classs + 1, 
            level = 3, 
            tags = ['merge', 'power', 'fix:chair', 'fix:survey'],
            title = T_('Power pole not integrated (MEA)')
        )
        self.def_class_possible_merge(
            item = 8291, 
            id = classs + 3, 
            level = 3, 
            tags = ['merge', 'power', 'fix:chair', 'fix:survey'],
            title = T_('Power pole integration suggestion')
        )
        self.def_class_update_official(
            item = 8292, 
            id = classs + 4, 
            level = 3, 
            tags = ['merge', 'power', 'fix:chair'],
            title = T_('Power pole update needed')
        )

        # Get Thai province code (10 = Bangkok)
        province_code = config.options.get('province_code') or '10'

        # Initialize with Thai data sources
        self.init(
            "https://data.go.th/dataset/mea-power-poles",  # Replace with actual URL
            "MEA Power Pole Locations - Bangkok Metropolitan",
            SourceCSV(
                url="https://data.go.th/dataset/mea-power-poles/resource/poles.csv",
                attribution="MEA (Metropolitan Electricity Authority)",
                encoding='utf-8'
            ),
            Load_XY(
                lat_field='Latitude',
                lon_field='Longitude',
                select={
                    "ProvinceCode": province_code,  # Bangkok = 10
                    "Precision": ["A", "B"],  # High precision only
                    "Voltage": ["22kV", "33kV"]  # MV distribution
                }
            ),
            Conflate(
                select=Select(
                    types=['nodes'],
                    tags=[
                        {"power": ["pole", "tower"]},
                        {"disused:power": ["pole", "tower"]},
                        {"removed:power": ["pole", "tower"]},
                    ]),
                conflationDistance=10,  # 10 meters for Thai data (less precise than France)
                mapping=Mapping(
                    static1={'power': 'pole'},
                    static2={
                        'source': self.source,
                        'operator': 'MEA',
                        'operator:wikidata': 'Q13116849'  # MEA Wikidata ID
                    },
                    mapping1={
                        'ref': lambda fields: f'MEA-{fields["PoleID"]}',
                        'voltage': lambda fields: str(int(fields["Voltage"].replace('kV', '')) * 1000)
                    },
                    text=lambda tags, fields: T_("MEA power pole {0} in {1}", 
                                               fields["PoleID"], 
                                               fields["District"])
                )
            )
        )
```

---

## 📊 Step 2: Prepare Thai Data Format

### CSV Data Structure

**French Format (Original):**
```csv
Code Département,Geo Point,PREC,Code Commune,Type
75,48.8566,2.3522,A : 0 - 50cm,75001
```

**Thai Format (Adapted):**
```csv
PoleID,ProvinceCode,Province,District,Subdistrict,Latitude,Longitude,Precision,Voltage,InstallYear,Type
MEA-001,10,Bangkok,Bang Rak,Talat Mai,13.8512,100.5923,A,22kV,2015,Concrete
MEA-002,10,Bangkok,Pathum Wan,Wang Mai,13.7465,100.5345,B,22kV,2010,Concrete
```

### Field Mapping

| French Field | Thai Field | Transformation |
|--------------|------------|----------------|
| `Code Département` | `ProvinceCode` | Direct mapping (75 → 10) |
| `Geo Point` | `Latitude,Longitude` | Split into separate fields |
| `PREC` | `Precision` | Simplify (A,B,C → A,B) |
| - | `Voltage` | Add Thai voltage (22kV, 33kV) |
| - | `InstallYear` | Add for asset management |
| - | `Type` | Add pole type (Concrete, Steel) |

---

## ⚡ Step 3: Configure Thai Voltage Standards

### Voltage Conversion

**French Voltages:**
```python
# France (Enedis)
voltage_mapping = {
    'HTA': 20000,      # High Tension A (20kV)
    'BT': 230,         # Low Tension (230V)
    '45kV': 45000,
}
```

**Thai Voltages:**
```python
# Thailand (MEA/PEA)
voltage_mapping = {
    '22kV': 22000,     # Standard MV distribution
    '33kV': 33000,     # Some provincial areas
    '115kV': 115000,   # Sub-transmission
    '230kV': 230000,   # Transmission (EGAT)
    '500kV': 500000,   # Transmission (EGAT)
    '400V': 400,       # LV three-phase
    '230V': 230,       # LV single-phase
}
```

### Implementation

```python
def thai_voltage_converter(voltage_str):
    """
    Convert Thai voltage string to numeric value.
    
    Examples:
        "22kV" → 22000
        "400V" → 400
        "500kV" → 500000
    """
    if not voltage_str:
        return None
    
    voltage_str = str(voltage_str).strip().upper()
    
    try:
        if voltage_str.endswith('KV'):
            return int(float(voltage_str[:-2]) * 1000)
        elif voltage_str.endswith('V'):
            return int(float(voltage_str[:-1]))
        else:
            # Assume kV if no unit
            return int(float(voltage_str) * 1000)
    except (ValueError, TypeError):
        return None


# Usage in analyser
mapping1 = {
    'voltage': lambda fields: thai_voltage_converter(fields.get('Voltage'))
}
```

---

## 🗺️ Step 4: Thai Administrative Divisions

### French System
```
Country → Region → Département → Commune
France  → Île-de-France → Paris (75) → Paris (75056)
```

### Thai System
```
Country → Province (จังหวัด) → District (อำเภอ) → Subdistrict (ตำบล)
Thailand → Bangkok → Bang Rak → Talat Mai
```

### Province Code Mapping

```python
THAI_PROVINCE_CODES = {
    'Bangkok': '10',
    'Samut Prakan': '11',
    'Nonthaburi': '12',
    'Pathum Thani': '13',
    'Phra Nakhon Si Ayutthaya': '14',
    'Ang Thong': '15',
    'Lopburi': '16',
    'Sing Buri': '17',
    'Chai Nat': '18',
    'Saraburi': '19',
    # ... more provinces
    'Chiang Mai': '50',
    'Chiang Rai': '57',
    # ... up to 77 provinces
}

# Usage in config
config = {
    'province_code': '10',  # Bangkok
    'province_name': 'Bangkok',
    'mea_service_area': True  # MEA serves Bangkok metro only
}
```

---

## 🏢 Step 5: Thai Operator Wikidata IDs

### Create/Use Wikidata Items

```python
# Thai utility operators
THAI_OPERATORS = {
    'EGAT': {
        'name': 'Electricity Generating Authority of Thailand',
        'wikidata': 'Q5353891',
        'type': 'transmission',
        'service_area': 'National (Transmission)'
    },
    'MEA': {
        'name': 'Metropolitan Electricity Authority',
        'wikidata': 'Q13116849',
        'type': 'distribution',
        'service_area': 'Bangkok, Nonthaburi, Samut Prakan'
    },
    'PEA': {
        'name': 'Provincial Electricity Authority',
        'wikidata': 'Q7385915',
        'type': 'distribution',
        'service_area': 'All other provinces'
    }
}

# Usage in analyser
static2 = {
    'operator': 'MEA',
    'operator:wikidata': 'Q13116849',
    'operator:type': 'distribution'
}
```

---

## 📏 Step 6: Adjust Conflation Distances

### French Standards (High Precision)
```python
# France - Very precise data
conflation_distances = {
    'power_pole': 6,      # 6 meters (±50cm precision)
    'power_line': 30,     # 30 meters
    'substation': 200,    # 200 meters (large facilities)
}
```

### Thai Standards (Moderate Precision)
```python
# Thailand - Less precise initially
conflation_distances = {
    'power_pole': 10,     # 10 meters (±5m precision expected)
    'power_line': 50,     # 50 meters
    'substation': 100,    # 100 meters
    'transmission_tower': 30,  # 30 meters
}
```

### Rationale

| Infrastructure | France | Thailand | Reason for Difference |
|----------------|--------|----------|----------------------|
| Power Pole | 6m | 10m | Thai data less precise initially |
| Power Line | 30m | 50m | Larger tolerance for rural areas |
| Substation | 200m | 100m | Similar facility sizes |
| Transmission Tower | 10m | 30m | EGAT data moderate precision |

---

## 🎯 Step 7: Complete Implementation Example

### Full Thai Power Pole Analyser

```python
#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Thai Power Pole Analyser - MEA (Metropolitan Electricity Authority)

Adapted from: analyser_merge_power_pole_FR_spec_enedis.py
For: GridTokenX Smart Meter Simulator - Phase 23

Validates power poles in Bangkok metropolitan area.
"""

from modules.OsmoseTranslation import T_
from .Analyser_Merge import Analyser_Merge_Point, SourceCSV, Load_XY, Conflate, Select, Mapping


class Analyser_Merge_power_pole_TH_MEA(Analyser_Merge_Point):
    """
    Validate MEA power poles against OSM data.
    
    Data Source: MEA (Metropolitan Electricity Authority)
    Coverage: Bangkok, Nonthaburi, Samut Prakan
    Precision: Class A (±5m), Class B (±10m)
    """
    
    def __init__(self, config, logger=None):
        Analyser_Merge_Point.__init__(self, config, logger)
        
        # Issue classification
        classs = 1070
        self.def_class_missing_official(
            item=8290, id=classs+1, level=3,
            tags=['merge', 'power', 'fix:chair', 'fix:survey'],
            title=T_('MEA power pole not integrated')
        )
        self.def_class_possible_merge(
            item=8291, id=classs+3, level=3,
            tags=['merge', 'power', 'fix:chair', 'fix:survey'],
            title=T_('Power pole integration suggestion')
        )
        self.def_class_update_official(
            item=8292, id=classs+4, level=3,
            tags=['merge', 'power', 'fix:chair'],
            title=T_('MEA power pole update needed')
        )

        # Get configuration
        province_code = config.options.get('province_code') or '10'  # Bangkok default
        
        # Helper function for voltage conversion
        def convert_thai_voltage(voltage_str):
            if not voltage_str:
                return None
            voltage_str = str(voltage_str).strip().upper()
            try:
                if voltage_str.endswith('KV'):
                    return str(int(float(voltage_str[:-2]) * 1000))
                elif voltage_str.endswith('V'):
                    return str(int(float(voltage_str[:-1])))
                return str(int(float(voltage_str) * 1000))
            except:
                return None

        # Initialize analyser
        self.init(
            # Data source
            "https://data.go.th/dataset/mea-power-poles",
            "MEA Power Pole Locations - Bangkok Metropolitan",
            SourceCSV(
                url="https://data.go.th/dataset/mea-power-poles/resource/poles.csv",
                attribution="Metropolitan Electricity Authority (MEA)",
                encoding='utf-8'
            ),
            
            # Data loading
            Load_XY(
                lat_field='Latitude',
                lon_field='Longitude',
                select={
                    "ProvinceCode": province_code,
                    "Precision": ["A", "B"],
                    "Voltage": ["22kV", "33kV", "115kV"]
                }
            ),
            
            # Conflation (matching with OSM)
            Conflate(
                select=Select(
                    types=['nodes'],
                    tags=[
                        {"power": ["pole", "tower"]},
                        {"disused:power": ["pole", "tower"]},
                    ]),
                conflationDistance=10,  # 10 meters
                mapping=Mapping(
                    static1={'power': 'pole'},
                    static2={
                        'source': self.source,
                        'operator': 'MEA',
                        'operator:wikidata': 'Q13116849'
                    },
                    mapping1={
                        'ref': lambda fields: f'MEA-{fields["PoleID"]}',
                        'voltage': lambda fields: convert_thai_voltage(fields.get('Voltage')),
                        'start_date': lambda fields: str(fields['InstallYear']) if fields.get('InstallYear') else None
                    },
                    text=lambda tags, fields: T_(
                        "MEA pole {0} ({1}), {2} District, {3}",
                        fields["PoleID"],
                        fields.get('Voltage', 'Unknown'),
                        fields.get('District', 'Unknown'),
                        fields.get('Precision', 'Unknown precision')
                    )
                )
            )
        )
```

---

## ✅ Step 8: Testing

### Test Configuration

```python
# test_config_thai_power.py

def test_thai_voltage_converter():
    """Test Thai voltage conversion function"""
    from analysers.analyser_merge_power_pole_TH_MEA import convert_thai_voltage
    
    # Test kV conversion
    assert convert_thai_voltage("22kV") == "22000"
    assert convert_thai_voltage("115kV") == "115000"
    assert convert_thai_voltage("500kV") == "500000"
    
    # Test V conversion
    assert convert_thai_voltage("400V") == "400"
    assert convert_thai_voltage("230V") == "230"
    
    # Test edge cases
    assert convert_thai_voltage(None) is None
    assert convert_thai_voltage("") is None
    assert convert_thai_voltage("invalid") is None


def test_mea_analyser_initialization():
    """Test MEA analyser initializes correctly"""
    from analysers.analyser_merge_power_pole_TH_MEA import Analyser_Merge_power_pole_TH_MEA
    
    config = MockConfig({
        'province_code': '10',
        'country': 'th'
    })
    
    analyser = Analyser_Merge_power_pole_TH_MEA(config)
    
    assert analyser is not None
    assert analyser.conflation_distance == 10
    assert analyser.operator == 'MEA'
```

---

## 📦 Step 9: Deployment

### Configuration File

```yaml
# config/thai_power_infrastructure.yaml

thai_power:
  enabled: true
  
  operators:
    EGAT:
      wikidata: Q5353891
      service_area: national
      voltage_levels: [500, 230, 115]
      
    MEA:
      wikidata: Q13116849
      service_area: ["Bangkok", "Nonthaburi", "Samut Prakan"]
      voltage_levels: [115, 22]
      
    PEA:
      wikidata: Q73875915
      service_area: all_other_provinces
      voltage_levels: [115, 22]
  
  conflation:
    power_pole: 10      # meters
    power_line: 50      # meters
    substation: 100     # meters
    transmission_tower: 30  # meters
  
  provinces:
    bangkok:
      code: "10"
      operator: MEA
      priority: high
      
    samut_prakan:
      code: "11"
      operator: MEA
      priority: high
      
    nonthaburi:
      code: "12"
      operator: MEA
      priority: high
      
    chiang_mai:
      code: "50"
      operator: PEA
      priority: medium
```

### Deployment Script

```bash
#!/bin/bash
# deploy_thai_power_analysers.sh

echo "Deploying Thai Power Infrastructure Analysers..."

# 1. Copy analyser files
cp analysers/analyser_merge_power_pole_TH_MEA.py /opt/osmose/analysers/
cp analysers/analyser_merge_power_line_TH_EGAT.py /opt/osmose/analysers/
cp analysers/analyser_merge_power_substation_TH.py /opt/osmose/analysers/

# 2. Copy configuration
cp config/thai_power_infrastructure.yaml /opt/osmose/config/

# 3. Update main config
cat >> /opt/osmose/osmose_config.py << EOF

# Thai Power Infrastructure
config["th"] = {
    "province_code": "10",
    "operators": ["EGAT", "MEA", "PEA"],
    "voltage_standards": {
        "transmission": [500, 230, 115],
        "distribution_mv": [22, 33],
        "distribution_lv": [0.4, 0.23]
    }
}
EOF

# 4. Restart OSMOSE service
systemctl restart osmose-backend

# 5. Verify deployment
echo "Verifying deployment..."
curl http://localhost:8080/api/status | grep -i "thai_power"

echo "Deployment complete!"
```

---

## 🎓 Summary: Key Adaptation Points

| Aspect | French Original | Thai Adaptation |
|--------|----------------|-----------------|
| **Data Source** | data.gouv.fr | data.go.th + Direct utility APIs |
| **Administrative** | Département (101) | Province (77) |
| **Operator** | Enedis (single) | MEA/PEA (dual) + EGAT |
| **Voltage** | 20kV MV | 22kV MV |
| **Precision** | ±50cm (Class A) | ±5m (initially) |
| **Conflation** | 6m (poles) | 10m (poles) |
| **Language** | French | Thai + English |
| **Encoding** | UTF-8 | UTF-8 (with Thai script support) |

---

## 📚 Next Steps

1. **Contact Utilities** - Request data from EGAT/MEA/PEA
2. **Prepare Sample Data** - Create test datasets
3. **Implement Analysers** - Use templates from this guide
4. **Test Locally** - Run with sample data
5. **Deploy to Staging** - Test with real OSM data
6. **Production Rollout** - Gradual deployment by province

---

**Version:** 1.0  
**Date:** 2024-03-30  
**Based on:** OSMOSE Backend `analyser_merge_power_pole_FR_spec_enedis.py`  
**Adapted for:** GridTokenX Smart Meter Simulator - Thailand
