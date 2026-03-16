import pytest
import pandapower as pp
from smart_meter_simulator.adapters.cim_adapter import CIMAdapter

def test_cim_export_import_buses_loads():
    # 1. Create a simple network
    net = pp.create_empty_network()
    b1 = pp.create_bus(net, vn_kv=0.4, name="Bus 1")
    b2 = pp.create_bus(net, vn_kv=0.4, name="Bus 2")
    pp.create_load(net, bus=b1, p_mw=0.05, q_mvar=0.01, name="Load 1")
    
    # 2. Export to CIM
    adapter = CIMAdapter()
    xml_content = adapter.export_to_xml(net)
    assert "<cim:ConnectivityNode" in xml_content
    assert "<cim:EnergyConsumer" in xml_content
    
    # 3. Import back
    new_net = adapter.load_from_xml(xml_content)
    
    # 4. Verify parity
    assert len(new_net.bus) == 2
    assert len(new_net.load) == 1
    assert new_net.load.p_mw.iloc[0] == pytest.approx(0.05)
    assert new_net.load.name.iloc[0] == "Load 1"

def test_cim_lines_supported():
    # Verify that lines ARE now supported
    net = pp.create_empty_network()
    b1 = pp.create_bus(net, vn_kv=0.4, name="Bus 1")
    b2 = pp.create_bus(net, vn_kv=0.4, name="Bus 2")
    pp.create_line_from_parameters(net, from_bus=b1, to_bus=b2, length_km=0.1, r_ohm_per_km=0.32, x_ohm_per_km=0.08, c_nf_per_km=210, max_i_ka=0.2, name="Line 1")
    
    adapter = CIMAdapter()
    xml_content = adapter.export_to_xml(net)
    
    assert "ACLineSegment" in xml_content
    
    # Import back
    new_net = adapter.load_from_xml(xml_content)
    assert len(new_net.line) == 1
    assert new_net.line.name.iloc[0] == "Line 1"
    # Note: length is 1.0 in my current simplified import, but R/X should be preserved as absolute values
    assert new_net.line.r_ohm_per_km.iloc[0] == pytest.approx(0.32)
    assert new_net.line.length_km.iloc[0] == pytest.approx(0.1)
