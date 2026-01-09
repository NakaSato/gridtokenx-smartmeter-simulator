
import logging
import random
from typing import List, Dict, Optional
import pandapower as pp

from ..core.engine import SimulationEngine
from ..core.meter import SmartMeter
from ..transport.base import TransportLayer
from ..core.database import DatabaseManager
from .thai_grid import ThaiGridModel
from .utcc_campus import UTCCSmartCampus
from .dynamic_grid import DynamicCommunityGrid
from ..services.gis_service import GISService
from ..services.zoning_service import MicrogridZoningService
from ..services.transaction_service import P2PTransactionService
from ..services.ledger_service import LedgerService
from .market_agent import GridState, MarketAgent
from .market_agent import GridState, MarketAgent
from ..services.token_service import TokenService

logger = logging.getLogger(__name__)

class PhysicsSimulationEngine(SimulationEngine):
    """
    Enhanced Simulation Engine that uses Pandapower physics models (Thai Grid)
    to drive the smart meter readings, instead of pure random generation.
    Now defaults to DynamicCommunityGrid for user-defined meter topologies.
    """
    
    def __init__(
        self,
        meters: List[SmartMeter],
        transport: TransportLayer,
        db_manager: DatabaseManager = None,
        model_type: str = "DYNAMIC", # Default to Dynamic
        num_zones: int = 5,
        quantum_matching: Optional['QuantumMatching'] = None
    ):
        super().__init__(meters, transport, db_manager)
        
        self.gis = GISService()
        self.model_type = model_type
        self.province = "Bangkok"
        
        self.zoning = MicrogridZoningService(num_zones=num_zones)
        self.transaction_service = P2PTransactionService(
            self.zoning,
            grid_validator=self.validate_grid_state
        )
        self.zoning_service = self.zoning
        
        # Time offset for testing (e.g., -6 hours to simulate daytime from evening)
        self.time_offset_hours = -6
        # FORCE CLOCK TO MIDDAY
        from datetime import datetime, time, timezone
        self.current_sim_time = datetime.combine(datetime.now(timezone.utc).date(), time(1, 0), tzinfo=timezone.utc)
        
        # Initialize Ledger
        if db_manager:
            self.ledger = LedgerService(db_manager)
        else:
            # Fallback if no db_manager passed (shouldn't happen in app.py usually)
            self.ledger = LedgerService(DatabaseManager())

        # Initialize Quantum Optimizer (Injected)
        self.quantum_matching = quantum_matching
        if not self.quantum_matching:
             logger.warning("QuantumOptimizer not injected. P2P matching will be disabled.")
        
        self.last_quantum_matches = []
        self.last_optimization_meta = {} 
        
        # Initial mapping/zoning
        self._assign_meter_zones()
        self._last_zone_count = len(self.meters)
        
        # Token Service
        self.token_service = TokenService()

        logger.info(f"Initializing Physics Model: {model_type}")
        if model_type == "UTCC":
            self.grid_model = UTCCSmartCampus()
            self.province = "Bangkok"
        elif model_type == "THAI_GRID":
            self.grid_model = ThaiGridModel()
            self.province = "Bangkok"
        else:
            # Dynamic Grid (Default)
            # Create grid from CURRENT meters (which now have zones)
            self.grid_model = DynamicCommunityGrid(self.meters)
            self.province = "Bangkok" 
            
        self.net = self.grid_model.net
        
        # Map meters to grid for static models (after self.net is assigned)
        if model_type in ("UTCC", "THAI_GRID"):
            self._map_meters_to_grid()
    
    def _is_on_peak_hour(self) -> bool:
        if not hasattr(self, 'current_sim_time') or self.current_sim_time is None:
            return False
        hour = self.current_sim_time.hour
        return 9 <= hour < 22
        
    def _map_meters_to_grid(self):
        """Legacy mapping for static grids (ThaiGrid/UTCC)."""
        self.meter_map: Dict[str, Dict[str, int]] = {}
        load_indices = self.net.load.index.tolist()
        sgen_indices = self.net.sgen.index.tolist()
        
        for meter in self.meters:
            is_producer = meter.config.get("has_solar", False)
            mapping = {}
            if is_producer and sgen_indices:
                idx = random.choice(sgen_indices)
                mapping["sgen_idx"] = idx
                mapping["bus_idx"] = self.net.sgen.at[idx, "bus"]
                mapping["name"] = self.net.sgen.at[idx, "name"]
            elif load_indices:
                idx = random.choice(load_indices)
                mapping["load_idx"] = idx
                mapping["bus_idx"] = self.net.load.at[idx, "bus"]
                mapping["name"] = self.net.load.at[idx, "name"]
            else:
                mapping["bus_idx"] = random.choice(self.net.bus.index.tolist())
                
            self.meter_map[meter.meter_id] = mapping
            
            if not meter.latitude or not meter.longitude:
                # No longer assigning random/centroid fallback coordinates
                pass
    
    def _map_single_meter(self, meter: SmartMeter):
        """Maps a new meter to the grid."""
        # For Dynamic Grid, we need to add it to the physics model physically
        if isinstance(self.grid_model, DynamicCommunityGrid):
            self.grid_model._add_meter_node(meter)
            logger.info(f"Dynamically added meter {meter.meter_id} to Dynamic Grid")
        else:
            # Legacy random mapping
            load_indices = self.net.load.index.tolist()
            sgen_indices = self.net.sgen.index.tolist()
            mapping = {}
            # ... (omitted simplified logic for brevity, assume similar to _map_meters_to_grid)
            # Just reusing the logic from init if needed, but for now focusing on Dynamic.

        if not meter.latitude or not meter.longitude:
            # No longer assigning random/centroid fallback coordinates
            pass
    
    def _assign_meter_zones(self):
        coordinates = []
        needs_zoning = False
        for meter in self.meters:
            if meter.grid_zone_id is None:
                needs_zoning = True
            
            if meter.latitude and meter.longitude:
                coordinates.append((meter.latitude, meter.longitude))
            else:
                # Use (None, None) or skip depending on zoning service requirements
                # Here we skip to avoid re-clustering with invalid points
                pass
        
        # Only re-cluster if at least one meter is missing a zone
        if needs_zoning:
            if coordinates and len(coordinates) >= self.zoning.num_zones:
                logger.info("Running KMeans re-clustering for zones...")
                zone_ids = self.zoning.fit(coordinates)
                idx_coord = 0
                for meter in self.meters:
                    if meter.latitude and meter.longitude:
                        meter.grid_zone_id = zone_ids[idx_coord]
                        idx_coord += 1
                    elif meter.grid_zone_id is None:
                         # Fallback for meters without coordinates
                         import random
                         meter.grid_zone_id = random.randint(1, self.zoning.num_zones)
            else:
                 # Fallback if not enough coordinates for clustering
                 logger.info("Not enough coordinates for clustering. Assigning random zones.")
                 import random
                 for meter in self.meters:
                     if meter.grid_zone_id is None:
                         meter.grid_zone_id = random.randint(1, self.zoning.num_zones)
        else:
            logger.info("All meters have pre-assigned zones. Skipping re-clustering.")

    def validate_grid_state(self) -> bool:
        """
        Public method to check if the current grid state is valid (Voltage/Overload).
        Used by P2P logic to approve/reject trades based on grid health.
        """
        if isinstance(self.grid_model, DynamicCommunityGrid):
            # Run power flow on current state
            success = self.grid_model.run_power_flow()
            if not success:
                return False
            violations = self.grid_model.check_grid_violations()
            if any(violations.values()):
                logger.warning(f"Grid Validation Failed: {violations}")
                return False
            return True
        return True

    async def tick(self):
        # 0. Handle Dynamic Meters
        # For Dynamic Grid, self.grid_model.meter_bus_map tracks added meters
        if isinstance(self.grid_model, DynamicCommunityGrid):
            for meter in self.meters:
                if meter.meter_id not in self.grid_model.meter_bus_map:
                    self._map_single_meter(meter)
        
        # Re-zoning check
        if len(self.meters) != getattr(self, "_last_zone_count", 0):
             self._assign_meter_zones()
             self._last_zone_count = len(self.meters)
             
        # 0.3 Initialize Market Agents for everyone
        from .market_agent import MarketAgent, TradingStrategy, GridState
        for meter in self.meters:
            if not hasattr(meter, '_market_agent'):
                # Default strategy
                strategy_str = meter.config.get("trading_preference", "Moderate")
                from .market_agent import TradingStrategy
                strategy = TradingStrategy(strategy_str) if strategy_str in ["Conservative", "Moderate", "Aggressive"] else TradingStrategy.MODERATE
                
                # Force THB base prices from MarketSystem
                meter._market_agent = MarketAgent(
                    meter.meter_id, 
                    strategy=strategy,
                    base_sell_price=self.market_system.base_sell_price,
                    base_buy_price=self.market_system.base_buy_price
                )
                logger.debug(f"Initialized MarketAgent for {meter.meter_id} with strategy {strategy.value} and base prices {self.market_system.base_sell_price}/{self.market_system.base_buy_price}")

        # 0.5 Update Weather (so Physics uses current weather)
        # We duplicate this from super().tick() because we need it BEFORE physics calcs
        current_weather = self.weather_system.update()
        global_irradiance, global_temp_offset = self.weather_system.get_factors()
        zone_weather = await self._fetch_zone_weather()
        
        for meter in self.meters:
            if meter.grid_zone_id is not None and meter.grid_zone_id in zone_weather:
                condition, irradiance, temp_offset = zone_weather[meter.grid_zone_id]
                meter.update_weather(condition, irradiance, temp_offset)
            else:
                meter.update_weather(current_weather, global_irradiance, global_temp_offset)

        # 1. Update Physics Model
        updates = {}
        timestamp = self.current_sim_time
        for meter in self.meters:
            cons_kw = meter._calculate_consumption(timestamp)
            gen_kw = 0.0
            if meter.config.get("has_solar"):
                gen_kw = meter._calculate_solar_generation(timestamp)
            
            updates[meter.meter_id] = {
                'p_load_mw': cons_kw / 1000.0,
                'p_gen_mw': gen_kw / 1000.0
            }
            
            # Store energy values directly in static_data for reading generation
            if meter.static_data is None:
                meter.static_data = {}
            meter.static_data["energy_consumed"] = cons_kw
            meter.static_data["energy_generated"] = gen_kw
            
            # --- Token Minting (Generation) ---
            # Mint NRG tokens for generation (Simulating "Proof of Origin" / REC)
            # We mint every tick based on generation in interval (e.g. 15min)
            gen_kwh = gen_kw * (16.0 / 60.0) # Approx 15 min interval
            if gen_kwh > 0:
                self.token_service.mint_nrg(meter, gen_kwh)

        if isinstance(self.grid_model, DynamicCommunityGrid):
            # Apply updates
            self.grid_model.update_grid_state(updates)
            
            # Run Power Flow
            grid_success = self.grid_model.run_power_flow()
            
            # Update Voltages
            if grid_success:
                for meter in self.meters:
                    vm_pu = self.grid_model.get_node_voltage(meter.meter_id)
                    voltage = vm_pu * 230.0
                    
                    if meter.static_data is None: meter.static_data = {}
                    meter.static_data["voltage"] = voltage
                    meter.static_data["voltage_pu"] = vm_pu
                    
                    # Physics-based frequency: derives from grid load balance
                    state = updates.get(meter.meter_id, {})
                    p_load = state.get('p_load_mw', 0)
                    p_gen = state.get('p_gen_mw', 0)
                    freq_deviation = -0.001 * (p_load - p_gen) * 1000 
                    freq_deviation = max(-0.05, min(0.05, freq_deviation))
                    meter.static_data["frequency"] = 50.0 + freq_deviation
                    
                    # Physics-based power factor
                    has_solar = meter.config.get("has_solar", False)
                    base_pf = 0.98 if has_solar else 0.92 
                    load_factor = min(1.0, p_load * 1000 / max(1, meter.config.get("base_consumption", 1.0)))
                    pf = base_pf - 0.02 * load_factor 
                    meter.static_data["power_factor"] = max(0.85, min(1.0, pf))
                    meter.static_data["temperature"] = 25.0 + meter.temp_offset
                    
                    # C.2: THD
                    from .power_quality import estimate_thd_for_bus
                    thd_v, thd_i = estimate_thd_for_bus(
                        has_ev_charger=False,
                        has_solar_inverter=meter.config.get("has_solar", False),
                        ev_power_kw=0,
                        solar_power_kw=p_gen*1000
                    )
                    meter.static_data["thd_voltage"] = thd_v
                    meter.static_data["thd_current"] = thd_i
                    
                    # C.3: Market Pricing
                    grid_state = GridState(
                        voltage_pu=vm_pu,
                        frequency_hz=meter.static_data["frequency"],
                        thd_voltage=thd_v,
                        is_on_peak=self._is_on_peak_hour()
                    )
                    surplus = meter.last_reading.surplus_energy if meter.last_reading else 0.0
                    deficit = meter.last_reading.deficit_energy if meter.last_reading else 0.0
                    sell, buy = meter._market_agent.calculate_prices(grid_state, surplus, deficit)
                    meter.static_data["max_sell_price"] = sell
                    meter.static_data["max_buy_price"] = buy
        else:
            # Fallback for legacy models (THAI_GRID / UTCC)
            # Still update pricing so they can participate in Quantum Market
            for meter in self.meters:
                if meter.static_data is None: meter.static_data = {}
                # Legacy models might not have node-specific physics yet, use nominal
                grid_state = GridState(
                    voltage_pu=1.0,
                    frequency_hz=50.0,
                    thd_voltage=0.01,
                    is_on_peak=self._is_on_peak_hour()
                )
                surplus = meter.last_reading.surplus_energy if meter.last_reading else 0.0
                deficit = meter.last_reading.deficit_energy if meter.last_reading else 0.0
                sell, buy = meter._market_agent.calculate_prices(grid_state, surplus, deficit)
                meter.static_data["max_sell_price"] = sell
                meter.static_data["max_buy_price"] = buy
                
                # Fill basic physics for legacy readings
                meter.static_data["voltage"] = 230.0
                meter.static_data["frequency"] = 50.0
                meter.static_data["power_factor"] = 0.95
                meter.static_data["temperature"] = 25.0 + meter.temp_offset

        # 1.5 Generate Readings (populates last_reading with current physics state)
        # This will send data to Gateway and set self.last_reading
        await super().tick()

        # 2. Run Quantum Market Clearing
        # Now self.last_reading is FRESH for the current tick
        if self.quantum_matching and len(self.meters) > 2:
            await self._run_quantum_market()

    async def _run_quantum_market(self):
        """
        Collects market participants and runs the Quantum Optimizer.
        """
        logger.info(f"--- Quantum Market Loop @ {self.current_sim_time.isoformat()} ---")
        bids = []
        asks = []
        
        for meter in self.meters:
            if not hasattr(meter, '_market_agent') or not meter.last_reading:
                continue
            
            # Skip meters without a valid zone assignment
            if meter.grid_zone_id is None:
                continue
                
            # Surplus > 0 => Seller
            if meter.last_reading.surplus_energy > 0.01: # Minimum threshold lowered
                max_sell = meter.static_data.get("max_sell_price") if meter.static_data else None
                # Fallback if static_data not populated yet
                if max_sell is None:
                     max_sell, _ = meter._market_agent.calculate_prices(
                         GridState(voltage_pu=1.0), # Approximate
                         meter.last_reading.surplus_energy, 
                         0
                     )
                     
                asks.append({
                    'id': meter.meter_id,
                    'price': max_sell,
                    'amount': meter.last_reading.surplus_energy,
                    'zone': meter.grid_zone_id
                })
            
            # Deficit > 0 => Buyer
            if meter.last_reading.deficit_energy > 0.01:
                max_buy = meter.static_data.get("max_buy_price") if meter.static_data else None
                if max_buy is None:
                     _, max_buy = meter._market_agent.calculate_prices(
                         GridState(voltage_pu=1.0),
                         0,
                         meter.last_reading.deficit_energy
                     )

                bids.append({
                    'id': meter.meter_id,
                    'price': max_buy,
                    'amount': meter.last_reading.deficit_energy,
                    'zone': meter.grid_zone_id
                })
        
        logger.info(f"Market Participants: {len(bids)} bids, {len(asks)} asks")

        if bids and asks:
            # logger.info(f"Running Quantum Optimization for {len(bids)} bids and {len(asks)} asks")
            
            # Define Cost Callback
            def cost_callback(buyer_zone, seller_zone, amount):
                return self.transaction_service.calculate_transaction_cost(
                    buyer_zone, seller_zone, amount
                )
            
            # --- Gather Zone Voltages for Stability / Physics-aware Optimization ---
            # Aggregate average voltage_pu per zone
            zone_voltages_map = {}
            zone_counts = {}
            
            for meter in self.meters:
                if meter.grid_zone_id is not None and meter.static_data and "voltage_pu" in meter.static_data:
                    z = meter.grid_zone_id
                    v = meter.static_data["voltage_pu"]
                    zone_voltages_map[z] = zone_voltages_map.get(z, 0.0) + v
                    zone_counts[z] = zone_counts.get(z, 0) + 1
            
            # Average
            final_zone_voltages = {}
            for z, total_v in zone_voltages_map.items():
                if zone_counts[z] > 0:
                    final_zone_voltages[z] = total_v / zone_counts[z]
            
            matches, meta = self.quantum_matching.optimize_matches(
                bids, 
                asks, 
                cost_callback,
                zone_voltages=final_zone_voltages
            )
            
            # Inject voltage profile for visualization
            meta['zone_voltages'] = final_zone_voltages
            
            self.last_quantum_matches = matches
            self.last_optimization_meta = meta
            
            # Record transactions and settle tokens
            if matches:
                 logger.info(f"Quantum Market Cleared: {len(matches)} matches. Duration: {meta.get('duration',0):.3f}s")
                 for match in matches:
                     # Identify participants
                     buyer = next((m for m in self.meters if m.meter_id == match.buyer_id), None)
                     seller = next((m for m in self.meters if m.meter_id == match.seller_id), None)
                     
                     buyer_zone = 0
                     seller_zone = 0
                     
                     if buyer: buyer_zone = buyer.grid_zone_id
                     if seller: seller_zone = seller.grid_zone_id
                     
                     # --- TOKEN SETTLEMENT ---
                     tx_hash = None
                     if buyer and seller:
                         tx_hash = self.token_service.process_settlement(match, buyer, seller)
                         # Store hash in match object so LedgerService can record it
                         match.tx_hash = tx_hash
                     
                     self.ledger.record_match(match, zones=(buyer_zone, seller_zone))
