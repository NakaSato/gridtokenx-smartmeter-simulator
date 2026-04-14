"""
Multi-port EV Charging Station Model

Manages multiple EV charging ports sharing a single grid connection point.
Implements dynamic load balancing across ports with CC-CV charging curves.
"""

import random
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class EVPort:
    """Individual charging port within a station"""
    port_id: str
    occupied: bool = False
    vehicle_soc: float = 0.0  # State of charge (0-100%)
    vehicle_capacity_kwh: float = 60.0  # Vehicle battery capacity
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    charge_rate_kw: float = 150.0  # Max charge rate for this port
    energy_delivered_kwh: float = 0.0  # Total energy delivered this session


class ChargingStation:
    """
    Multi-port EV charging station with load balancing.
    
    Multiple ports share a common grid connection point.
    Total power is dynamically distributed across active ports.
    Implements CC-CV (Constant Current - Constant Voltage) charging curve.
    """
    
    def __init__(
        self,
        station_id: str,
        meter_id: str,
        num_ports: int = 4,
        max_station_capacity_kw: float = 600.0,
        base_charge_rate_kw: float = 150.0,
    ):
        self.station_id = station_id
        self.meter_id = meter_id
        self.num_ports = num_ports
        self.max_station_capacity_kw = max_station_capacity_kw
        self.base_charge_rate_kw = base_charge_rate_kw
        
        # Initialize ports
        self.ports: List[EVPort] = [
            EVPort(
                port_id=f"{station_id}_PORT_{i+1}",
                charge_rate_kw=base_charge_rate_kw,
            )
            for i in range(num_ports)
        ]
        
        # Metrics
        self.total_energy_delivered_kwh = 0.0
        self.total_sessions = 0
        self.current_power_kw = 0.0
    
    def get_available_port(self) -> Optional[EVPort]:
        """Find an available (unoccupied) port"""
        for port in self.ports:
            if not port.occupied:
                return port
        return None
    
    def occupy_port(
        self,
        port: EVPort,
        initial_soc: float = 20.0,
        capacity_kwh: float = 60.0,
        departure_time: Optional[datetime] = None,
    ) -> bool:
        """
        Occupy a port with a vehicle.
        
        Args:
            port: Port to occupy
            initial_soc: Initial vehicle SoC (%)
            capacity_kwh: Vehicle battery capacity
            departure_time: Expected departure time
            
        Returns:
            True if port was successfully occupied
        """
        if port.occupied:
            return False
        
        port.occupied = True
        port.vehicle_soc = initial_soc
        port.vehicle_capacity_kwh = capacity_kwh
        port.arrival_time = datetime.now()
        port.departure_time = departure_time
        port.energy_delivered_kwh = 0.0
        self.total_sessions += 1
        
        return True
    
    def release_port(self, port: EVPort) -> Dict:
        """
        Release an occupied port and return session summary.
        
        Returns:
            Dict with session energy, duration, final SoC
        """
        if not port.occupied:
            return {}
        
        session_data = {
            'port_id': port.port_id,
            'energy_delivered_kwh': port.energy_delivered_kwh,
            'final_soc': port.vehicle_soc,
            'duration_hours': self._calculate_session_duration(port),
        }
        
        # Reset port
        port.occupied = False
        port.vehicle_soc = 0.0
        port.arrival_time = None
        port.departure_time = None
        port.energy_delivered_kwh = 0.0
        
        return session_data
    
    def calculate_power_distribution(self) -> Dict[str, float]:
        """
        Calculate power distribution across active ports with load balancing.
        
        If total demand > station capacity, distribute proportionally.
        Implements CC-CV charging curve tapering at high SoC.
        
        Returns:
            Dict mapping port_id -> allocated power (kW)
        """
        active_ports = [p for p in self.ports if p.occupied]
        
        if not active_ports:
            self.current_power_kw = 0.0
            return {}
        
        # Calculate base demand per port (before load balancing)
        port_demands = {}
        total_demand = 0.0
        
        for port in active_ports:
            # Apply CC-CV charging curve
            soc_fraction = port.vehicle_soc / 100.0
            
            if soc_fraction > 0.8:
                # CV phase: taper charging
                taper_factor = 1.0 - ((soc_fraction - 0.8) / 0.2) * 0.6
                demand = port.charge_rate_kw * taper_factor
            elif soc_fraction < 0.2:
                # Low SoC: reduced rate (battery warming)
                warmup_factor = 0.7 + (soc_fraction / 0.2) * 0.3
                demand = port.charge_rate_kw * warmup_factor
            else:
                # CC phase: full rate
                demand = port.charge_rate_kw
            
            port_demands[port.port_id] = demand
            total_demand += demand
        
        # Load balancing: cap at station capacity
        if total_demand > self.max_station_capacity_kw:
            # Proportional reduction
            reduction_factor = self.max_station_capacity_kw / total_demand
            for port_id in port_demands:
                port_demands[port_id] *= reduction_factor
        
        self.current_power_kw = sum(port_demands.values())
        return port_demands
    
    def simulate_charging(self, interval_hours: float = 0.25) -> Dict[str, float]:
        """
        Simulate charging for all active ports over an interval.
        
        Args:
            interval_hours: Simulation interval (default 15 min = 0.25h)
            
        Returns:
            Dict mapping port_id -> energy delivered (kWh)
        """
        power_distribution = self.calculate_power_distribution()
        energy_delivered = {}
        
        for port in self.ports:
            if not port.occupied:
                continue
            
            power_kw = power_distribution.get(port.port_id, 0.0)
            energy_kwh = power_kw * interval_hours
            
            # Update SoC
            soc_increase = (energy_kwh / port.vehicle_capacity_kwh) * 100.0
            port.vehicle_soc = min(100.0, port.vehicle_soc + soc_increase)
            
            # Check if fully charged
            if port.vehicle_soc >= 100.0:
                logger.info(f"Port {port.port_id} fully charged, auto-releasing")
                session = self.release_port(port)
                energy_kwh = session.get('energy_delivered_kwh', energy_kwh)
            
            port.energy_delivered_kwh += energy_kwh
            self.total_energy_delivered_kwh += energy_kwh
            energy_delivered[port.port_id] = energy_kwh
        
        return energy_delivered
    
    def get_utilization(self) -> float:
        """Get current port utilization (0.0-1.0)"""
        active = sum(1 for p in self.ports if p.occupied)
        return active / self.num_ports if self.num_ports > 0 else 0.0
    
    def get_status(self) -> Dict:
        """Get comprehensive station status"""
        return {
            'station_id': self.station_id,
            'meter_id': self.meter_id,
            'num_ports': self.num_ports,
            'active_ports': sum(1 for p in self.ports if p.occupied),
            'utilization': self.get_utilization(),
            'current_power_kw': self.current_power_kw,
            'max_capacity_kw': self.max_station_capacity_kw,
            'total_energy_delivered_kwh': self.total_energy_delivered_kwh,
            'total_sessions': self.total_sessions,
            'ports': [
                {
                    'port_id': p.port_id,
                    'occupied': p.occupied,
                    'soc': p.vehicle_soc if p.occupied else None,
                    'energy_delivered': p.energy_delivered_kwh if p.occupied else None,
                }
                for p in self.ports
            ]
        }
    
    @staticmethod
    def _calculate_session_duration(port: EVPort) -> float:
        """Calculate session duration in hours"""
        if port.arrival_time is None:
            return 0.0
        
        from datetime import datetime
        duration = datetime.now() - port.arrival_time
        return duration.total_seconds() / 3600.0
    
    def random_vehicle_arrival(self, departure_time: Optional[datetime] = None) -> bool:
        """
        Simulate a random vehicle arriving at an available port.
        
        Returns:
            True if a port was occupied
        """
        port = self.get_available_port()
        if port is None:
            return False
        
        # Random vehicle characteristics
        initial_soc = random.uniform(10.0, 50.0)  # Typically arrive with 10-50%
        capacity = random.uniform(40.0, 100.0)  # Vehicle battery size
        
        return self.occupy_port(
            port=port,
            initial_soc=initial_soc,
            capacity_kwh=capacity,
            departure_time=departure_time,
        )
    
    def check_departures(self, current_time: datetime) -> List[Dict]:
        """
        Check for vehicles that have departed.
        
        Returns:
            List of session summaries for departed vehicles
        """
        departed_sessions = []
        
        for port in self.ports:
            if port.occupied and port.departure_time and current_time >= port.departure_time:
                session = self.release_port(port)
                departed_sessions.append(session)
        
        return departed_sessions
