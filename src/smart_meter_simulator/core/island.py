
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class IslandState:
    is_islanded: bool
    slack_bus_id: Optional[int] # ID of the bus acting as reference
    grid_forming_meter_id: Optional[str] # Meter ID of the battery forming the grid

class IslandManager:
    """
    Manages the connection status of the microgrid to the main grid.
    Handles Slack Bus swapping when islanding.
    """
    
    def __init__(self):
        self.state = IslandState(
            is_islanded=False,
            slack_bus_id=None, # Default to main grid connection point
            grid_forming_meter_id=None
        )
        self.main_grid_bus_id = 0 # Assumption: Bus 0 is the creation of the external grid
        
    def disconnect(self, net, meters: List[any], meter_to_bus: Dict[str, int]) -> bool:
        """
        Disconnect from main grid (Island Mode).
        1. Find suitable Grid Forming asset (Battery with highest capacity/SoC).
        2. Change slack bus in pandapower network.
        """
        if self.state.is_islanded:
            logger.warning("Already islanded.")
            return False
            
        logger.info("Initiating Islanding Sequence...")
        
        # 1. Find Grid Forming Candidate
        # Look for meters with 'BATTERY_STORAGE' type or just 'has_battery' with high capacity
        candidates = [m for m in meters if m.config.get('has_battery')]
        
        if not candidates:
            logger.error("Islanding Failed: No Grid Forming capability (No Batteries).")
            return False
            
        # Sort by battery level (highest first) - simplified selection logic
        # In reality, we'd check inverter capability (Grid Forming vs Grid Following)
        best_candidate = sorted(candidates, key=lambda m: m.battery_level, reverse=True)[0]
        
        bus_idx = meter_to_bus.get(best_candidate.meter_id)
        if bus_idx is None:
             logger.error(f"Islanding Failed: Forming candidate {best_candidate.meter_id} not mapped to bus.")
             return False

        # 2. Update Network Topology (Pandapower)
        try:
            import pandapower as pp
            # Disconnect external grid (usually at bus 0 or separate element)
            # We assume ext_grid is at index 0
            if len(net.ext_grid) > 0:
                net.ext_grid.in_service.at[0] = False
                
            # Set new slack bus
            # Find the load/gen at this bus and mark it? 
            # Actually, pandapower needs a 'slack' gen or ext_grid.
            # We can change the type of the bus to 'SLACK' and add a generator there if needed?
            # Creating a temporary slack generator at the battery bus 
            # (treating the battery as the slack generator)
            
            # Check if there's already a gen at this bus
            # existing_gen = net.gen[net.gen.bus == bus_idx]
            
            # For simulation stability, we add a virtual slack generator representing the VPP anchor
            pp.create_ext_grid(net, bus=bus_idx, vm_pu=1.0, name="VPP_Anchor_Slack")
            
            self.state.is_islanded = True
            self.state.slack_bus_id = bus_idx
            self.state.grid_forming_meter_id = best_candidate.meter_id
            
            logger.info(f"Islanding Successful. New Slate Bus: {bus_idx} (Meter: {best_candidate.meter_id})")
            return True
            
        except Exception as e:
            logger.error(f"Islanding topology update failed: {e}", exc_info=True)
            return False

    def reconnect(self, net) -> bool:
        """
        Reconnect to main grid.
        """
        if not self.state.is_islanded:
            return False
            
        logger.info("Initiating Reconnection Sequence...")
        try:
            # 1. Remove VPP Anchor Slack
            # We created a new ext_grid. We should remove it.
            # Assuming it's the last one added or find by name
            # For simplicity, let's just re-enable original ext_grid and disable/remove the temporary one.
            
            # Re-enable main grid
            if len(net.ext_grid) > 0:
                net.ext_grid.in_service.at[0] = True
                
            # Remove temporary slack (VPP_Anchor_Slack)
            # Find index by name
            temp_slacks = net.ext_grid[net.ext_grid.name == "VPP_Anchor_Slack"]
            if not temp_slacks.empty:
                net.ext_grid.drop(temp_slacks.index, inplace=True)
            
            self.state.is_islanded = False
            self.state.slack_bus_id = 0
            self.state.grid_forming_meter_id = None
            
            logger.info("Reconnection Successful.")
            return True
            
        except Exception as e:
            logger.error(f"Reconnection failed: {e}", exc_info=True)
            return False
