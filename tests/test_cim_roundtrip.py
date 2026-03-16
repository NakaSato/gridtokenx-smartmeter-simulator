import pytest
import pandapower as pp
from smart_meter_simulator.adapters.cim_adapter import CIMAdapter

def test_cim_roundtrip():
    """Verify that a network can be exported to CIM and re-imported accurately."""
    adapter = CIMAdapter(net_name="TestNetwork")
    
    # 1. Create a simple network
    net = pp.create_empty_network()
    b1 = pp.create_bus(net, vn_kv=0.4, name="Bus 1")
    b2 = pp.create_bus(net, vn_kv=0.4, name="Bus 2")
    pp.create_load(net, bus=b1, p_mw=0.1, q_mvar=0.03, name="Load 1")
    pp.create_load(net, bus=b2, p_mw=0.2, q_mvar=0.06, name="Load 2")
    
    # Add a measurement
    pp.create_measurement(net, "v", "bus", 1.0, 0.01, b1, name="M_V1")
    
    # 2. Export to XML
    xml_content = adapter.export_to_xml(net)
    assert "<cim:ConnectivityNode" in xml_content
    assert "<cim:EnergyConsumer" in xml_content
    
    # 3. Import back
    net_imported = adapter.load_from_xml(xml_content)
    
    # 4. Verify content
    assert len(net_imported.bus) == 2
    assert len(net_imported.load) == 2
    
    # Check bus names
    assert "Bus 1" in net_imported.bus.name.values
    assert "Bus 2" in net_imported.bus.name.values
    
    # Check load values
    l1 = net_imported.load[net_imported.load.name == "Load 1"].iloc[0]
    l2 = net_imported.load[net_imported.load.name == "Load 2"].iloc[0]
    
    assert l2.p_mw == 0.2
    assert l2.q_mvar == 0.06
    
    # Check measurement
    assert len(net_imported.measurement) == 1
    m = net_imported.measurement.iloc[0]
    assert m['measurement_type'] == "v"
    assert m['element_type'] == "bus"
    assert m['element'] == net_imported.bus[net_imported.bus.name == "Bus 1"].index[0]
    assert m['value'] == 1.0
    
    print("CIM Advanced Roundtrip Test Passed!")

if __name__ == "__main__":
    test_cim_roundtrip()
