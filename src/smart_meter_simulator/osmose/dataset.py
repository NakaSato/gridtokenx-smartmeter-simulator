"""
OSMOSE Dataset Module

Provides sample datasets, test data generators, and real-world OSM data loaders
for validation testing and demonstration.
"""

from typing import Dict, Any, List, Optional
import json
import random
from datetime import datetime


class OSMOSEDataset:
    """
    Dataset manager for OSMOSE validation.
    
    Provides:
    - Sample OSM data for testing
    - Test data generators
    - Real-world data loaders
    - Dataset export/import
    """
    
    def __init__(self):
        self.datasets: Dict[str, Dict[str, Any]] = {}
        self.current_dataset: Optional[str] = None
    
    def load_sample(self, name: str) -> Dict[str, Any]:
        """Load a sample dataset by name"""
        if name == "thailand_power":
            return self._thailand_power_sample()
        elif name == "bangkok_substation":
            return self._bangkok_substation_sample()
        elif name == "power_line_network":
            return self._power_line_network_sample()
        elif name == "validation_errors":
            return self._validation_errors_sample()
        else:
            raise ValueError(f"Unknown dataset: {name}")
    
    def _thailand_power_sample(self) -> Dict[str, Any]:
        """
        Sample power infrastructure data for Thailand.
        
        Includes:
        - EGAT transmission towers (500kV, 230kV)
        - MEA/PEA distribution poles (22kV)
        - Substations
        - Transformers
        """
        return {
            "metadata": {
                "name": "Thailand Power Infrastructure Sample",
                "country": "th",
                "region": "Central Thailand",
                "bbox": {
                    "north": 14.5,
                    "south": 13.0,
                    "east": 101.0,
                    "west": 100.0,
                },
                "created": datetime.utcnow().isoformat() + "Z",
                "source": "OpenStreetMap",
            },
            "nodes": [
                # EGAT 500kV Tower
                {
                    "id": 1001,
                    "lat": 14.2563,
                    "lon": 100.5018,
                    "tags": {
                        "power": "tower",
                        "tower:type": "lattice",
                        "line_management": "straight",
                        "line_arrangement": "horizontal",
                        "voltage": "500000",
                        "operator": "EGAT",
                    }
                },
                # EGAT 230kV Tower
                {
                    "id": 1002,
                    "lat": 14.2570,
                    "lon": 100.5025,
                    "tags": {
                        "power": "tower",
                        "tower:type": "lattice",
                        "line_management": "branch",
                        "line_arrangement": "horizontal",
                        "voltage": "230000",
                        "operator": "EGAT",
                    }
                },
                # MEA Distribution Pole
                {
                    "id": 1003,
                    "lat": 14.2580,
                    "lon": 100.5030,
                    "tags": {
                        "power": "pole",
                        "pole:type": "distribution",
                        "line_management": "termination",
                        "line_arrangement": "horizontal",
                        "voltage": "22000",
                        "material": "concrete",
                        "operator": "MEA",
                    }
                },
                # Transformer (with error - should use voltage:primary/secondary)
                {
                    "id": 1004,
                    "lat": 14.2590,
                    "lon": 100.5040,
                    "tags": {
                        "power": "transformer",
                        "voltage": "115000",  # ERROR: Should use voltage:primary/secondary
                    }
                },
                # Substation
                {
                    "id": 1005,
                    "lat": 14.2600,
                    "lon": 100.5050,
                    "tags": {
                        "power": "substation",
                        "substation": "transmission",
                        "voltage": "115000",
                        "operator": "EGAT",
                        "name": "สถานีไฟฟ้าแรงสูงบางปะอิน",
                    }
                },
                # Tower missing line_management (error)
                {
                    "id": 1006,
                    "lat": 14.2610,
                    "lon": 100.5060,
                    "tags": {
                        "power": "tower",
                        "tower:type": "lattice",
                        "voltage": "115000",
                        # MISSING: line_management
                    }
                },
            ],
            "ways": [
                # 500kV Power Line
                {
                    "id": 2001,
                    "nodes": [1001, 1002],
                    "tags": {
                        "power": "line",
                        "voltage": "500000",
                        "cables": "3",
                        "circuits": "1",
                        "frequency": "50",
                        "operator": "EGAT",
                    }
                },
                # 22kV Distribution Line
                {
                    "id": 2002,
                    "nodes": [1002, 1003],
                    "tags": {
                        "power": "minor_line",
                        "voltage": "22000",
                        "cables": "3",
                        "circuits": "1",
                        "operator": "MEA",
                    }
                },
                # Power line missing voltage (error)
                {
                    "id": 2003,
                    "nodes": [1003, 1004],
                    "tags": {
                        "power": "line",
                        "cables": "3",
                        # MISSING: voltage
                    }
                },
                # Transformer as way (error - should be node)
                {
                    "id": 2004,
                    "nodes": [1004, 1005],
                    "tags": {
                        "power": "transformer",  # ERROR: Should be node
                    }
                },
            ],
            "relations": [
                # Transformer as relation (error - should be node)
                {
                    "id": 3001,
                    "members": [
                        {"type": "node", "ref": 1004, "role": "transformer"}
                    ],
                    "tags": {
                        "power": "transformer",  # ERROR: Should be node
                        "type": "site",
                    }
                },
            ],
            "statistics": {
                "total_nodes": 6,
                "total_ways": 4,
                "total_relations": 1,
                "power_towers": 3,
                "power_poles": 1,
                "power_lines": 3,
                "substations": 1,
                "transformers": 3,
            }
        }
    
    def _bangkok_substation_sample(self) -> Dict[str, Any]:
        """
        Sample substation data for Bangkok area.
        """
        return {
            "metadata": {
                "name": "Bangkok Substation Sample",
                "country": "th",
                "region": "Bangkok Metropolitan",
                "bbox": {
                    "north": 13.8,
                    "south": 13.7,
                    "east": 100.6,
                    "west": 100.5,
                },
            },
            "nodes": [
                {
                    "id": 5001,
                    "lat": 13.7563,
                    "lon": 100.5018,
                    "tags": {
                        "power": "substation",
                        "substation": "distribution",
                        "voltage": "115000",
                        "operator": "MEA",
                        "name": "สถานีไฟฟ้าชิดลม",
                    }
                },
                {
                    "id": 5002,
                    "lat": 13.7570,
                    "lon": 100.5025,
                    "tags": {
                        "power": "transformer",
                        "voltage:primary": "115000",
                        "voltage:secondary": "22000",
                        "rating": "50 MVA",
                    }
                },
            ],
            "ways": [],
            "relations": [],
        }
    
    def _power_line_network_sample(self) -> Dict[str, Any]:
        """
        Sample power line network with complete topology.
        """
        # Generate a network of towers connected by power lines
        nodes = []
        ways = []
        
        # Create grid of towers
        for i in range(5):
            for j in range(5):
                lat = 14.0 + i * 0.05
                lon = 100.0 + j * 0.05
                
                node = {
                    "id": 10000 + i * 5 + j,
                    "lat": lat,
                    "lon": lon,
                    "tags": {
                        "power": "tower",
                        "tower:type": "lattice",
                        "voltage": "115000",
                    }
                }
                
                # Add line_management based on position
                if i == 0:
                    node["tags"]["line_management"] = "termination"
                elif i == 4:
                    node["tags"]["line_management"] = "termination"
                elif j == 0 or j == 4:
                    node["tags"]["line_management"] = "branch"
                else:
                    node["tags"]["line_management"] = "straight"
                
                nodes.append(node)
        
        # Connect towers with power lines
        for i in range(5):
            for j in range(4):
                way = {
                    "id": 20000 + i * 4 + j,
                    "nodes": [
                        10000 + i * 5 + j,
                        10000 + i * 5 + j + 1,
                    ],
                    "tags": {
                        "power": "line",
                        "voltage": "115000",
                        "cables": "3",
                        "circuits": "1",
                    }
                }
                ways.append(way)
        
        return {
            "metadata": {
                "name": "Power Line Network Sample",
                "description": "5x5 grid of transmission towers",
            },
            "nodes": nodes,
            "ways": ways,
            "relations": [],
            "statistics": {
                "total_nodes": len(nodes),
                "total_ways": len(ways),
            }
        }
    
    def _validation_errors_sample(self) -> Dict[str, Any]:
        """
        Sample data with intentional validation errors for testing.
        """
        return {
            "metadata": {
                "name": "Validation Errors Sample",
                "description": "Dataset with common validation errors",
            },
            "nodes": [
                # Error 91002: Transformer with voltage instead of voltage:primary/secondary
                {
                    "id": 9001,
                    "lat": 13.75,
                    "lon": 100.50,
                    "tags": {
                        "power": "transformer",
                        "voltage": "115000",  # ERROR
                    }
                },
                # Error 91201: Tower missing type
                {
                    "id": 9002,
                    "lat": 13.76,
                    "lon": 100.51,
                    "tags": {
                        "power": "tower",
                        "voltage": "115000",
                        # MISSING: tower:type
                    }
                },
                # Error 91202: Pole missing line_management
                {
                    "id": 9003,
                    "lat": 13.77,
                    "lon": 100.52,
                    "tags": {
                        "power": "pole",
                        "voltage": "22000",
                        # MISSING: line_management
                    }
                },
                # Error 91301: Substation missing voltage
                {
                    "id": 9004,
                    "lat": 13.78,
                    "lon": 100.53,
                    "tags": {
                        "power": "substation",
                        "substation": "distribution",
                        # MISSING: voltage
                    }
                },
                # Error 91302: Substation missing type
                {
                    "id": 9005,
                    "lat": 13.79,
                    "lon": 100.54,
                    "tags": {
                        "power": "substation",
                        "voltage": "115000",
                        # MISSING: substation type
                    }
                },
            ],
            "ways": [
                # Error 91001: Transformer as way
                {
                    "id": 9101,
                    "nodes": [9001, 9002],
                    "tags": {
                        "power": "transformer",  # ERROR
                    }
                },
                # Error 91101: Line missing voltage
                {
                    "id": 9102,
                    "nodes": [9002, 9003],
                    "tags": {
                        "power": "line",
                        "cables": "3",
                        # MISSING: voltage
                    }
                },
                # Error 91102: Wrong voltage format
                {
                    "id": 9103,
                    "nodes": [9003, 9004],
                    "tags": {
                        "power": "line",
                        "voltage": "115kV",  # ERROR: Should be 115000
                        "cables": "3",
                    }
                },
                # Error 91103: Line missing cables
                {
                    "id": 9104,
                    "nodes": [9004, 9005],
                    "tags": {
                        "power": "line",
                        "voltage": "115000",
                        # MISSING: cables
                    }
                },
            ],
            "relations": [
                # Error 91001: Transformer as relation
                {
                    "id": 9201,
                    "members": [],
                    "tags": {
                        "power": "transformer",  # ERROR
                        "type": "site",
                    }
                },
            ],
            "expected_errors": {
                "91001": 2,  # Transformer as way/relation
                "91002": 1,  # Wrong transformer voltage tagging
                "91101": 1,  # Missing voltage on line
                "91102": 1,  # Wrong voltage format
                "91103": 1,  # Missing cables
                "91201": 1,  # Missing tower:type
                "91202": 1,  # Missing line_management
                "91301": 1,  # Missing substation voltage
                "91302": 1,  # Missing substation type
            }
        }
    
    def generate_test_data(self, count: int = 100, 
                          error_rate: float = 0.3) -> Dict[str, Any]:
        """
        Generate random test data for validation.
        
        Args:
            count: Number of objects to generate
            error_rate: Fraction of objects with validation errors
            
        Returns:
            Generated OSM data
        """
        nodes = []
        ways = []
        
        # Generate towers
        for i in range(count // 3):
            lat = 13.5 + random.random() * 1.0
            lon = 100.0 + random.random() * 1.0
            
            has_error = random.random() < error_rate
            
            node = {
                "id": 100000 + i,
                "lat": lat,
                "lon": lon,
                "tags": {
                    "power": "tower",
                    "tower:type": random.choice(["lattice", "tubular", "guyed"]),
                    "voltage": random.choice(["115000", "230000", "500000"]),
                }
            }
            
            if not has_error:
                node["tags"]["line_management"] = random.choice([
                    "straight", "branch", "termination", "split"
                ])
                node["tags"]["line_arrangement"] = random.choice([
                    "horizontal", "vertical", "triangle"
                ])
            
            nodes.append(node)
        
        # Generate poles
        for i in range(count // 3):
            lat = 13.5 + random.random() * 1.0
            lon = 100.0 + random.random() * 1.0
            
            has_error = random.random() < error_rate
            
            node = {
                "id": 200000 + i,
                "lat": lat,
                "lon": lon,
                "tags": {
                    "power": "pole",
                    "pole:type": "distribution",
                    "voltage": "22000",
                    "material": random.choice(["concrete", "wood", "steel"]),
                }
            }
            
            if not has_error:
                node["tags"]["line_management"] = random.choice([
                    "straight", "branch", "termination"
                ])
            
            nodes.append(node)
        
        # Generate power lines
        for i in range(count // 3):
            has_error = random.random() < error_rate
            
            way = {
                "id": 300000 + i,
                "nodes": [
                    random.randint(100000, 299999),
                    random.randint(100000, 299999),
                ],
                "tags": {
                    "power": random.choice(["line", "minor_line"]),
                }
            }
            
            if not has_error:
                way["tags"]["voltage"] = random.choice([
                    "115000", "230000", "22000"
                ])
                way["tags"]["cables"] = str(random.choice([3, 6, 9]))
            
            ways.append(way)
        
        return {
            "metadata": {
                "name": "Generated Test Data",
                "count": count,
                "error_rate": error_rate,
            },
            "nodes": nodes,
            "ways": ways,
            "relations": [],
        }
    
    def to_geojson(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OSM data to GeoJSON"""
        features = []
        
        # Convert nodes
        for node in data.get("nodes", []):
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [node["lon"], node["lat"]],
                },
                "properties": {
                    "id": node["id"],
                    "type": "node",
                    **node.get("tags", {})
                }
            })
        
        # Convert ways (simplified as linestrings)
        # In production, would need to lookup node coordinates
        for way in data.get("ways", []):
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[0, 0], [1, 1]],  # Placeholder
                },
                "properties": {
                    "id": way["id"],
                    "type": "way",
                    **way.get("tags", {})
                }
            })
        
        return {
            "type": "FeatureCollection",
            "features": features,
        }
    
    def save(self, data: Dict[str, Any], filepath: str):
        """Save dataset to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Dataset saved to {filepath}")
    
    def load(self, filepath: str) -> Dict[str, Any]:
        """Load dataset from JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def list_samples(self) -> List[str]:
        """List available sample datasets"""
        return [
            "thailand_power",
            "bangkok_substation",
            "power_line_network",
            "validation_errors",
        ]


# Global dataset instance
dataset = OSMOSEDataset()


def get_sample(name: str) -> Dict[str, Any]:
    """Get sample dataset by name"""
    return dataset.load_sample(name)


def generate_test(count: int = 100, error_rate: float = 0.3) -> Dict[str, Any]:
    """Generate test data"""
    return dataset.generate_test_data(count, error_rate)
