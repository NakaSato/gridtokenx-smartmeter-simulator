import pandapower as pp
import numpy as np
import pandas as pd
from app.simulation.std_types import create_thai_std_types
from pandapower.timeseries.data_sources.frame_data import DFData
import pandapower.control as control

class UTCCSmartCampus:
    """
    Models the UTCC (University of the Thai Chamber of Commerce) Smart Campus Microgrid.
    
    Key Characteristics:
    - Urban Grid: Embedded in robust MEA 24 kV network.
    - Prosumer: 5 MW Rooftop Solar.
    - Load: Commercial/Academic (AC driven), aligned with solar generation.
    - BEMS: High resolution (1-min) data monitoring and optimization.
    """

    def __init__(self):
        self.net = pp.create_empty_network()
        create_thai_std_types(self.net)
        self.profiles = None
        self.build_network()

    def build_network(self):
        # 1. MEA Strong Grid Connection (24 kV)
        # Low impedance, high short circuit power
        self.mea_bus = pp.create_bus(self.net, vn_kv=24.0, name="MEA Interface 24kV", zone="MEA")
        pp.create_ext_grid(self.net, bus=self.mea_bus, vm_pu=1.0, name="MEA Grid")

        # 2. Campus Main Ring/Bus
        self.campus_bus = pp.create_bus(self.net, vn_kv=24.0, name="UTCC Main Bus", zone="Campus")
        
        # Connection to MEA (Short, strong underground cable)
        pp.create_line(self.net, from_bus=self.mea_bus, to_bus=self.campus_bus, length_km=0.5, 
                       std_type="NA2XS2Y 1x240 RM/25 12/20 kV", name="MEA-UTCC Feeder")

        # 3. Faculty Buildings (Loads)
        # Modeled as LV loads behind transformers
        # Faculty of Engineering
        self.eng_bus = pp.create_bus(self.net, vn_kv=0.416, name="Eng Faculty LV", zone="Campus")
        pp.create_transformer(self.net, hv_bus=self.campus_bus, lv_bus=self.eng_bus, 
                              std_type="MEA 2000 kVA", name="Eng Faculty Tx")
        self.eng_load = pp.create_load(self.net, bus=self.eng_bus, p_mw=1.5, q_mvar=0.5, name="Eng Load")
        
        # Admin Building
        self.admin_bus = pp.create_bus(self.net, vn_kv=0.416, name="Admin Building LV", zone="Campus")
        pp.create_transformer(self.net, hv_bus=self.campus_bus, lv_bus=self.admin_bus, 
                              std_type="MEA 2000 kVA", name="Admin Building Tx")
        self.admin_load = pp.create_load(self.net, bus=self.admin_bus, p_mw=2.0, q_mvar=0.6, name="Admin Load")

        # 4. Rooftop Solar (5 MW Distributed)
        # Aggregated at MV bus or distributed at LV? 
        # Requirement says "5 MW installed". Let's put 2.5 MW at each building bus to simulate rooftop.
        pp.create_sgen(self.net, bus=self.eng_bus, p_mw=2.5, q_mvar=0.0, name="Eng Solar")
        pp.create_sgen(self.net, bus=self.admin_bus, p_mw=2.5, q_mvar=0.0, name="Admin Solar")

    def generate_high_res_profiles(self, num_minutes=60*24):
        """
        Generates 1-minute resolution profiles for a single day.
        """
        # Time steps
        times = np.linspace(0, 24, num_minutes, endpoint=False)
        idx = range(num_minutes)
        df = pd.DataFrame(index=idx)
        
        # 1. Commercial/Academic Load Profile
        # High during 8am - 6pm (AC driven), drops significantly at night.
        # Spiky behavior to simulate "Transient load spikes" mentioned in prompt?
        # Smooth base curve
        base_load = 0.2 + 0.7 * np.exp(-0.5 * ((times - 14.0) / 4.0)**4) # Plateau centered at 2pm
        
        # Add Noise/Spikes (1-min resolution feature)
        np.random.seed(42)
        noise = np.random.normal(0, 0.05, num_minutes) # 5% fluctation
        spikes = np.where(np.random.rand(num_minutes) > 0.98, 0.2, 0) # Occasional 20% jumps (Large AC starting)
        
        df['campus_load'] = np.clip(base_load + noise + spikes, 0.1, 1.0)
        
        # 2. Solar Profile
        # Bell curve 6am-6pm
        solar_vals = 1.0 * np.exp(-0.5 * ((times - 12.0) / 2.5)**2) - 0.01
        
        # Add Cloud passing effects (High frequency drops)
        # Cloud mask: clusters of drops
        cloud_mask = np.ones(num_minutes)
        # Simple cloud simulation: random blocks
        for i in range(10): # 10 cloud events
            start = np.random.randint(6*60, 16*60)
            duration = np.random.randint(5, 20) # 5-20 mins
            cloud_mask[start:start+duration] = np.random.uniform(0.2, 0.6) # Drop to 20-60% output
            
        df['solar_high_res'] = np.maximum(0, solar_vals * cloud_mask)
        
        self.profiles = df
        return df

    def setup_time_series(self):
        if self.profiles is None:
            self.generate_high_res_profiles()
            
        ds = DFData(self.profiles)
        
        # Apply to Loads
        for idx in self.net.load.index:
            control.ConstControl(self.net, element='load', variable='p_mw', element_index=[idx],
                                 data_source=ds, profile_name='campus_load')
                                 
        # Apply to Solar
        for idx in self.net.sgen.index:
            control.ConstControl(self.net, element='sgen', variable='p_mw', element_index=[idx],
                                 data_source=ds, profile_name='solar_high_res')

    def run_power_flow(self, robust=True):
        """Runs Newton-Raphson power flow."""
        try:
            pp.runpp(self.net, algorithm='nr')
            return True
        except pp.LoadflowNotConverged:
            if robust:
                try:
                    pp.runpp(self.net, algorithm='nri')
                    return True
                except pp.LoadflowNotConverged:
                    return False
            return False
