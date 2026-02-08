import random
from typing import Dict, Any, List, Optional
from ..models.reading import EnergyReading
import logging

logger = logging.getLogger(__name__)

class FDI_Attacker:
    """
    Simulates a False Data Injection (FDI) attacker.
    Intercepts and modifies meter readings before processing by state estimation.
    """
    
    def __init__(self):
        self.active = False
        self.target_meters: List[str] = []
        self.bias_kw: float = 0.0
        self.scale_factor: float = 1.0
        self.mode: str = "bias" # "bias", "scale", "random"
        self.stealthy: bool = False # If true, tries to keep residuals low
        
    def configure(self, active: bool, targets: List[str], mode: str = "bias", 
                  bias: float = 0.0, scale: float = 1.0, stealthy: bool = False):
        """Configure the attack parameters."""
        self.active = active
        self.target_meters = targets
        self.mode = mode
        self.bias_kw = bias
        self.scale_factor = scale
        self.stealthy = stealthy
        
        status = "Active" if active else "Inactive"
        logger.info(f"FDI Attacker {status} on {len(targets)} targets. Mode: {mode}, Bias: {bias}kW")

    def intercept(self, readings: List[EnergyReading]) -> List[EnergyReading]:
        """
        Intercept and modify readings if the attacker is active.
        """
        if not self.active:
            return readings
            
        modified_readings = []
        for reading in readings:
            if reading.meter_id in self.target_meters or not self.target_meters:
                # Apply attack
                modified = self._modify_reading(reading)
                modified_readings.append(modified)
            else:
                modified_readings.append(reading)
                
        return modified_readings

    def _modify_reading(self, reading: EnergyReading) -> EnergyReading:
        """Modify a single reading based on attacker mode."""
        # Deep copy or just modify fields (Reading is Pydantic, so model_copy is safe)
        attack_reading = reading.model_copy()
        
        # Calculate current bias (kW)
        current_bias = self.bias_kw
        
        # Stealthy Mode: Apply bias incrementally or limit it to 3*sigma if sigma is known
        # In this layer, we don't have direct access to sigma from the meter's accuracy class easily,
        # but we can assume typical accuracy (1.0% - 2.0%) or just use a small fraction of the nominal value.
        if self.stealthy:
            # Simple stealth: limit current_bias to 5% of nominal consumption to stay 'under the radar'
            nominal = abs(reading.energy_consumed) * 4.0 # kW approx
            stealth_limit = nominal * 0.05 
            current_bias = min(current_bias, stealth_limit)
            
        if self.mode == "bias":
            attack_reading.energy_consumed += current_bias / 4.0 # kWh for 15m
            # Ensure non-negative
            attack_reading.energy_consumed = max(0.0, attack_reading.energy_consumed)
            
        elif self.mode == "scale":
            # In scale mode, stealthy means keeping the scale factor close to 1.0
            actual_scale = self.scale_factor
            if self.stealthy:
                actual_scale = 1.0 + (self.scale_factor - 1.0) * 0.2 # Dampen scale
            attack_reading.energy_consumed *= actual_scale
            
        elif self.mode == "random":
            # Add random noise spikes
            noise = random.uniform(-self.bias_kw, self.bias_kw) / 4.0
            if self.stealthy:
                noise *= 0.3 # Dampen noise
            attack_reading.energy_consumed = max(0.0, attack_reading.energy_consumed + noise)
            
        # Re-calculate surplus/deficit to mimic physical consistency
        net = attack_reading.energy_generated - attack_reading.energy_consumed
        attack_reading.surplus_energy = max(0.0, net)
        attack_reading.deficit_energy = max(0.0, -net)
        
        # Log stealthy activity if active
        if self.active and self.stealthy and random.random() < 0.01:
            logger.debug(f"Stealthy FDI applied to {reading.meter_id}: bias={current_bias:.3f}kW")
            
        return attack_reading

    def get_status(self) -> Dict[str, Any]:
        """Return attacker status for API/UI."""
        return {
            "active": self.active,
            "targets": self.target_meters,
            "mode": self.mode,
            "bias_kw": self.bias_kw,
            "scale_factor": self.scale_factor,
            "stealthy": self.stealthy
        }
