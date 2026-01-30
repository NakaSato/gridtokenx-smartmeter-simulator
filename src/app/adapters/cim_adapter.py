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
    Supports basic export of buses, loads, and measurements.
    """
    
    CIM_NS = "http://iec.ch/TC57/2013/CIM-schema-cim16#"
    RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    
    def __init__(self, net_name: str = "GridTokenX_Substation"):
        self.net_name = net_name
        
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
                
        # 4. Export Measurements (Analogs)
        if hasattr(net, 'measurement'):
            for idx, meas in net.measurement.iterrows():
                analog = ET.SubElement(root, f"{{{self.CIM_NS}}}Analog")
                analog.set(f"{{{self.RDF_NS}}}ID", f"_Meas_{idx}")
                ET.SubElement(analog, f"{{{self.CIM_NS}}}IdentifiedObject.name").text = str(meas.get('name', f"Meas {idx}"))
                ET.SubElement(analog, f"{{{self.CIM_NS}}}Analog.unitSymbol").text = meas.get('meas_type', 'v')
                
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
