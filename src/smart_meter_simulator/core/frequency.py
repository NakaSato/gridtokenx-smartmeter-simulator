
import logging
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FrequencyState:
    frequency: float  # Hz
    rocof: float      # Hz/s
    angle_deg: float  # Degrees (relative to 50Hz reference)
    time_step: float  # Seconds since last update

class FrequencyModel:
    """
    Simulates grid frequency dynamics based on Swing Equation.
    df/dt = (P_mech - P_elec) / (2 * H * S_base) * f_0
    """
    
    def __init__(self, nominal_freq: float = 50.0, inertia_h: float = 5.0, s_base_mva: float = 10.0):
        self.f0 = nominal_freq
        self.H = inertia_h          # Inertia constant (seconds)
        self.S_base = s_base_mva    # System Base Power (MVA)
        
        self.state = FrequencyState(
            frequency=nominal_freq,
            rocof=0.0,
            angle_deg=0.0,
            time_step=0.0
        )
        
        # Damping factor (Load frequency dependence)
        self.D = 1.0  # % load change per % frequency change
        
    def step(self, power_imbalance_mw: float, dt_seconds: float) -> FrequencyState:
        """
        Calculate new frequency state based on power imbalance.
        Positive imbalance (Gen > Load) -> Frequency increases.
        """
        if dt_seconds <= 0:
            return self.state
            
        current_freq = self.state.frequency
        
        # simplified swing equation
        # P_acc = P_mech - P_elec - D * (f - f0)
        # We assume power_imbalance_mw = P_mech - P_elec
        
        # Damping power (Load relief due to frequency deviation)
        p_damping = (self.D / 100.0) * (current_freq - self.f0) * self.S_base
        
        p_acc = power_imbalance_mw - p_damping
        
        # Calculate RoCoF (df/dt)
        # 2 * H * df/dt = P_acc (pu) * f0
        # P_acc (pu) = P_acc (MW) / S_base (MVA)
        
        p_acc_pu = p_acc / self.S_base
        
        df_dt = (p_acc_pu * self.f0) / (2 * self.H)
        
        # Update Frequency
        new_freq = current_freq + (df_dt * dt_seconds)
        
        # Update Phase Angle (integral of frequency deviation)
        # d_delta/dt = 360 * (f - f0)
        d_angle = 360.0 * (new_freq - self.f0) * dt_seconds
        new_angle = (self.state.angle_deg + d_angle) % 360.0
        
        self.state = FrequencyState(
            frequency=new_freq,
            rocof=df_dt,
            angle_deg=new_angle,
            time_step=dt_seconds
        )
        
        return self.state
        
    def reset(self):
        self.state.frequency = self.f0
        self.state.rocof = 0.0
        self.state.angle_deg = 0.0
