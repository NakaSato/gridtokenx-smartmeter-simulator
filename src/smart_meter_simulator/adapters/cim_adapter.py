import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional, List
import xml.etree.ElementTree as ET
from datetime import datetime

logger = logging.getLogger(__name__)

class CIMAdapter:
    """
    Adapter for converting pandapower networks to CIM (IEC 61970) XML/RDF format.
    Supports export and import of buses, loads, and measurements.
    """
    
    CIM_NS = "http://iec.ch/TC57/2013/CIM-schema-cim16#"
    RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    
    def __init__(self, net_name: str = "GridTokenX_Substation"):
        self.net_name = net_name
        
    def load_from_xml(self, xml_content: str) -> Any:
        """
        Import a pandapower network from a CIM XML string.
        """
        import pandapower as pp
        net = pp.create_empty_network(name=self.net_name)
        
        root = ET.fromstring(xml_content)
        ns = {
            'cim': self.CIM_NS,
            'rdf': self.RDF_NS
        }
        
        # Mapping RDF ID to pandapower index
        bus_map = {} # rdf_id -> bus_idx
        load_map = {} # rdf_id -> load_idx
        
        # 1. Import Buses (ConnectivityNodes)
        for node in root.findall('.//cim:ConnectivityNode', ns):
            rdf_id = node.get(f"{{{self.RDF_NS}}}ID")
            name = node.find('cim:IdentifiedObject.name', ns).text
            vn_kv = float(node.find('cim:ConnectivityNode.baseVoltage', ns).text)
            
            bus_idx = pp.create_bus(net, vn_kv=vn_kv, name=name)
            bus_map[rdf_id] = bus_idx
            
        # 2. Import Loads (EnergyConsumers)
        for consumer in root.findall('.//cim:EnergyConsumer', ns):
            name = consumer.find('cim:IdentifiedObject.name', ns).text
            p_mw = float(consumer.find('cim:EnergyConsumer.p', ns).text)
            q_mvar = float(consumer.find('cim:EnergyConsumer.q', ns).text)
            
            # Find associated bus
            bus_ref_node = consumer.find('cim:Equipment.MemberOf_EquipmentContainer', ns)
            bus_rdf_id = bus_ref_node.get(f"{{{self.RDF_NS}}}resource")
            if bus_rdf_id and bus_rdf_id.startswith('#'):
                bus_rdf_id = bus_rdf_id[1:]
            
            bus_idx = bus_map.get(bus_rdf_id)
            if bus_idx is not None:
                load_idx = pp.create_load(net, bus=bus_idx, p_mw=p_mw, q_mvar=q_mvar, name=name)
                load_map[consumer.get(f"{{{self.RDF_NS}}}ID")] = load_idx
            else:
                logger.warning(f"Load {name} references unknown bus {bus_rdf_id}")
                
        # 2.5 Import Lines (ACLineSegments)
        for line_node in root.findall('.//cim:ACLineSegment', ns):
            name = line_node.find('cim:IdentifiedObject.name', ns).text
            # Try to get from/to bus from our custom tags or standard ones
            from_ref = line_node.find('cim:ACLineSegment.from_bus', ns)
            to_ref = line_node.find('cim:ACLineSegment.to_bus', ns)
            
            if from_ref is not None and to_ref is not None:
                from_id = from_ref.get(f"{{{self.RDF_NS}}}resource")
                to_id = to_ref.get(f"{{{self.RDF_NS}}}resource")
                if from_id.startswith('#'): from_id = from_id[1:]
                if to_id.startswith('#'): to_id = to_id[1:]
                
                from_idx = bus_map.get(from_id)
                to_idx = bus_map.get(to_id)
                
                if from_idx is not None and to_idx is not None:
                    # Simplified import
                    length = float(line_node.find('cim:Conductor.length', ns).text) if line_node.find('cim:Conductor.length', ns) is not None else 1.0
                    r_tot = float(line_node.find('cim:ACLineSegment.r', ns).text) if line_node.find('cim:ACLineSegment.r', ns) is not None else 0.1
                    x_tot = float(line_node.find('cim:ACLineSegment.x', ns).text) if line_node.find('cim:ACLineSegment.x', ns) is not None else 0.05
                    c_tot = float(line_node.find('cim:ACLineSegment.c', ns).text) if line_node.find('cim:ACLineSegment.c', ns) is not None else 0.0
                    
                    pp.create_line_from_parameters(
                        net, from_bus=from_idx, to_bus=to_idx, 
                        length_km=length, 
                        r_ohm_per_km=r_tot/length if length > 0 else r_tot, 
                        x_ohm_per_km=x_tot/length if length > 0 else x_tot, 
                        c_nf_per_km=c_tot/length if length > 0 else c_tot,
                        max_i_ka=1.0, name=name
                    )
                
        # 3. Import Measurements (Analogs)
        # First, find Analogs to get metadata
        analog_map = {} # rdf_id -> {name, type, psr_ref}
        for analog in root.findall('.//cim:Analog', ns):
            rdf_id = analog.get(f"{{{self.RDF_NS}}}ID")
            name = analog.find('cim:IdentifiedObject.name', ns).text
            m_type = analog.find('cim:Analog.unitSymbol', ns).text
            
            psr_node = analog.find('cim:Measurement.PowerSystemResource', ns)
            psr_ref = None
            if psr_node is not None:
                psr_ref = psr_node.get(f"{{{self.RDF_NS}}}resource")
                if psr_ref.startswith('#'):
                    psr_ref = psr_ref[1:]
            
            analog_map[rdf_id] = {'name': name, 'type': m_type, 'psr_ref': psr_ref}
            
        # Then, find AnalogValues and create pandapower measurements
        for val_node in root.findall('.//cim:AnalogValue', ns):
            value = float(val_node.find('cim:AnalogValue.value', ns).text)
            analog_ref = val_node.find('cim:AnalogValue.Analog', ns).get(f"{{{self.RDF_NS}}}resource")
            if analog_ref and analog_ref.startswith('#'):
                analog_ref = analog_ref[1:]
                
            meta = analog_map.get(analog_ref)
            if meta and meta['psr_ref']:
                psr_id = meta['psr_ref']
                # Determine element type and index
                element_type = None
                element_idx = None
                
                if psr_id in bus_map:
                    element_type = "bus"
                    element_idx = bus_map[psr_id]
                elif psr_id in load_map:
                    element_type = "load"
                    element_idx = load_map[psr_id]
                
                if element_type:
                    pp.create_measurement(
                        net, 
                        meas_type=meta['type'], 
                        element_type=element_type, 
                        value=value, 
                        std_dev=0.01, # Default
                        element=element_idx, 
                        name=meta['name']
                    )
                else:
                    logger.warning(f"Measurement {meta['name']} references unknown PSR {psr_id}")
                
        return net
        
    def export_to_xml(self, net: Any) -> str:
        """
        Export a pandapower network to a CIM XML string.
        """
        root = ET.Element(f"{{{self.RDF_NS}}}RDF")
        ET.register_namespace('cim', self.CIM_NS)
        ET.register_namespace('rdf', self.RDF_NS)
        
        # 1. Header/FullModel
        model = ET.SubElement(root, f"{{{self.RDF_NS}}}Description")
        model.set(f"{{{self.RDF_NS}}}about", f"#{self.net_name}")
        ET.SubElement(model, f"{{{self.CIM_NS}}}IdentifiedObject.name").text = self.net_name
        
        # 2. Export Buses (ConnectivityNodes)
        if hasattr(net, 'bus'):
            for idx, bus in net.bus.iterrows():
                node = ET.SubElement(root, f"{{{self.CIM_NS}}}ConnectivityNode")
                node.set(f"{{{self.RDF_NS}}}ID", f"_Bus_{idx}")
                ET.SubElement(node, f"{{{self.CIM_NS}}}IdentifiedObject.name").text = str(bus.get('name', f"Bus {idx}"))
                ET.SubElement(node, f"{{{self.CIM_NS}}}ConnectivityNode.baseVoltage").text = str(bus.get('vn_kv', 0.4))
                
        # 3. Export Loads (EnergyConsumers)
        if hasattr(net, 'load'):
            for idx, load in net.load.iterrows():
                consumer = ET.SubElement(root, f"{{{self.CIM_NS}}}EnergyConsumer")
                consumer.set(f"{{{self.RDF_NS}}}ID", f"_Load_{idx}")
                ET.SubElement(consumer, f"{{{self.CIM_NS}}}IdentifiedObject.name").text = str(load.get('name', f"Load {idx}"))
                ET.SubElement(consumer, f"{{{self.CIM_NS}}}EnergyConsumer.p").text = str(load.get('p_mw', 0))
                ET.SubElement(consumer, f"{{{self.CIM_NS}}}EnergyConsumer.q").text = str(load.get('q_mvar', 0))
                
                # Link to bus
                bus_ref = ET.SubElement(consumer, f"{{{self.CIM_NS}}}Equipment.MemberOf_EquipmentContainer")
                bus_ref.set(f"{{{self.RDF_NS}}}resource", f"#_Bus_{load.bus}")
                
        # 3.5 Export Lines (ACLineSegments)
        if hasattr(net, 'line'):
            for idx, line in net.line.iterrows():
                acline = ET.SubElement(root, f"{{{self.CIM_NS}}}ACLineSegment")
                acline.set(f"{{{self.RDF_NS}}}ID", f"_Line_{idx}")
                ET.SubElement(acline, f"{{{self.CIM_NS}}}IdentifiedObject.name").text = str(line.get('name', f"Line {idx}"))
                ET.SubElement(acline, f"{{{self.CIM_NS}}}ACLineSegment.r").text = str(line.get('r_ohm_per_km', 0) * line.get('length_km', 1))
                ET.SubElement(acline, f"{{{self.CIM_NS}}}ACLineSegment.x").text = str(line.get('x_ohm_per_km', 0) * line.get('length_km', 1))
                ET.SubElement(acline, f"{{{self.CIM_NS}}}ACLineSegment.c").text = str(line.get('c_nf_per_km', 0) * line.get('length_km', 1))
                ET.SubElement(acline, f"{{{self.CIM_NS}}}Conductor.length").text = str(line.get('length_km', 1))
                
                # In CIM, lines have two terminals. Here we use a simplified ref for from/to buses.
                from_ref = ET.SubElement(acline, f"{{{self.CIM_NS}}}ACLineSegment.from_bus")
                from_ref.set(f"{{{self.RDF_NS}}}resource", f"#_Bus_{line.from_bus}")
                to_ref = ET.SubElement(acline, f"{{{self.CIM_NS}}}ACLineSegment.to_bus")
                to_ref.set(f"{{{self.RDF_NS}}}resource", f"#_Bus_{line.to_bus}")
                
        # 4. Export Measurements (Analogs)
        if hasattr(net, 'measurement'):
            for idx, meas in net.measurement.iterrows():
                analog = ET.SubElement(root, f"{{{self.CIM_NS}}}Analog")
                analog.set(f"{{{self.RDF_NS}}}ID", f"_Meas_{idx}")
                ET.SubElement(analog, f"{{{self.CIM_NS}}}IdentifiedObject.name").text = str(meas.get('name', f"Meas {idx}"))
                ET.SubElement(analog, f"{{{self.CIM_NS}}}Analog.unitSymbol").text = meas.get('meas_type', 'v')
                
                # Link Analog to the element it measures (PowerSystemResource)
                element_type = meas.get('element_type')
                element_idx = meas.get('element')
                if element_type == 'bus':
                    psr_ref = ET.SubElement(analog, f"{{{self.CIM_NS}}}Measurement.PowerSystemResource")
                    psr_ref.set(f"{{{self.RDF_NS}}}resource", f"#_Bus_{element_idx}")
                elif element_type == 'load':
                    psr_ref = ET.SubElement(analog, f"{{{self.CIM_NS}}}Measurement.PowerSystemResource")
                    psr_ref.set(f"{{{self.RDF_NS}}}resource", f"#_Load_{element_idx}")
                
                value_node = ET.SubElement(root, f"{{{self.CIM_NS}}}AnalogValue")
                value_node.set(f"{{{self.RDF_NS}}}ID", f"_Value_{idx}")
                ET.SubElement(value_node, f"{{{self.CIM_NS}}}AnalogValue.value").text = str(meas.get('value', 0))
                
                # Link value to analog
                analog_ref = ET.SubElement(value_node, f"{{{self.CIM_NS}}}AnalogValue.Analog")
                analog_ref.set(f"{{{self.RDF_NS}}}resource", f"#_Meas_{idx}")
                
        return ET.tostring(root, encoding='unicode')

    def save_cim(self, net: Any, filename: str):
        """Save network to a CIM XML file."""
        xml_content = self.export_to_xml(net)
        with open(filename, 'w') as f:
            f.write(xml_content)
        logger.info(f"Exported CIM model to {filename}")
        return filename
