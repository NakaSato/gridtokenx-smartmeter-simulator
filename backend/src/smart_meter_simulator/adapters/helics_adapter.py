"""
HELICS Co-Simulation Adapter for GridTokenX Smart Meter Simulator.
Bridges the simulator with PNNL's Transactive Energy Simulation Platform (TESP).
Allows the simulator to act as a HELICS federate, coordinating time and data exchange.
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import helics. If not available, we define placeholders to avoid crash.
try:
    import helics as h
    HELICS_AVAILABLE = True
except ImportError:
    h = None
    HELICS_AVAILABLE = False
    logger.warning("HELICS package is not installed. HelicsAdapter will run in mockup/no-op mode.")


class HelicsAdapter:
    """
    Adapter to bridge GridTokenX Smart Meter Simulator with a HELICS co-simulation environment (TESP).
    Manages publications of meter readings/grid state and subscriptions to market/external controllers.
    """

    def __init__(
        self,
        fed_name: str = "SmartMeterSimulator",
        core_type: str = "zmq",
        broker_address: str = "localhost",
        broker_port: int = 23404,
        time_period: float = 900.0,
        data_flow: str = "individual",  # "individual" or "aggregate"
    ):
        self.fed_name = fed_name
        self.core_type = core_type
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.time_period = time_period
        self.data_flow = data_flow

        self.fed = None
        self.fed_info = None
        self.is_connected = False
        self.current_time_seconds = 0.0

        # Mappings: key -> HELICS Publication / Subscription object
        self.publications: Dict[str, Any] = {}
        self.subscriptions: Dict[str, Any] = {}
        self.subscribed_keys: Dict[str, str] = {}  # local_key -> helics_global_key

        # Cached latest values from subscriptions
        self.subscription_cache: Dict[str, Any] = {}

    def is_available(self) -> bool:
        """Returns True if helics module is successfully imported."""
        return HELICS_AVAILABLE

    def initialize(self, meters: List[Any], subscription_mappings: Optional[Dict[str, str]] = None) -> bool:
        """
        Create the HELICS federate and register publications and subscriptions.
        
        Args:
            meters: List of smart meters in the simulation.
            subscription_mappings: Optional dictionary mapping internal keys to global HELICS keys.
                                  E.g., {"global_price": "MarketFederate/retail_price"}
        """
        if not HELICS_AVAILABLE:
            logger.error("Cannot initialize HELICS adapter: helics package is not installed.")
            return False

        try:
            logger.info(f"Initializing HELICS Federate '{self.fed_name}' (Core Type: {self.core_type})...")
            
            # 1. Create Federate Info
            self.fed_info = h.helicsCreateFederateInfo()
            h.helicsFederateInfoSetCoreTypeFromString(self.fed_info, self.core_type)
            
            # Configure broker
            broker_str = f"{self.broker_address}:{self.broker_port}" if self.broker_port else self.broker_address
            h.helicsFederateInfoSetCoreInitString(self.fed_info, f"--broker={broker_str} --federates=1")
            
            # Configure timing properties
            h.helicsFederateInfoSetTimeProperty(self.fed_info, h.HELICS_PROPERTY_TIME_PERIOD, self.time_period)
            h.helicsFederateInfoSetTimeProperty(self.fed_info, h.HELICS_PROPERTY_TIME_DELTA, self.time_period)
            h.helicsFederateInfoSetFlagOption(self.fed_info, h.HELICS_FLAG_UNINTERRUPTIBLE, True)

            # 2. Create Value Federate
            self.fed = h.helicsCreateValueFederate(self.fed_name, self.fed_info)
            logger.info("HELICS Value Federate created successfully.")

            # 3. Register Publications
            # Register aggregated topics
            self.publications["total_p_mw"] = h.helicsFederateRegisterGlobalPublication(
                self.fed, f"{self.fed_name}/total_p_mw", h.HELICS_DATA_TYPE_DOUBLE, "MW"
            )
            self.publications["total_gen_mw"] = h.helicsFederateRegisterGlobalPublication(
                self.fed, f"{self.fed_name}/total_gen_mw", h.HELICS_DATA_TYPE_DOUBLE, "MW"
            )
            self.publications["net_p_mw"] = h.helicsFederateRegisterGlobalPublication(
                self.fed, f"{self.fed_name}/net_p_mw", h.HELICS_DATA_TYPE_DOUBLE, "MW"
            )
            self.publications["grid_frequency"] = h.helicsFederateRegisterGlobalPublication(
                self.fed, f"{self.fed_name}/grid_frequency", h.HELICS_DATA_TYPE_DOUBLE, "Hz"
            )

            # Register individual meter publications if in "individual" mode
            if self.data_flow == "individual":
                for meter in meters:
                    m_id = meter.meter_id
                    self.publications[f"{m_id}/p_kw"] = h.helicsFederateRegisterGlobalPublication(
                        self.fed, f"{self.fed_name}/meter_{m_id}/p_kw", h.HELICS_DATA_TYPE_DOUBLE, "kW"
                    )
                    self.publications[f"{m_id}/q_kvar"] = h.helicsFederateRegisterGlobalPublication(
                        self.fed, f"{self.fed_name}/meter_{m_id}/q_kvar", h.HELICS_DATA_TYPE_DOUBLE, "kVAR"
                    )
                    self.publications[f"{m_id}/energy_kwh"] = h.helicsFederateRegisterGlobalPublication(
                        self.fed, f"{self.fed_name}/meter_{m_id}/energy_kwh", h.HELICS_DATA_TYPE_DOUBLE, "kWh"
                    )

            # 4. Register Subscriptions
            # Default fallback global subscriptions
            sub_mappings = subscription_mappings or {}
            
            # We always subscribe to a retail electricity price
            price_key = sub_mappings.get("retail_price", "MarketFederate/retail_price")
            self.subscribed_keys["retail_price"] = price_key
            self.subscriptions["retail_price"] = h.helicsFederateRegisterSubscription(
                self.fed, price_key, "$/kWh"
            )
            logger.info(f"Subscribed to electricity price via HELICS: {price_key}")

            # Register individual meter subscriptions if mapping is available
            if self.data_flow == "individual":
                for meter in meters:
                    m_id = meter.meter_id
                    # Dynamic subscription to local dispatch commands
                    dispatch_key = sub_mappings.get(
                        f"{m_id}/dispatch_price",
                        f"MarketFederate/meter_{m_id}/dispatch_price"
                    )
                    self.subscribed_keys[f"{m_id}/dispatch_price"] = dispatch_key
                    self.subscriptions[f"{m_id}/dispatch_price"] = h.helicsFederateRegisterSubscription(
                        self.fed, dispatch_key, "Baht/kWh"
                    )

                    # Dynamic subscription to load shed switch command
                    shed_key = sub_mappings.get(
                        f"{m_id}/is_shed",
                        f"ControlFederate/meter_{m_id}/is_shed"
                    )
                    self.subscribed_keys[f"{m_id}/is_shed"] = shed_key
                    self.subscriptions[f"{m_id}/is_shed"] = h.helicsFederateRegisterSubscription(
                        self.fed, shed_key, ""
                    )

            logger.info(f"Registered {len(self.publications)} publications and {len(self.subscriptions)} subscriptions.")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize HELICS: {e}", exc_info=True)
            return False

    async def enter_execution_mode(self) -> bool:
        """Enter the execution mode of the HELICS co-simulation (blocks until granted)."""
        if not HELICS_AVAILABLE or not self.fed:
            logger.warning("HELICS not active or mock. Skipping execution entry.")
            self.is_connected = True
            return True

        try:
            logger.info("Entering HELICS execution mode (waiting for broker grant)...")
            loop = asyncio.get_event_loop()
            # Run blocking call in executor
            await loop.run_in_executor(None, h.helicsFederateEnterExecutingMode, self.fed)
            self.is_connected = True
            logger.info("Granted entry into HELICS execution mode.")
            return True
        except Exception as e:
            logger.error(f"Error entering HELICS execution mode: {e}", exc_info=True)
            return False

    async def request_time(self, target_time_seconds: float) -> float:
        """
        Request simulation time step from HELICS.
        
        Args:
            target_time_seconds: The time we want to advance to (relative to simulation start).
            
        Returns:
            The actual time granted by the HELICS broker.
        """
        if not HELICS_AVAILABLE or not self.fed or not self.is_connected:
            self.current_time_seconds = target_time_seconds
            return target_time_seconds

        try:
            loop = asyncio.get_event_loop()
            granted_time = await loop.run_in_executor(
                None, h.helicsFederateRequestTime, self.fed, target_time_seconds
            )
            self.current_time_seconds = float(granted_time)
            logger.debug(f"HELICS requested time {target_time_seconds}s, granted: {granted_time}s")
            return self.current_time_seconds
        except Exception as e:
            logger.error(f"Error requesting time from HELICS: {e}")
            return target_time_seconds

    def update_subscriptions(self):
        """Read latest values from all HELICS subscriptions and cache them."""
        if not HELICS_AVAILABLE or not self.fed or not self.is_connected:
            return

        for name, sub in self.subscriptions.items():
            if h.helicsInputIsUpdated(sub):
                try:
                    if "is_shed" in name:
                        val_str = None
                        try:
                            val_str = h.helicsInputGetString(sub).strip().upper()
                        except AttributeError:
                            pass
                        
                        if val_str is not None:
                            if val_str in ("OPEN", "SHED", "1", "TRUE", "1.0"):
                                self.subscription_cache[name] = True
                            elif val_str in ("CLOSED", "RESTORE", "0", "FALSE", "0.0"):
                                self.subscription_cache[name] = False
                            else:
                                try:
                                    val_num = h.helicsInputGetDouble(sub)
                                    self.subscription_cache[name] = bool(val_num > 0.5)
                                except Exception:
                                    pass
                        else:
                            try:
                                val_num = h.helicsInputGetDouble(sub)
                                self.subscription_cache[name] = bool(val_num > 0.5)
                            except Exception:
                                pass
                    else:
                        # Retrieve value as double
                        val = h.helicsInputGetDouble(sub)
                        self.subscription_cache[name] = val
                    logger.debug(f"Subscription updated [{name}]: {self.subscription_cache.get(name)}")
                except Exception as e:
                    logger.warning(f"Failed to read subscription value for '{name}': {e}")

    def get_subscription_value(self, key: str, default: Any = 0.0) -> Any:
        """Get the cached value of a subscription."""
        return self.subscription_cache.get(key, default)

    def publish_meter_data(self, readings: List[Any]):
        """Publish the current readings of all meters to the co-simulation."""
        if not HELICS_AVAILABLE or not self.fed or not self.is_connected:
            return

        total_p_kw = 0.0
        total_gen_kw = 0.0

        for r in readings:
            m_id = r.meter_id
            
            # Active/reactive power, conversion if necessary
            # active_power_kw is instantaneous power; cumulative energy in kWh
            p_kw = getattr(r, 'active_power_kw', 0.0)
            q_kvar = p_kw * 0.1  # Mock reactive power if not present
            energy_kwh = getattr(r, 'energy_consumed', 0.0)
            gen_kw = getattr(r, 'energy_generated', 0.0) * (3600.0 / self.time_period) # convert energy in interval to kW

            total_p_kw += p_kw
            total_gen_kw += gen_kw

            # Publish individual meter metrics if configured
            if self.data_flow == "individual":
                try:
                    if f"{m_id}/p_kw" in self.publications:
                        h.helicsPublicationPublishDouble(self.publications[f"{m_id}/p_kw"], float(p_kw))
                    if f"{m_id}/q_kvar" in self.publications:
                        h.helicsPublicationPublishDouble(self.publications[f"{m_id}/q_kvar"], float(q_kvar))
                    if f"{m_id}/energy_kwh" in self.publications:
                        h.helicsPublicationPublishDouble(self.publications[f"{m_id}/energy_kwh"], float(energy_kwh))
                except Exception as e:
                    logger.warning(f"Failed to publish individual meter {m_id} data to HELICS: {e}")

        # Publish aggregated metrics
        try:
            total_p_mw = total_p_kw / 1000.0
            total_gen_mw = total_gen_kw / 1000.0
            net_p_mw = total_p_mw - total_gen_mw

            h.helicsPublicationPublishDouble(self.publications["total_p_mw"], total_p_mw)
            h.helicsPublicationPublishDouble(self.publications["total_gen_mw"], total_gen_mw)
            h.helicsPublicationPublishDouble(self.publications["net_p_mw"], net_p_mw)
            
            logger.info(f"Published aggregated values to HELICS: Load={total_p_mw:.3f}MW, Gen={total_gen_mw:.3f}MW, Net={net_p_mw:.3f}MW")
        except Exception as e:
            logger.error(f"Failed to publish aggregated metrics to HELICS: {e}")

    def publish_frequency(self, frequency_hz: float):
        """Publish grid frequency to co-simulation."""
        if not HELICS_AVAILABLE or not self.fed or not self.is_connected:
            return
        try:
            h.helicsPublicationPublishDouble(self.publications["grid_frequency"], float(frequency_hz))
        except Exception as e:
            logger.warning(f"Failed to publish frequency to HELICS: {e}")

    async def finalize(self):
        """Finalize and close the HELICS federate."""
        if not HELICS_AVAILABLE or not self.fed:
            return

        try:
            logger.info("Finalizing HELICS Federate...")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, h.helicsFederateFinalize, self.fed)
            h.helicsFederateFree(self.fed)
            h.helicsCloseLibrary()
            self.is_connected = False
            logger.info("HELICS Federate finalized and closed successfully.")
        except Exception as e:
            logger.error(f"Error finalizing HELICS federate: {e}")
