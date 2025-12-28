from smart_meter_simulator.simulation.std_types import create_thai_std_types
import pandapower as pp
import pandapower.control as control
import pandapower.timeseries as timeseries
from pandapower.timeseries.data_sources.frame_data import DFData
from smart_meter_simulator.simulation.profiles import create_thai_daily_profiles
import os

class ThaiGridModel:
    """
    A class to generate representative models of the Thai Power System 
    using pandapower.
    
    Architecture based on:
    1. EGAT (Transmission): 230/115 kV, acts as External Grid.
    2. MEA (Metropolitan): 69 kV -> 24 kV (Underground XLPE).
    3. PEA (Provincial): 115 kV -> 22 kV (Standard) / 33 kV (South).
    """

    def __init__(self):
        self.net = pp.create_empty_network()
        # Initialize Thai Standard Types
        create_thai_std_types(self.net)
        self.profiles = None
        self.build_hybrid_grid()

    def create_egat_boundary(self, voltage_kv=115.0):
        """
        Creates the EGAT interface point (External Grid).
        Modeled as an infinite bus with fixed voltage.
        """
        # Create the EGAT bus
        self.egat_bus = pp.create_bus(self.net, vn_kv=voltage_kv, name="EGAT Interface", zone="EGAT")
        
        # Create external grid connection (Slack Bus)
        # vm_pu=1.0, va_degree=0.0
        pp.create_ext_grid(self.net, bus=self.egat_bus, vm_pu=1.0, va_degree=0.0, name="EGAT Grid Connection")
        return self.egat_bus

    # ... (Rest of the topology methods remain unchanged, just skipped in this view) ...

    def setup_time_series(self):
        """
        Configures the network for time-series simulation using Thai load profiles.
        """
        # 1. Generate Profiles
        self.profiles = create_thai_daily_profiles()
        ds = DFData(self.profiles)
        
        # 2. Assign Profiles to Loads
        # MEA Loads -> Commercial (e.g., dense urban) or Residential depending on logic
        # PEA Loads -> Residential + Agri
        # VSPP -> Solar
        
        # We need to iterate through existing elements and attach controllers
        # For simplicity in this demo:
        # - Any load with "MEA" in name: 70% Commercial, 30% Residential
        # - Any load with "PEA" in name: 80% Residential
        # - Any sgen: Solar
        
        # Create controllers
        # Note: ConstControl updates 'p_mw' = p_mw_base * profile_val
        # So we ensure the base p_mw in build_network was the peak or rated capacity.
        
        for idx in self.net.load.index:
            load_name = self.net.load.at[idx, 'name']
            
            if "EV Station" in load_name:
                # Assign Stochastic EV Profile
                # The profile is p.u. (0.5-1.0), so it scales the 0.12 MW base load.
                control.ConstControl(self.net, element='load', variable='p_mw', element_index=[idx],
                                     data_source=ds, profile_name='ev_fast_charge')
            elif "MEA" in load_name:
                # Assign Commercial Profile
                control.ConstControl(self.net, element='load', variable='p_mw', element_index=[idx],
                                     data_source=ds, profile_name='commercial')
            elif "PEA" in load_name:
                # Assign Residential Profile
                control.ConstControl(self.net, element='load', variable='p_mw', element_index=[idx],
                                     data_source=ds, profile_name='residential')

        # VSPP / Solar
        for idx in self.net.sgen.index:
            sgen_name = self.net.sgen.at[idx, 'name']
            if "Solar" in sgen_name or "VSPP" in sgen_name:
                 control.ConstControl(self.net, element='sgen', variable='p_mw', element_index=[idx],
                                     data_source=ds, profile_name='solar')

        # Initialize output writer? 
        # Usually handled by the runner script, but we prepare the net.
        print("Time Series Controllers initialized.")

    def run_power_flow(self, robust=True):
        """
        Runs Newton-Raphson power flow.
        If robust=True, falls back to Newton-Raphson with Iwamoto multipliers (nri)
        if the standard method fails (common in stressed PEA radial networks).
        """
        try:
            pp.runpp(self.net, algorithm='nr')
            return True
        except pp.LoadflowNotConverged:
            if robust:
                print("Standard NR Failed. Attempting Robust Newton-Raphson-Iwamoto (nri)...")
                try:
                    pp.runpp(self.net, algorithm='nri')
                    print("Robust NRI Converged.")
                    return True
                except pp.LoadflowNotConverged:
                    print("CRITICAL: Robust NRI also failed to converge!")
                    return False
            else:
                print("Power flow did not converge!")
                return False

    def create_mea_subsystem(self, parent_bus, num_feeders=2):
        """
        Creates a representative MEA distribution network.
        - Steps down from interactions (e.g. 115 kV) to 69 kV then 24 kV.
        - Uses underground cables (high capacitance).
        """
        # 1. Sub-transmission Step-down
        mea_hv_bus = pp.create_bus(self.net, vn_kv=115.0, name="MEA Substation HV", zone="MEA")
        
        pp.create_line(self.net, from_bus=parent_bus, to_bus=mea_hv_bus, length_km=5.0, 
                       std_type="N2XS(FL)2Y 1x300 RM/35 64/110 kV", name="Trasmission Line to MEA")

        # 2. Main Transformer 115/24 kV (using generic here as we only defined MV/LV trafos in std_types so far)
        # Note: The prompt gave MEA MV/LV trafos (24/0.416). It didn't specify HV/MV.
        # Keeping generic HV/MV for now.
        mea_mv_bus = pp.create_bus(self.net, vn_kv=24.0, name="MEA Main Bus 24kV", zone="MEA")
        pp.create_transformer(self.net, hv_bus=mea_hv_bus, lv_bus=mea_mv_bus, std_type="63 MVA 110/20 kV", name="MEA Tx 115/24")

        # 3. Underground Feeders (24 kV)
        for i in range(num_feeders):
            # Create a feeder head
            feeder_bus = pp.create_bus(self.net, vn_kv=24.0, name=f"MEA Feeder {i+1} Head", zone="MEA")
            pp.create_switch(self.net, bus=mea_mv_bus, element=feeder_bus, et="b", type="CB", closed=True)
            
            previous_bus = feeder_bus
            # Create segments of underground cable
            for j in range(3):
                load_bus = pp.create_bus(self.net, vn_kv=24.0, name=f"MEA Feeder {i+1} Node {j+1}", zone="MEA")
                
                # Underground Cable: XLPE
                # Using generic XLPE for 24kV as explicit Table 1 was for PEA. 
                # Assuming MEA uses XLPE typicals. 'NA2XS2Y 1x240 RM/25 12/20 kV' is a good proxy in pandapower.
                pp.create_line(self.net, from_bus=previous_bus, to_bus=load_bus, length_km=2.0, 
                               std_type="NA2XS2Y 1x240 RM/25 12/20 kV", name=f"MEA Cable {i}-{j}")
                
                # Add distribution transformer (MV/LV) to simulate load connected at LV side?
                # Or just lump load. To verify std_types, let's add a consumer transformer.
                if j == 2: # At the end
                    lv_bus = pp.create_bus(self.net, vn_kv=0.416, name=f"MEA LV Load Bus {i}", zone="MEA")
                    pp.create_transformer(self.net, hv_bus=load_bus, lv_bus=lv_bus, std_type="MEA 1000 kVA", name=f"MEA Dist Trafo {i}")
                    pp.create_load(self.net, bus=lv_bus, p_mw=0.5, q_mvar=0.1, name=f"MEA LV Load {i}")
                else:
                    pp.create_load(self.net, bus=load_bus, p_mw=1.0, q_mvar=0.2, name=f"MEA MV Load {i}-{j}")
                
                previous_bus = load_bus

    def create_pea_subsystem(self, parent_bus, region="Central", num_feeders=2):
        """
        Creates a representative PEA distribution network using Thai Standard Types.
        """
        mv_voltage = 33.0 if region == "South" else 22.0
        
        pea_hv_bus = pp.create_bus(self.net, vn_kv=115.0, name=f"PEA Substation HV ({region})", zone="PEA")
        
        pp.create_line(self.net, from_bus=parent_bus, to_bus=pea_hv_bus, length_km=20.0, 
                       std_type="N2XS(FL)2Y 1x300 RM/35 64/110 kV", name="Transmission Line to PEA")

        # Transformer 115/MV
        pea_mv_bus = pp.create_bus(self.net, vn_kv=mv_voltage, name=f"PEA Main Bus {mv_voltage}kV", zone="PEA")
        # Selecting appropriate trafo based on voltage (Generic HV/MV)
        trafo_type = "63 MVA 110/30 kV" if mv_voltage == 33.0 else "63 MVA 110/20 kV"
        pp.create_transformer(self.net, hv_bus=pea_hv_bus, lv_bus=pea_mv_bus, std_type=trafo_type, name=f"PEA Tx 115/{mv_voltage}")

        # Long Radial Feeders using PEA Standard Conductors
        for i in range(num_feeders):
            feeder_head = pp.create_bus(self.net, vn_kv=mv_voltage, name=f"PEA Feeder {i+1} Head", zone="PEA")
            pp.create_switch(self.net, bus=pea_mv_bus, element=feeder_head, et="b", type="CB", closed=True)
            
            previous_bus = feeder_head
            for j in range(5):
                node_bus = pp.create_bus(self.net, vn_kv=mv_voltage, name=f"PEA {region} Feeder {i+1} Node {j+1}", zone="PEA")
                
                # Alternate between SAC and PIC for demonstration
                # '185 SAC' or '120 AAC' for long lines
                line_type = "185 SAC" if i == 0 else "120 AAC"
                
                pp.create_line(self.net, from_bus=previous_bus, to_bus=node_bus, length_km=5.0, 
                               std_type=line_type, name=f"PEA Line {i}-{j} ({line_type})")
                
                # Add PEA Distribution Transformer at specific points
                if j in [2, 4]:
                    lv_bus = pp.create_bus(self.net, vn_kv=0.4, name=f"PEA LV Node {i}-{j}", zone="PEA")
                    pp.create_transformer(self.net, hv_bus=node_bus, lv_bus=lv_bus, std_type="PEA 250 kVA", name=f"PEA Dist Trafo {i}-{j}")
                    pp.create_load(self.net, bus=lv_bus, p_mw=0.1, q_mvar=0.05, name=f"PEA LV Load {i}-{j}")
                else: 
                     # Direct MV Load (Industrial/VSPP)
                     pp.create_load(self.net, bus=node_bus, p_mw=0.2, q_mvar=0.05, name=f"PEA MV Load {i}-{j}")
                
                # VSPP logic
                if j == 4 and i == 1: 
                    pp.create_sgen(self.net, bus=node_bus, p_mw=1.5, q_mvar=0.0, name=f"VSPP {i} Solar")
                
                previous_bus = node_bus

    def build_hybrid_grid(self):
        """
        Builds a combined grid with EGAT supplying both MEA and PEA subsystems.
        """
        # 1. EGAT (Slack)
        egat_node = self.create_egat_boundary()
        
        # 2. MEA System (Bangkok)
        self.create_mea_subsystem(egat_node)
        
        # 3. PEA System (Provinces)
        self.create_pea_subsystem(egat_node, region="Central")

        return self.net

    def run_power_flow(self, robust=True):
        """
        Runs Newton-Raphson power flow.
        If robust=True, falls back to Newton-Raphson with Iwamoto multipliers (nri)
        if the standard method fails (common in stressed PEA radial networks).
        """
        try:
            print("Attempting Standard Newton-Raphson (nr)...")
            pp.runpp(self.net, algorithm='nr')
            print("Standard NR Converged.")
            return True
        except pp.LoadflowNotConverged:
            if robust:
                print("Standard NR Failed. Attempting Robust Newton-Raphson-Iwamoto (nri)...")
                try:
                    pp.runpp(self.net, algorithm='nri')
                    print("Robust NRI Converged.")
                    return True
                except pp.LoadflowNotConverged:
                    print("CRITICAL: Robust NRI also failed to converge!")
                    return False
            else:
                print("Power flow did not converge!")
                return False
