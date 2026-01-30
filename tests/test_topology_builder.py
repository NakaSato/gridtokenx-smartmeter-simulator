"""
Tests for TopologyBuilder - Phase 2

Tests network topology creation with various configurations.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import pandapower as pp
    from app.adapters.topology_builder import (
        TopologyBuilder,
        VoltageLevel,
        NetworkTopology,
        BusConfig,
        LineConfig,
        TransformerConfig
    )
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not PANDAPOWER_AVAILABLE,
    reason="pandapower not installed"
)


class TestTopologyBuilder:
    """Test suite for TopologyBuilder class."""
    
    def test_create_empty_network(self):
        """Test creating an empty network."""
        builder = TopologyBuilder(network_name="Test Network")
        net = builder.create_network()
        
        assert net is not None
        assert len(net.bus) == 0
        assert len(net.line) == 0
        assert builder.net == net
    
    def test_add_single_bus(self):
        """Test adding a single bus."""
        builder = TopologyBuilder()
        builder.create_network()
        
        config = BusConfig(
            bus_id="TestBus_1",
            voltage_level=VoltageLevel.LV,
            vn_kv=0.4,
            name="Test Bus 1"
        )
        
        bus_idx = builder.add_bus(config)
        
        assert bus_idx == 0
        assert len(builder.net.bus) == 1
        assert builder.get_bus_index("TestBus_1") == 0
        assert builder.net.bus.loc[bus_idx, 'vn_kv'] == 0.4
        assert builder.net.bus.loc[bus_idx, 'name'] == "Test Bus 1"
    
    def test_add_duplicate_bus(self):
        """Test that adding duplicate bus returns existing index."""
        builder = TopologyBuilder()
        builder.create_network()
        
        config = BusConfig(
            bus_id="DupBus",
            voltage_level=VoltageLevel.LV,
            vn_kv=0.4
        )
        
        idx1 = builder.add_bus(config)
        idx2 = builder.add_bus(config)  # Should return same index
        
        assert idx1 == idx2
        assert len(builder.net.bus) == 1  # Only one bus created
    
    def test_add_line_between_buses(self):
        """Test adding a line connection."""
        builder = TopologyBuilder()
        builder.create_network()
        
        # Create two buses
        builder.add_bus(BusConfig("Bus1", VoltageLevel.LV, 0.4))
        builder.add_bus(BusConfig("Bus2", VoltageLevel.LV, 0.4))
        
        # Add line
        line_config = LineConfig(
            from_bus_id="Bus1",
            to_bus_id="Bus2",
            length_km=0.5,
            std_type="NAYY 4x50 SE"
        )
        
        line_idx = builder.add_line(line_config)
        
        assert line_idx == 0
        assert len(builder.net.line) == 1
        assert builder.net.line.loc[line_idx, 'length_km'] == 0.5
    
    def test_add_line_without_buses_raises_error(self):
        """Test that adding line without buses raises error."""
        builder = TopologyBuilder()
        builder.create_network()
        
        line_config = LineConfig(
            from_bus_id="NonexistentBus1",
            to_bus_id="NonexistentBus2",
            length_km=0.1
        )
        
        with pytest.raises(ValueError, match="Buses must exist"):
            builder.add_line(line_config)
    
    def test_add_transformer(self):
        """Test adding a transformer."""
        builder = TopologyBuilder()
        builder.create_network()
        
        # Create HV and LV buses
        builder.add_bus(BusConfig("HV_Bus", VoltageLevel.HV, 110.0))
        builder.add_bus(BusConfig("LV_Bus", VoltageLevel.LV, 0.4))
        
        # Add transformer
        trafo_config = TransformerConfig(
            hv_bus_id="HV_Bus",
            lv_bus_id="LV_Bus",
            sn_mva=10.0,
            vn_hv_kv=110.0,
            vn_lv_kv=0.4
        )
        
        trafo_idx = builder.add_transformer(trafo_config)
        
        assert trafo_idx == 0
        assert len(builder.net.trafo) == 1
        assert builder.net.trafo.loc[trafo_idx, 'sn_mva'] == 10.0
    
    def test_add_external_grid(self):
        """Test adding external grid connection."""
        builder = TopologyBuilder()
        builder.create_network()
        
        builder.add_bus(BusConfig("GridBus", VoltageLevel.MV, 10.0))
        ext_grid_idx = builder.add_external_grid("GridBus", vm_pu=1.0)
        
        assert ext_grid_idx == 0
        assert len(builder.net.ext_grid) == 1
        assert builder.net.ext_grid.loc[ext_grid_idx, 'vm_pu'] == 1.0


class TestRadialNetwork:
    """Test radial network topology."""
    
    def test_build_radial_lv_network(self):
        """Test building simple LV radial network."""
        builder = TopologyBuilder()
        net = builder.build_radial_network(
            num_buses=5,
            voltage_kv=0.4,
            line_length_km=0.1
        )
        
        assert len(net.bus) == 5
        assert len(net.line) == 4  # n-1 lines for radial
        assert len(net.ext_grid) == 1
        assert all(net.bus['vn_kv'] == 0.4)
    
    def test_build_radial_mv_network(self):
        """Test building MV radial network."""
        builder = TopologyBuilder()
        net = builder.build_radial_network(
            num_buses=10,
            voltage_kv=10.0,
            line_length_km=0.5
        )
        
        assert len(net.bus) == 10
        assert len(net.line) == 9
        assert all(net.bus['vn_kv'] == 10.0)
    
    def test_radial_without_grid(self):
        """Test radial network without external grid."""
        builder = TopologyBuilder()
        net = builder.build_radial_network(
            num_buses=3,
            voltage_kv=0.4,
            add_grid=False
        )
        
        assert len(net.bus) == 3
        assert len(net.ext_grid) == 0  # No grid


class TestFeederNetwork:
    """Test multi-feeder network topology."""
    
    def test_build_feeder_network(self):
        """Test building multi-feeder network."""
        builder = TopologyBuilder()
        net = builder.build_feeder_network(
            num_feeders=3,
            buses_per_feeder=5,
            voltage_kv=0.4
        )
        
        # 1 substation + (3 feeders × 5 buses) = 16 buses
        assert len(net.bus) == 16
        
        # 3 feeders × (1 connection to sub + 4 internal) = 15 lines
        assert len(net.line) == 15
        
        # 1 external grid at substation
        assert len(net.ext_grid) == 1
        
        # Check zones
        zones = net.bus['zone'].unique()
        assert 'Substation' in zones
        assert 'Feeder_0' in zones
        assert 'Feeder_2' in zones
    
    def test_feeder_bus_naming(self):
        """Test feeder bus naming convention."""
        builder = TopologyBuilder()
        net = builder.build_feeder_network(
            num_feeders=2,
            buses_per_feeder=3,
            voltage_kv=0.4
        )
        
        # Check bus IDs exist
        assert builder.get_bus_index("Substation") is not None
        assert builder.get_bus_index("Feeder0_Bus0") is not None
        assert builder.get_bus_index("Feeder1_Bus2") is not None


class TestMultiVoltageNetwork:
    """Test multi-voltage level network."""
    
    def test_build_multi_voltage_network(self):
        """Test building HV/MV/LV network."""
        builder = TopologyBuilder()
        net = builder.build_multi_voltage_network(
            hv_buses=1,
            mv_buses=2,
            lv_buses_per_mv=3,
            hv_voltage_kv=110.0,
            mv_voltage_kv=10.0,
            lv_voltage_kv=0.4
        )
        
        # 1 HV + 2 MV + (2×3) LV = 9 buses
        assert len(net.bus) == 9
        
        # 2 HV/MV transformers + (2×3) MV/LV transformers = 8 transformers
        assert len(net.trafo) == 8
        
        # Check voltage levels
        voltage_levels = sorted(net.bus['vn_kv'].unique())
        assert voltage_levels == [0.4, 10.0, 110.0]
    
    def test_transformer_connections(self):
        """Test transformer voltage ratios."""
        builder = TopologyBuilder()
        net = builder.build_multi_voltage_network(
            hv_buses=1,
            mv_buses=1,
            lv_buses_per_mv=1,
            hv_voltage_kv=110.0,
            mv_voltage_kv=10.0,
            lv_voltage_kv=0.4
        )
        
        # Check HV/MV transformer
        hv_mv_trafo = net.trafo[net.trafo['name'].str.contains('HV0_MV0')]
        assert len(hv_mv_trafo) == 1
        
        trafo = hv_mv_trafo.iloc[0]
        hv_bus_voltage = net.bus.loc[trafo['hv_bus'], 'vn_kv']
        lv_bus_voltage = net.bus.loc[trafo['lv_bus'], 'vn_kv']
        
        assert hv_bus_voltage == 110.0
        assert lv_bus_voltage == 10.0


class TestNetworkSummary:
    """Test network summary functionality."""
    
    def test_get_network_summary(self):
        """Test getting network summary."""
        builder = TopologyBuilder(network_name="Test Summary Network")
        net = builder.build_radial_network(num_buses=5, voltage_kv=0.4)
        
        summary = builder.get_network_summary()
        
        assert summary['name'] == "Test Summary Network"
        assert summary['buses'] == 5
        assert summary['lines'] == 4
        assert summary['external_grids'] == 1
        assert 0.4 in summary['voltage_levels']
    
    def test_summary_before_network_creation(self):
        """Test summary when no network exists."""
        builder = TopologyBuilder()
        summary = builder.get_network_summary()
        
        assert 'error' in summary


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_create_network_before_operations_raises_error(self):
        """Test that operations without network raise error."""
        builder = TopologyBuilder()
        
        config = BusConfig("Bus1", VoltageLevel.LV, 0.4)
        
        with pytest.raises(ValueError, match="Network not created"):
            builder.add_bus(config)
    
    def test_single_bus_radial_network(self):
        """Test radial network with single bus."""
        builder = TopologyBuilder()
        net = builder.build_radial_network(num_buses=1, voltage_kv=0.4)
        
        assert len(net.bus) == 1
        assert len(net.line) == 0  # No lines needed
        assert len(net.ext_grid) == 1
    
    def test_bus_with_geodata(self):
        """Test adding bus with geographic coordinates."""
        builder = TopologyBuilder()
        builder.create_network()
        
        config = BusConfig(
            bus_id="GeoBus",
            voltage_level=VoltageLevel.LV,
            vn_kv=0.4,
            geo_data={'latitude': 13.7563, 'longitude': 100.5018}
        )
        
        bus_idx = builder.add_bus(config)
        
        # Note: geodata is stored separately in pandapower
        assert bus_idx is not None
