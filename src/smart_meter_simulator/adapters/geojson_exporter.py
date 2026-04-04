"""
GeoJSON Exporter for Pandapower Networks

Exports pandapower networks to GeoJSON format for web map visualization.
Compatible with Leaflet, Mapbox, and other GeoJSON-aware mapping libraries.

References:
- GeoJSON Spec: https://geojson.org/
- Open Infrastructure Map: https://openinframap.org/
"""

from typing import Dict, Any, List, Optional
import json
import pandas as pd

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False


class NetworkGeoJSONExporter:
    """
    Exports pandapower networks to GeoJSON for web visualization.
    
    Features:
    - Bus/substation markers
    - Line/cable routes
    - Transformer locations
    - Custom styling properties
    - Layer separation (MV/LV)
    
    Example:
        exporter = NetworkGeoJSONExporter()
        geojson = exporter.to_geojson(net)
        
        # Or save to file
        exporter.save_to_file(net, "network.geojson")
    """
    
    # Map power infrastructure types to Open Infrastructure Map style
    OIM_STYLE_MAP = {
        'substation': {
            'type': 'substation',
            'icon': 'substation',
            'color': '#ff6600',
            'radius': 8
        },
        'bus_mv': {
            'type': 'substation',
            'icon': 'substation',
            'color': '#ff9933',
            'radius': 6
        },
        'bus_lv': {
            'type': 'substation',
            'icon': 'substation',
            'color': '#ffcc00',
            'radius': 4
        },
        'line_mv': {
            'type': 'line',
            'voltage': '22000',
            'color': '#ff6600',
            'width': 3
        },
        'line_lv': {
            'type': 'line',
            'voltage': '400',
            'color': '#ffcc00',
            'width': 2
        },
        'transformer': {
            'type': 'transformer',
            'icon': 'transformer',
            'color': '#9933ff',
            'radius': 5
        }
    }
    
    def __init__(self, include_properties: bool = True):
        """
        Initialize GeoJSON exporter.
        
        Args:
            include_properties: Include pandapower properties in GeoJSON
        """
        self.include_properties = include_properties
    
    def to_geojson(
        self,
        net: 'pp.pandapowerNet',
        include_buses: bool = True,
        include_lines: bool = True,
        include_transformers: bool = True,
        voltage_threshold_kv: float = 1.0
    ) -> Dict[str, Any]:
        """
        Convert pandapower network to GeoJSON FeatureCollection.
        
        Args:
            net: Pandapower network
            include_buses: Include bus/substation markers
            include_lines: Include line/cable routes
            include_transformers: Include transformer markers
            voltage_threshold_kv: Threshold to distinguish MV vs LV (default 1.0 kV)
            
        Returns:
            GeoJSON FeatureCollection dictionary
        """
        features = []
        
        # Extract buses
        if include_buses and hasattr(net, 'bus') and len(net.bus) > 0:
            bus_features = self._extract_buses(net, voltage_threshold_kv)
            features.extend(bus_features)
        
        # Extract lines
        if include_lines and hasattr(net, 'line') and len(net.line) > 0:
            line_features = self._extract_lines(net, voltage_threshold_kv)
            features.extend(line_features)
        
        # Extract transformers
        if include_transformers and hasattr(net, 'trafo') and len(net.trafo) > 0:
            trafo_features = self._extract_transformers(net)
            features.extend(trafo_features)
        
        return {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'network_name': getattr(net, 'name', 'Unknown'),
                'num_buses': len(net.bus) if hasattr(net, 'bus') else 0,
                'num_lines': len(net.line) if hasattr(net, 'line') else 0,
                'num_transformers': len(net.trafo) if hasattr(net, 'trafo') else 0,
                'generator': 'Thai Grid Topology - GridTokenX'
            }
        }
    
    def _extract_buses(
        self,
        net: 'pp.pandapowerNet',
        voltage_threshold_kv: float
    ) -> List[Dict[str, Any]]:
        """Extract bus features from network."""
        features = []
        
        # Try to get coordinates from bus_geocoord or bus.geo
        has_geocoord = hasattr(net, 'bus_geocoord') and net.bus_geocoord is not None
        has_geo_column = 'geo' in net.bus.columns if hasattr(net, 'bus') else False
        
        for idx, bus in net.bus.iterrows():
            # Get coordinates
            lat, lon = None, None
            
            if has_geocoord and idx in net.bus_geocoord.index:
                # From bus_geocoord table (x=lon, y=lat)
                geo = net.bus_geocoord.loc[idx]
                lon = geo.get('x', geo.get('longitude'))
                lat = geo.get('y', geo.get('latitude'))
            elif has_geo_column:
                # From bus.geo column
                geo = bus['geo']
                if isinstance(geo, (tuple, list)) and len(geo) == 2:
                    lat, lon = geo
                elif isinstance(geo, dict):
                    lat = geo.get('latitude', geo.get('lat'))
                    lon = geo.get('longitude', geo.get('lon'))
            
            # Skip if no coordinates
            if lat is None or lon is None:
                continue
            
            # Determine voltage level
            vn_kv = bus.get('vn_kv', 0.4)
            is_mv = vn_kv >= voltage_threshold_kv
            
            # Build properties
            properties = {
                'name': bus.get('name', f'Bus {idx}'),
                'voltage_level_kv': vn_kv,
                'type': 'substation' if is_mv else 'bus',
                'layer': 'MV' if is_mv else 'LV',
                'zone': bus.get('zone', ''),
                'in_service': bus.get('in_service', True)
            }
            
            # Add style
            style = self.OIM_STYLE_MAP['bus_mv' if is_mv else 'bus_lv'].copy()
            properties.update(style)
            
            # Add extra properties
            if self.include_properties:
                for col in net.bus.columns:
                    if col not in ['name', 'geo', 'in_service']:
                        properties[f'bus_{col}'] = bus.get(col)
            
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [lon, lat]
                },
                'properties': properties
            })
        
        return features
    
    def _extract_lines(
        self,
        net: 'pp.pandapowerNet',
        voltage_threshold_kv: float
    ) -> List[Dict[str, Any]]:
        """Extract line features from network."""
        features = []
        
        # Need coordinates for from and to buses
        has_geocoord = hasattr(net, 'bus_geocoord') and net.bus_geocoord is not None
        has_geo_column = 'geo' in net.bus.columns
        
        for idx, line in net.line.iterrows():
            from_bus = line['from_bus']
            to_bus = line['to_bus']
            
            # Get coordinates for both buses
            from_coords = self._get_bus_coordinates(net, from_bus, has_geocoord, has_geo_column)
            to_coords = self._get_bus_coordinates(net, to_bus, has_geocoord, has_geo_column)
            
            # Skip if missing coordinates
            if from_coords is None or to_coords is None:
                continue
            
            from_lon, from_lat = from_coords
            to_lon, to_lat = to_coords
            
            # Determine voltage level from from_bus
            from_bus_data = net.bus.loc[from_bus]
            vn_kv = from_bus_data.get('vn_kv', 0.4)
            is_mv = vn_kv >= voltage_threshold_kv
            
            # Build properties
            properties = {
                'name': line.get('name', f'Line {idx}'),
                'voltage_level_kv': vn_kv,
                'type': 'line',
                'layer': 'MV' if is_mv else 'LV',
                'length_km': line.get('length_km', 0),
                'std_type': line.get('std_type', ''),
                'in_service': line.get('in_service', True)
            }
            
            # Add style
            style = self.OIM_STYLE_MAP['line_mv' if is_mv else 'line_lv'].copy()
            properties.update(style)
            
            # Add extra properties
            if self.include_properties:
                for col in net.line.columns:
                    if col not in ['name', 'in_service']:
                        properties[f'line_{col}'] = line.get(col)
            
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [
                        [from_lon, from_lat],
                        [to_lon, to_lat]
                    ]
                },
                'properties': properties
            })
        
        return features
    
    def _extract_transformers(
        self,
        net: 'pp.pandapowerNet'
    ) -> List[Dict[str, Any]]:
        """Extract transformer features from network."""
        features = []
        
        has_geocoord = hasattr(net, 'bus_geocoord') and net.bus_geocoord is not None
        has_geo_column = 'geo' in net.bus.columns
        
        for idx, trafo in net.trafo.iterrows():
            hv_bus = trafo['hv_bus']
            lv_bus = trafo['lv_bus']
            
            # Get coordinates (use HV bus location)
            hv_coords = self._get_bus_coordinates(net, hv_bus, has_geocoord, has_geo_column)
            
            if hv_coords is None:
                continue
            
            lon, lat = hv_coords
            
            # Build properties
            properties = {
                'name': trafo.get('name', f'Transformer {idx}'),
                'type': 'transformer',
                'sn_mva': trafo.get('sn_mva', 0),
                'vn_hv_kv': trafo.get('vn_hv_kv', 22),
                'vn_lv_kv': trafo.get('vn_lv_kv', 0.4),
                'in_service': trafo.get('in_service', True)
            }
            
            # Add style
            style = self.OIM_STYLE_MAP['transformer'].copy()
            properties.update(style)
            
            # Add extra properties
            if self.include_properties:
                for col in net.trafo.columns:
                    if col not in ['name', 'in_service']:
                        properties[f'trafo_{col}'] = trafo.get(col)
            
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [lon, lat]
                },
                'properties': properties
            })
        
        return features
    
    def _get_bus_coordinates(
        self,
        net: 'pp.pandapowerNet',
        bus_idx: int,
        has_geocoord: bool,
        has_geo_column: bool
    ) -> Optional[tuple]:
        """Get (lon, lat) coordinates for a bus."""
        lon, lat = None, None
        
        if has_geocoord and bus_idx in net.bus_geocoord.index:
            geo = net.bus_geocoord.loc[bus_idx]
            lon = geo.get('x', geo.get('longitude'))
            lat = geo.get('y', geo.get('latitude'))
        elif has_geo_column and bus_idx in net.bus.index:
            geo = net.bus.loc[bus_idx, 'geo']
            if geo is not None:
                # Handle JSON string format (pandapower stores geo as JSON string)
                if isinstance(geo, str):
                    try:
                        geo = json.loads(geo)
                    except json.JSONDecodeError:
                        return None
                
                # Handle GeoJSON-like format: {"coordinates":[lat,lon], "type":"Point"}
                if isinstance(geo, dict):
                    coords = geo.get('coordinates', [])
                    if len(coords) >= 2:
                        # GeoJSON stores as [lat, lon] in our case
                        lat = coords[0]
                        lon = coords[1]
                # Handle tuple/list format: (lat, lon)
                elif isinstance(geo, (tuple, list)) and len(geo) == 2:
                    lat, lon = geo
        
        if lat is not None and lon is not None:
            return (lon, lat)
        return None
    
    def to_geojson_string(
        self,
        net: 'pp.pandapowerNet',
        indent: int = 2,
        **kwargs
    ) -> str:
        """
        Convert network to GeoJSON string.
        
        Args:
            net: Pandapower network
            indent: JSON indentation level
            **kwargs: Passed to to_geojson()
            
        Returns:
            GeoJSON string
        """
        geojson = self.to_geojson(net, **kwargs)
        return json.dumps(geojson, indent=indent)
    
    def save_to_file(
        self,
        net: 'pp.pandapowerNet',
        filepath: str,
        **kwargs
    ):
        """
        Save network GeoJSON to file.
        
        Args:
            net: Pandapower network
            filepath: Output file path
            **kwargs: Passed to to_geojson()
        """
        geojson = self.to_geojson(net, **kwargs)
        
        # Custom JSON encoder to handle pandas NA types
        class PandasNAEncoder(json.JSONEncoder):
            def default(self, obj):
                import pandas as pd
                import numpy as np
                if pd.isna(obj):
                    return None
                if isinstance(obj, (pd.Int64Dtype, pd.Float64Dtype)):
                    return obj.tolist()
                if isinstance(obj, np.integer):
                    return int(obj)
                if isinstance(obj, np.floating):
                    return float(obj)
                return super().default(obj)
        
        with open(filepath, 'w') as f:
            json.dump(geojson, f, indent=2, cls=PandasNAEncoder)
    
    def create_layered_geojson(
        self,
        net: 'pp.pandapowerNet',
        voltage_threshold_kv: float = 1.0
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create separate GeoJSON FeatureCollections for each layer.
        
        Args:
            net: Pandapower network
            voltage_threshold_kv: MV/LV threshold
            
        Returns:
            Dictionary with layer names as keys
        """
        layers = {
            'MV_lines': self.to_geojson(
                net,
                include_buses=False,
                include_transformers=False,
                voltage_threshold_kv=voltage_threshold_kv
            ),
            'LV_lines': self.to_geojson(
                net,
                include_buses=False,
                include_transformers=False,
                voltage_threshold_kv=voltage_threshold_kv
            ),
            'substations': self.to_geojson(
                net,
                include_lines=False,
                include_transformers=False,
                voltage_threshold_kv=voltage_threshold_kv
            ),
            'transformers': self.to_geojson(
                net,
                include_buses=False,
                include_lines=False,
                voltage_threshold_kv=voltage_threshold_kv
            )
        }
        
        # Filter by layer in properties
        for layer_name, geojson in layers.items():
            if 'lines' in layer_name:
                target_layer = layer_name.split('_')[0]  # 'MV' or 'LV'
                geojson['features'] = [
                    f for f in geojson['features']
                    if f['properties'].get('layer') == target_layer
                ]
        
        return layers


def export_network_to_geojson(
    net: 'pp.pandapowerNet',
    filepath: Optional[str] = None,
    include_properties: bool = True
) -> str:
    """
    Convenience function to export network to GeoJSON.
    
    Args:
        net: Pandapower network
        filepath: Optional file path to save
        include_properties: Include pandapower properties
        
    Returns:
        GeoJSON string
    """
    exporter = NetworkGeoJSONExporter(include_properties=include_properties)
    
    if filepath:
        exporter.save_to_file(net, filepath)
    
    return exporter.to_geojson_string(net)
