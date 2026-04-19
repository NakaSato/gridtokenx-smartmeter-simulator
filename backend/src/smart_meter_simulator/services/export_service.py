"""
Grid Export Service

Handles conversion of grid data into exchange formats such as CIM (IEC 61970).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GridExportService:
    """
    Service for exporting grid topology and state in standardized formats.
    """

    @staticmethod
    def generate_cim_rdf(engine) -> str:
        """
        Generate CIM RDF/XML (IEC 61970) from the current pandapower network.
        """
        if not engine or not engine.net:
            return ""

        net = engine.net
        rdf = '<?xml version="1.0" encoding="UTF-8"?>\n'
        rdf += '<rdf:RDF xmlns:cim="http://iec.ch/TC57/CIM100#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'

        # 1. Base Voltages
        if hasattr(net, "bus") and len(net.bus) > 0:
            for idx, row in net.bus.iterrows():
                rdf += f'  <cim:BaseVoltage rdf:ID="BV_{idx}">\n'
                rdf += f'    <cim:BaseVoltage.nominalVoltage>{row.vn_kv * 1000:.0f}</cim:BaseVoltage.nominalVoltage>\n'
                rdf += f"  </cim:BaseVoltage>\n"

        # 2. Generating Units (Static Generators)
        if hasattr(net, "sgen") and len(net.sgen) > 0:
            for idx, row in net.sgen.iterrows():
                rdf += f'  <cim:SynchronousMachine rdf:ID="SGEN_{idx}">\n'
                rdf += f'    <cim:SynchronousMachine.p>{row.p_mw * 1000:.2f}</cim:SynchronousMachine.p>\n'
                if "sn_mw" in row:
                    rdf += f'    <cim:SynchronousMachine.ratedS>{row.sn_mw * 1000:.2f}</cim:SynchronousMachine.ratedS>\n'
                rdf += f"  </cim:SynchronousMachine>\n"

        # 3. Energy Consumers (Loads)
        if hasattr(net, "load") and len(net.load) > 0:
            for idx, row in net.load.iterrows():
                rdf += f'  <cim:EnergyConsumer rdf:ID="LOAD_{idx}">\n'
                rdf += f'    <cim:EnergyConsumer.pFixed>{row.p_mw * 1000:.2f}</cim:EnergyConsumer.pFixed>\n'
                rdf += f"  </cim:EnergyConsumer>\n"

        # 4. Power Transformers
        if hasattr(net, "trafo") and len(net.trafo) > 0:
            for idx, row in net.trafo.iterrows():
                rdf += f'  <cim:PowerTransformer rdf:ID="TRF_{idx}">\n'
                rdf += f'    <cim:PowerTransformer.u1>{row.vn_hv_kv * 1000:.0f}</cim:PowerTransformer.u1>\n'
                rdf += f'    <cim:PowerTransformer.u2>{row.vn_lv_kv * 1000:.0f}</cim:PowerTransformer.u2>\n'
                rdf += f"  </cim:PowerTransformer>\n"

        rdf += "</rdf:RDF>\n"
        return rdf
