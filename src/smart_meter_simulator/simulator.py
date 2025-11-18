#!/usr/bin/env python3
"""
Smart Meter Simulator - Main Module
Orchestrates meter simulation with real-time data streaming
"""

import os
import json
import time
import random
import logging
import schedule
import math
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import asdict


# Import modular components
from smart_meter_simulator.config import (
    MeterType,
    WeatherCondition,
    GridConnectionStatus,
)
from smart_meter_simulator.utils import (
    EnergyReading,
)
from smart_meter_simulator.websocket_server import WebSocketServer

# Optional imports with graceful fallback
try:
    from kafka import KafkaProducer
except ImportError:
    KafkaProducer = None

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None

try:
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS
except ImportError:
    InfluxDBClient = None
    SYNCHRONOUS = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmartMeterSimulator:
    def __init__(self):
        # Service Configuration
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://p2p_user:p2p_password@localhost:5432/p2p_energy_trading')
        
        # InfluxDB Configuration
        self.influxdb_url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        self.influxdb_token = os.getenv('INFLUXDB_TOKEN', '')
        self.influxdb_org = os.getenv('INFLUXDB_ORG', 'gridtoken')
        self.influxdb_bucket = os.getenv('INFLUXDB_BUCKET', 'energy_readings')
        
        # Simulation Configuration
        self.simulation_interval = int(os.getenv('SIMULATION_INTERVAL', '30'))
        self.num_meters = int(os.getenv('NUM_METERS', '20'))
        self.output_file = os.getenv('OUTPUT_FILE', './data/meter_readings.jsonl')
        
        # Control State
        self.is_running = False
        self.is_paused = False
        self.simulation_task = None
        self.last_error = None
        
        # Solar Configuration
        self.solar_panel_efficiency_min = float(os.getenv('SOLAR_PANEL_EFFICIENCY_MIN', '0.85'))
        self.solar_panel_efficiency_max = float(os.getenv('SOLAR_PANEL_EFFICIENCY_MAX', '0.95'))
        self.base_generation_min = float(os.getenv('BASE_GENERATION_MIN', '3.0'))
        self.base_generation_max = float(os.getenv('BASE_GENERATION_MAX', '12.0'))
        
        # Trading Configuration
        self.min_sell_price = float(os.getenv('MIN_SELL_PRICE', '0.15'))  # USD per kWh
        self.max_sell_price = float(os.getenv('MAX_SELL_PRICE', '0.35'))
        self.min_buy_price = float(os.getenv('MIN_BUY_PRICE', '0.20'))
        self.max_buy_price = float(os.getenv('MAX_BUY_PRICE', '0.40'))
        self.grid_feed_in_rate = float(os.getenv('GRID_FEED_IN_RATE', '0.12'))
        self.grid_purchase_rate = float(os.getenv('GRID_PURCHASE_RATE', '0.28'))
        
        # Weather Weights
        self.weather_weights = {
            WeatherCondition.SUNNY: float(os.getenv('WEATHER_SUNNY_WEIGHT', '0.4')),
            WeatherCondition.PARTLY_CLOUDY: float(os.getenv('WEATHER_PARTLY_CLOUDY_WEIGHT', '0.3')),
            WeatherCondition.CLOUDY: float(os.getenv('WEATHER_CLOUDY_WEIGHT', '0.15')),
            WeatherCondition.OVERCAST: float(os.getenv('WEATHER_OVERCAST_WEIGHT', '0.1')),
            WeatherCondition.RAINY: float(os.getenv('WEATHER_RAINY_WEIGHT', '0.05'))
        }
        
        # Initialize services
        self.producer = None
        self.db_conn = None
        self.influxdb_client = None
        self.influxdb_write_api = None
        self.standalone_mode = False
        
        # WebSocket Configuration
        self.ws_host = os.getenv('WS_HOST', 'localhost')
        self.ws_port = int(os.getenv('WS_PORT', '8765'))
        self.ws_enabled = os.getenv('WS_ENABLED', 'true').lower() == 'true'
        self.ws_server = None
        
        self.initialize_services()
        
        # Initialize enhanced meter configurations
        self.meters = self.initialize_enhanced_meters()
        
        # Statistics
        self.stats = {
            'total_readings': 0,
            'kafka_sends': 0,
            'db_stores': 0,
            'file_saves': 0,
            'trading_opportunities': 0,
            'rec_generated': 0,
            'ws_broadcasts': 0
        }
        
        # Weather simulation state
        self.current_weather = WeatherCondition.SUNNY
        self.weather_duration = 0
        self.weather_change_interval = random.randint(3, 8)  # Change weather every 3-8 cycles

    def initialize_services(self):
        """Initialize external services with enhanced error handling"""
        services_available = 0
        
        # Initialize Kafka
        if KafkaProducer:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.kafka_servers.split(','),
                    value_serializer=lambda v: json.dumps(
                        v,
                        default=str
                    ).encode('utf-8'),
                    key_serializer=lambda k: (
                        k.encode('utf-8') if k else None
                    ),
                    request_timeout_ms=10000,
                    retries=3,
                    max_request_size=1048576,
                    compression_type='gzip'
                )
                logger.info("Kafka producer initialized successfully")
                services_available += 1
            except Exception as e:
                logger.warning(f"Kafka not available: {e}")
                self.producer = None
        else:
            logger.warning("Kafka not available: KafkaProducer not installed")
            self.producer = None
        
        # Initialize Database connections
        if psycopg2:
            try:
                self.db_conn = psycopg2.connect(self.db_url)
                logger.info("Main database connection established")
                services_available += 1
            except Exception as e:
                logger.warning(f"Main database not available: {e}")
                self.db_conn = None
        else:
            logger.warning("Main database not available: psycopg2 not installed")
            self.db_conn = None
        
        # Initialize InfluxDB
        if InfluxDBClient and SYNCHRONOUS:
            try:
                self.influxdb_client = InfluxDBClient(
                    url=self.influxdb_url,
                    token=self.influxdb_token,
                    org=self.influxdb_org
                )
                try:
                    # Try new API (v1.18+)
                    self.influxdb_write_api = (
                        self.influxdb_client.write_api(write_type=SYNCHRONOUS)
                    )
                except TypeError:
                    # Fallback to older API
                    self.influxdb_write_api = (
                        self.influxdb_client.write_api(SYNCHRONOUS)
                    )
                logger.info("InfluxDB connection established")
                services_available += 1
            except Exception as e:
                logger.warning(f"InfluxDB not available: {e}")
                self.influxdb_client = None
                self.influxdb_write_api = None
        else:
            logger.warning(
                "InfluxDB not available: influxdb_client not installed"
            )
            self.influxdb_client = None
            self.influxdb_write_api = None
        
        # Set mode
        self.standalone_mode = services_available == 0
        
        if self.standalone_mode:
            logger.info("Running in STANDALONE mode")
        else:
            logger.info(f"Running in INTEGRATED mode - {services_available}/3 services available")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file) if os.path.dirname(self.output_file) else './data', exist_ok=True)

    def initialize_enhanced_meters(self) -> List[Dict[str, Any]]:
        """Initialize enhanced meter configurations with trading capabilities"""
        meters = []
        
        # Try to get meters from database first
        if self.db_conn:
            try:
                with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT sm.meter_id, sm.meter_type, sm.location, 
                               u.user_type, u.trading_preferences
                        FROM smart_meters sm
                        JOIN users u ON sm.user_id = u.id
                        WHERE sm.status = 'Active'
                        LIMIT %s
                    """, (self.num_meters,))
                    
                    db_meters = cursor.fetchall()
                    for meter in db_meters:
                        meter_config = self.create_meter_config(
                            meter['meter_id'],
                            meter['meter_type'],
                            meter['location'],
                            meter['user_type'],
                            meter.get('trading_preferences', {})
                        )
                        meters.append(meter_config)
            except Exception as e:
                logger.warning(f"Failed to load meters from database: {e}")
        
        # Fallback to simulated meters
        if not meters:
            meter_types = [
                MeterType.SOLAR_PROSUMER,
                MeterType.GRID_CONSUMER,
                MeterType.HYBRID_PROSUMER,
                MeterType.BATTERY_STORAGE
            ]
            
            for i in range(self.num_meters):
                meter_type = random.choice(meter_types)
                user_type = self.get_user_type_from_meter_type(meter_type)
                
                meter_config = self.create_meter_config(
                    f'AMI_METER_{i+1:03d}',
                    meter_type.value,
                    f'Zone_{random.randint(1, 5)}_Building_{i+1}',
                    user_type
                )
                meters.append(meter_config)
        
        logger.info(f"Initialized {len(meters)} enhanced meters")
        return meters

    def get_user_type_from_meter_type(self, meter_type: MeterType) -> str:
        """Map meter type to user type"""
        mapping = {
            MeterType.SOLAR_PROSUMER: 'Prosumer',
            MeterType.GRID_CONSUMER: 'Consumer',
            MeterType.HYBRID_PROSUMER: 'Prosumer',
            MeterType.BATTERY_STORAGE: 'Storage_Provider'
        }
        return mapping.get(meter_type, 'Consumer')

    def create_meter_config(self, meter_id: str, meter_type: str, location: str, 
                          user_type: str, trading_prefs: Optional[Dict] = None) -> Dict[str, Any]:
        """Create enhanced meter configuration"""
        config = {
            'meter_id': meter_id,
            'meter_type': meter_type,
            'location': location,
            'user_type': user_type,
            
            # Blockchain verification fields
            'static_key': f"KEY_{meter_id}_{random.randint(100000, 999999)}",
            'blockchain_registered': False,
            
            # Generation capabilities
            'has_solar': meter_type in ['Solar_Prosumer', 'Hybrid_Prosumer'],
            'has_battery': meter_type in ['Hybrid_Prosumer', 'Battery_Storage'],
            'solar_capacity': random.uniform(5.0, 15.0) if 'Prosumer' in meter_type else 0.0,
            'battery_capacity': random.uniform(10.0, 30.0) if 'Battery' in meter_type or 'Hybrid' in meter_type else 0.0,
            
            # Efficiency parameters
            'panel_efficiency': random.uniform(self.solar_panel_efficiency_min, self.solar_panel_efficiency_max),
            'inverter_efficiency': random.uniform(0.94, 0.98),
            'battery_efficiency': random.uniform(0.90, 0.95),
            
            # Consumption patterns
            'base_consumption': random.uniform(1.5, 8.0),
            'consumption_variability': random.uniform(0.1, 0.3),
            
            # Trading preferences
            'trading_enabled': trading_prefs.get('enabled', True) if trading_prefs else True,
            'preferred_sell_price': random.uniform(self.min_sell_price, self.max_sell_price),
            'preferred_buy_price': random.uniform(self.min_buy_price, self.max_buy_price),
            'trading_strategy': random.choice(['Conservative', 'Moderate', 'Aggressive']),
            
            # Battery state (if applicable)
            'current_battery_level': random.uniform(20, 80) if 'Battery' in meter_type or 'Hybrid' in meter_type else 0,
            
            # Noise and variability
            'noise_factor': random.uniform(0.05, 0.15),
            'weather_sensitivity': random.uniform(0.7, 1.0)
        }
        
        return config

    def update_weather_simulation(self):
        """Update weather conditions with realistic patterns"""
        self.weather_duration += 1
        
        if self.weather_duration >= self.weather_change_interval:
            # Choose new weather condition based on current weather and probabilities
            weather_transitions = {
                WeatherCondition.SUNNY: [WeatherCondition.SUNNY, WeatherCondition.PARTLY_CLOUDY],
                WeatherCondition.PARTLY_CLOUDY: [WeatherCondition.SUNNY, WeatherCondition.CLOUDY, WeatherCondition.PARTLY_CLOUDY],
                WeatherCondition.CLOUDY: [WeatherCondition.PARTLY_CLOUDY, WeatherCondition.OVERCAST, WeatherCondition.CLOUDY],
                WeatherCondition.OVERCAST: [WeatherCondition.CLOUDY, WeatherCondition.RAINY, WeatherCondition.OVERCAST],
                WeatherCondition.RAINY: [WeatherCondition.OVERCAST, WeatherCondition.CLOUDY]
            }
            
            possible_conditions = weather_transitions.get(self.current_weather, list(WeatherCondition))
            weights = [self.weather_weights[condition] for condition in possible_conditions]
            
            self.current_weather = random.choices(possible_conditions, weights=weights)[0]
            self.weather_duration = 0
            self.weather_change_interval = random.randint(2, 10)
            
            logger.info(f"Weather changed to: {self.current_weather.value}")

    def calculate_solar_generation_factor(self) -> Tuple[float, float, float]:
        """Calculate solar generation factors with enhanced weather modeling"""
        current_time = datetime.now()
        hour = current_time.hour
        
        # Base solar curve (time of day factor)
        if 6 <= hour <= 18:
            # Solar curve with more realistic progression
            time_factor = math.sin(math.pi * (hour - 6) / 12) ** 2
        else:
            time_factor = 0.0
        
        # Weather impact on solar generation
        weather_factors = {
            WeatherCondition.SUNNY: 1.0,
            WeatherCondition.PARTLY_CLOUDY: random.uniform(0.7, 0.9),
            WeatherCondition.CLOUDY: random.uniform(0.4, 0.7),
            WeatherCondition.OVERCAST: random.uniform(0.2, 0.4),
            WeatherCondition.RAINY: random.uniform(0.1, 0.3)
        }
        
        weather_factor = weather_factors.get(self.current_weather, 0.8)
        
        # Calculate irradiance (W/m²)
        max_irradiance = 1200  # Clear sky peak irradiance
        irradiance = time_factor * weather_factor * max_irradiance + random.gauss(0, 50)
        irradiance = max(0, irradiance)
        
        # Panel temperature affects efficiency (higher temp = lower efficiency)
        ambient_temp = random.gauss(25, 5)  # Base temperature
        panel_temp = ambient_temp + (irradiance / 1000) * 25  # Panel heating from solar
        
        return time_factor * weather_factor, irradiance, panel_temp

    def calculate_consumption_pattern(self, hour: int, meter_config: Dict[str, Any]) -> float:
        """Calculate realistic consumption patterns based on user type and time"""
        base_consumption = meter_config['base_consumption']
        variability = meter_config['consumption_variability']
        user_type = meter_config['user_type']
        
        # Time-of-day patterns by user type
        if user_type == 'Consumer':
            # Residential pattern: morning and evening peaks
            if 6 <= hour <= 9 or 17 <= hour <= 22:  # Peak hours
                time_factor = random.uniform(1.4, 2.0)
            elif 22 <= hour or hour <= 6:  # Night
                time_factor = random.uniform(0.3, 0.7)
            else:  # Day
                time_factor = random.uniform(0.7, 1.1)
        
        elif user_type == 'Prosumer':
            # Smart prosumer: lower consumption during high solar generation
            if 10 <= hour <= 15:  # Solar peak hours - shifted consumption
                time_factor = random.uniform(0.6, 0.9)
            elif 7 <= hour <= 9 or 18 <= hour <= 21:  # Morning/evening
                time_factor = random.uniform(1.2, 1.6)
            else:
                time_factor = random.uniform(0.8, 1.2)
        
        else:  # Storage_Provider or other
            # More consistent industrial-like pattern
            if 8 <= hour <= 17:  # Business hours
                time_factor = random.uniform(1.1, 1.4)
            else:
                time_factor = random.uniform(0.7, 1.0)
        
        # Add randomness and variability
        consumption = base_consumption * time_factor * random.gauss(1.0, variability)
        return max(0, consumption)

    def generate_enhanced_reading(self, meter_config: Dict[str, Any]) -> EnergyReading:
        """Generate enhanced meter reading with trading data"""
        current_time = datetime.now(timezone.utc)
        timestamp = current_time.isoformat()
        hour = current_time.hour
        
        # Update weather
        self.update_weather_simulation()
        
        # Calculate solar generation
        solar_factor, irradiance, panel_temp = self.calculate_solar_generation_factor()
        
        energy_generated = 0.0
        if meter_config['has_solar']:
            solar_capacity = meter_config['solar_capacity']
            panel_efficiency = meter_config['panel_efficiency'] * meter_config['weather_sensitivity']
            inverter_efficiency = meter_config['inverter_efficiency']
            
            # Temperature derating (panels lose efficiency when hot)
            temp_coefficient = -0.004  # -0.4% per degree above 25°C
            temp_derating = 1 + temp_coefficient * (panel_temp - 25)
            temp_derating = max(0.7, min(1.0, temp_derating))  # Limit between 70% and 100%
            
            base_generation = solar_capacity * solar_factor * panel_efficiency * inverter_efficiency * temp_derating
            noise = random.gauss(0, base_generation * meter_config['noise_factor'])
            energy_generated = max(0, base_generation + noise)
        
        # Calculate consumption
        energy_consumed = self.calculate_consumption_pattern(hour, meter_config)
        
        # Battery simulation
        battery_level = meter_config.get('current_battery_level', 0)
        if meter_config['has_battery']:
            battery_capacity = meter_config['battery_capacity']
            battery_efficiency = meter_config['battery_efficiency']
            
            # Simple battery management: charge during excess, discharge during deficit
            net_energy = energy_generated - energy_consumed
            
            if net_energy > 0:  # Excess energy, charge battery
                charge_amount = min(net_energy * battery_efficiency, 
                                  (100 - battery_level) / 100 * battery_capacity)
                battery_level += (charge_amount / battery_capacity) * 100
            elif net_energy < 0:  # Energy deficit, discharge battery
                discharge_amount = min(abs(net_energy), 
                                     (battery_level / 100) * battery_capacity)
                battery_level -= (discharge_amount / battery_capacity) * 100
                energy_generated += discharge_amount  # Add battery energy to generation
            
            battery_level = max(0, min(100, battery_level))
            meter_config['current_battery_level'] = battery_level
        
        # Calculate trading parameters
        net_energy = energy_generated - energy_consumed
        surplus_energy = max(0, net_energy)
        deficit_energy = max(0, -net_energy)
        
        energy_available_for_sale = surplus_energy * 0.8  # Reserve 20% for self-consumption buffer
        energy_needed_from_grid = deficit_energy if not meter_config['has_battery'] or battery_level < 10 else max(0, deficit_energy - (battery_level/100 * meter_config.get('battery_capacity', 0)))
        
        # Trading preferences based on strategy
        strategy = meter_config['trading_strategy']
        base_sell_price = meter_config['preferred_sell_price']
        base_buy_price = meter_config['preferred_buy_price']
        
        if strategy == 'Aggressive':
            max_sell_price = base_sell_price * random.uniform(1.1, 1.3)
            max_buy_price = base_buy_price * random.uniform(0.8, 0.95)
        elif strategy == 'Conservative':
            max_sell_price = base_sell_price * random.uniform(0.9, 1.05)
            max_buy_price = base_buy_price * random.uniform(1.05, 1.2)
        else:  # Moderate
            max_sell_price = base_sell_price * random.uniform(0.95, 1.15)
            max_buy_price = base_buy_price * random.uniform(0.95, 1.1)
        
        # REC eligibility (Renewable Energy Certificate)
        rec_eligible = meter_config['has_solar'] and energy_generated > 0
        carbon_offset = energy_generated * 0.7 if rec_eligible else 0  # kg CO2 offset per kWh
        
        # Electrical parameters
        voltage = random.gauss(240.0, 3.0)
        total_power = energy_generated + energy_consumed
        current = (total_power / voltage * 1000) if voltage > 0 else 0
        power_factor = random.uniform(0.92, 0.98)
        frequency = random.gauss(50.0, 0.05)
        
        return EnergyReading(
            timestamp=timestamp,
            meter_id=meter_config['meter_id'],
            meter_type=meter_config['meter_type'],
            location=meter_config['location'],
            user_type=meter_config['user_type'],
            
            energy_generated=round(energy_generated, 4),
            energy_consumed=round(energy_consumed, 4),
            energy_available_for_sale=round(energy_available_for_sale, 4),
            energy_needed_from_grid=round(energy_needed_from_grid, 4),
            battery_level=round(battery_level, 1),
            
            voltage=round(voltage, 2),
            current=round(current, 3),
            power_factor=round(power_factor, 3),
            frequency=round(frequency, 2),
            temperature=round(panel_temp if meter_config['has_solar'] else random.gauss(25, 3), 1),
            
            irradiance=round(irradiance, 1) if meter_config['has_solar'] else None,
            panel_temperature=round(panel_temp, 1) if meter_config['has_solar'] else None,
            weather_condition=self.current_weather.value,
            
            grid_connection_status=GridConnectionStatus.CONNECTED.value,
            grid_feed_in_rate=round(self.grid_feed_in_rate, 3),
            grid_purchase_rate=round(self.grid_purchase_rate, 3),
            
            surplus_energy=round(surplus_energy, 4),
            deficit_energy=round(deficit_energy, 4),
            trading_preference=strategy,
            max_sell_price=round(max_sell_price, 3),
            max_buy_price=round(max_buy_price, 3),
            
            rec_eligible=rec_eligible,
            carbon_offset=round(carbon_offset, 3)
        )

    def send_to_kafka(self, reading: EnergyReading) -> bool:
        """Send enhanced reading to Kafka with multiple topics"""
        if not self.producer:
            return False
        
        try:
            reading_dict = asdict(reading)
            
            # Send to main energy readings topic
            self.producer.send('energy-readings', 
                             key=reading.meter_id, 
                             value=reading_dict)
            
            # Send trading data to trading topic if surplus or deficit exists
            if reading.surplus_energy > 0 or reading.deficit_energy > 0:
                trading_data = {
                    'timestamp': reading.timestamp,
                    'meter_id': reading.meter_id,
                    'user_type': reading.user_type,
                    'surplus_energy': reading.surplus_energy,
                    'deficit_energy': reading.deficit_energy,
                    'max_sell_price': reading.max_sell_price,
                    'max_buy_price': reading.max_buy_price,
                    'trading_preference': reading.trading_preference,
                    'location': reading.location
                }
                
                self.producer.send('trading-opportunities', 
                                 key=reading.meter_id,
                                 value=trading_data)
                self.stats['trading_opportunities'] += 1
            
            # Send REC data if eligible
            if reading.rec_eligible:
                rec_data = {
                    'timestamp': reading.timestamp,
                    'meter_id': reading.meter_id,
                    'energy_generated': reading.energy_generated,
                    'carbon_offset': reading.carbon_offset,
                    'weather_condition': reading.weather_condition,
                    'irradiance': reading.irradiance
                }
                
                self.producer.send('renewable-certificates',
                                 key=reading.meter_id,
                                 value=rec_data)
                self.stats['rec_generated'] += 1
            
            self.stats['kafka_sends'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to send to Kafka: {e}")
            return False

    def store_in_influxdb(self, reading: EnergyReading) -> bool:
        """Store enhanced reading in InfluxDB"""
        if not self.influxdb_client:
            return False
        
        try:
            from influxdb_client.client.write_api import Point
            
            point = Point("meter_readings") \
                .tag("meter_id", reading.meter_id) \
                .tag("meter_type", reading.meter_type) \
                .tag("location", reading.location) \
                .tag("user_type", reading.user_type) \
                .tag("weather_condition", reading.weather_condition) \
                .field("energy_generated", float(reading.energy_generated)) \
                .field("energy_consumed", float(reading.energy_consumed)) \
                .field("energy_available_for_sale", float(reading.energy_available_for_sale)) \
                .field("energy_needed_from_grid", float(reading.energy_needed_from_grid)) \
                .field("battery_level", float(reading.battery_level)) \
                .field("voltage", float(reading.voltage)) \
                .field("current", float(reading.current)) \
                .field("power_factor", float(reading.power_factor)) \
                .field("frequency", float(reading.frequency)) \
                .field("temperature", float(reading.temperature)) \
                .field("irradiance", float(reading.irradiance) if reading.irradiance else 0.0) \
                .field("panel_temperature", float(reading.panel_temperature) if reading.panel_temperature else 0.0) \
                .field("grid_feed_in_rate", float(reading.grid_feed_in_rate)) \
                .field("grid_purchase_rate", float(reading.grid_purchase_rate)) \
                .field("surplus_energy", float(reading.surplus_energy)) \
                .field("deficit_energy", float(reading.deficit_energy)) \
                .field("max_sell_price", float(reading.max_sell_price)) \
                .field("max_buy_price", float(reading.max_buy_price)) \
                .field("rec_eligible", reading.rec_eligible) \
                .field("carbon_offset", float(reading.carbon_offset)) \
                .time(reading.timestamp)
            
            self.influxdb_write_api.write(bucket=self.influxdb_bucket, record=point)
            self.stats['db_stores'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to store in InfluxDB: {e}")
            return False

    def save_to_file(self, reading: EnergyReading) -> bool:
        """Save reading to JSONL file"""
        try:
            with open(self.output_file, 'a') as f:
                json.dump(asdict(reading), f, default=str)
                f.write('\n')
            
            self.stats['file_saves'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to save to file: {e}")
            return False

    def simulate_readings(self):
        """Generate and process all meter readings"""
        logger.info(f"Generating enhanced readings for {len(self.meters)} meters")
        
        batch_readings = []
        
        for meter_config in self.meters:
            try:
                reading = self.generate_enhanced_reading(meter_config)
                batch_readings.append(reading)
                
                self.stats['total_readings'] += 1
                
                # Send to various outputs
                kafka_success = self.send_to_kafka(reading)
                db_success = self.store_in_influxdb(reading)
                file_success = self.save_to_file(reading)
                
                # Broadcast to WebSocket clients
                if self.ws_server:
                    self.ws_server.broadcast_reading_sync(reading)
                    self.stats['ws_broadcasts'] += 1
                
                if not (kafka_success or db_success or file_success):
                    logger.warning(f"Failed to store reading for {meter_config['meter_id']}")
                
            except Exception as e:
                logger.error(f"Failed to process meter {meter_config['meter_id']}: {e}")
        
        # Flush Kafka producer
        if self.producer:
            try:
                self.producer.flush()
            except Exception as e:
                logger.error(f"Failed to flush Kafka: {e}")
        
        # Broadcast batch to WebSocket clients
        if self.ws_server and batch_readings:
            self.ws_server.broadcast_batch_sync(batch_readings)
        
        # Log summary
        total_surplus = sum(r.surplus_energy for r in batch_readings)
        total_deficit = sum(r.deficit_energy for r in batch_readings)
        total_generation = sum(r.energy_generated for r in batch_readings)
        total_consumption = sum(r.energy_consumed for r in batch_readings)
        
        logger.info(f"Cycle Summary - Generation: {total_generation:.2f} kWh, "
                   f"Consumption: {total_consumption:.2f} kWh, "
                   f"Surplus: {total_surplus:.2f} kWh, "
                   f"Deficit: {total_deficit:.2f} kWh")

    # Control Methods
    def start(self):
        """Start simulation"""
        if self.is_running:
            logger.warning("Simulation is already running")
            return False
        
        try:
            self.is_running = True
            self.is_paused = False
            self.last_error = None
            
            # Initialize WebSocket server if enabled and not already started
            if self.ws_enabled and not self.ws_server:
                self.ws_server = WebSocketServer(host=self.ws_host, port=self.ws_port)
                self.ws_server.start()
                logger.info(f"WebSocket server started on ws://{self.ws_host}:{self.ws_port}")
            
            logger.info("Simulation started successfully")
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to start simulation: {e}")
            self.is_running = False
            return False

    def stop(self):
        """Stop simulation"""
        if not self.is_running:
            logger.warning("Simulation is not running")
            return False
        
        try:
            self.is_running = False
            self.is_paused = False
            
            # Note: We don't stop WebSocket server here as it might be used by other components
            
            logger.info("Simulation stopped successfully")
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to stop simulation: {e}")
            return False

    def pause(self):
        """Pause simulation"""
        if not self.is_running:
            logger.warning("Simulation is not running")
            return False
        
        if self.is_paused:
            logger.warning("Simulation is already paused")
            return False
        
        self.is_paused = True
        logger.info("Simulation paused")
        return True

    def resume(self):
        """Resume simulation"""
        if not self.is_running:
            logger.warning("Simulation is not running")
            return False
        
        if not self.is_paused:
            logger.warning("Simulation is not paused")
            return False
        
        self.is_paused = False
        logger.info("Simulation resumed")
        return True

    def restart(self):
        """Restart simulation"""
        logger.info("Restarting simulation...")
        
        # Stop current simulation
        if self.is_running:
            self.stop()
        
        # Reset statistics
        self.stats = {
            'total_readings': 0,
            'kafka_sends': 0,
            'db_stores': 0,
            'file_saves': 0,
            'trading_opportunities': 0,
            'rec_generated': 0,
            'ws_broadcasts': 0
        }
        
        # Reset weather
        self.current_weather = WeatherCondition.SUNNY
        self.weather_duration = 0
        self.weather_change_interval = random.randint(3, 8)
        
        # Clear error
        self.last_error = None
        
        # Start simulation again
        return self.start()

    def update_meter_count(self, new_count: int) -> bool:
        """Update number of meters"""
        if new_count < 1:
            logger.error("Meter count must be at least 1")
            return False
        
        if new_count > 1000:
            logger.error("Meter count cannot exceed 1000 for performance reasons")
            return False
        
        try:
            old_count = len(self.meters)  # Use actual current meter count
            self.num_meters = new_count
            
            # Reinitialize meters with new count
            self.meters = self.initialize_enhanced_meters()
            
            logger.info(f"Meter count updated from {old_count} to {new_count}")
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to update meter count: {e}")
            # Restore original count
            self.num_meters = old_count
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get current simulator status"""
        return {
            "running": self.is_running,
            "paused": self.is_paused,
            "num_meters": len(self.meters),
            "configured_meters": self.num_meters,
            "simulation_interval": self.simulation_interval,
            "current_weather": self.current_weather.value,
            "total_readings": self.stats['total_readings'],
            "kafka_available": self.producer is not None,
            "database_available": self.db_conn is not None,
            "influxdb_available": self.influxdb_client is not None,
            "websocket_available": self.ws_server is not None,
            "websocket_connected_clients": len(self.ws_server.clients) if self.ws_server else 0,
            "mode": "Standalone" if self.standalone_mode else "Integrated",
            "last_error": self.last_error,
            "uptime_seconds": self._calculate_uptime()
        }

    def _calculate_uptime(self) -> int:
        """Calculate simulator uptime in seconds (placeholder)"""
        # This would be implemented with proper uptime tracking
        return 0

    def print_statistics(self):
        """Print comprehensive statistics"""
        print(f"\n{'='*60}")
        print("Smart Meter Simulator Statistics")
        print(f"{'='*60}")
        print(f"Total Readings Generated: {self.stats['total_readings']:,}")
        print(f"Kafka Messages Sent: {self.stats['kafka_sends']:,}")
        print(f"Database Records Stored: {self.stats['db_stores']:,}")
        print(f"Files Saved: {self.stats['file_saves']:,}")
        print(f"WebSocket Broadcasts: {self.stats['ws_broadcasts']:,}")
        print(f"Trading Opportunities: {self.stats['trading_opportunities']:,}")
        print(f"REC Certificates Generated: {self.stats['rec_generated']:,}")
        print(f"Current Weather: {self.current_weather.value}")
        print(f"Active Meters: {len(self.meters)}")
        print(f"Simulation Interval: {self.simulation_interval}s")
        print(f"Mode: {'Standalone' if self.standalone_mode else 'Integrated'}")
        if self.ws_server:
            print(f"WebSocket Server: ws://{self.ws_host}:{self.ws_port}")
            print(f"Connected Clients: {len(self.ws_server.clients)}")
        print(f"{'='*60}")

    def run(self):
        """Run simulator"""
        print("Starting Smart Meter Simulator for P2P Energy Trading")
        print("="*70)
        print(f"Meters: {self.num_meters}")
        print(f"Simulation Interval: {self.simulation_interval} seconds")
        print(f"Weather: {self.current_weather.value}")
        print(f"Mode: {'Standalone' if self.standalone_mode else 'Integrated'}")
        print(f"Output File: {self.output_file}")
        
        # Start simulation
        self.start()
        
        # Initialize WebSocket server if enabled
        if self.ws_enabled and not self.ws_server:
            self.ws_server = WebSocketServer(host=self.ws_host, port=self.ws_port)
            self.ws_server.start()
            print(f"WebSocket Server: ws://{self.ws_host}:{self.ws_port}")
        
        print("="*70)
        
        # Print meter summary
        meter_types = {}
        for meter in self.meters:
            meter_type = meter['meter_type']
            meter_types[meter_type] = meter_types.get(meter_type, 0) + 1
        
        print("Meter Distribution:")
        for meter_type, count in meter_types.items():
            print(f"  {meter_type}: {count}")
        print("="*70)
        
        # Schedule periodic readings
        schedule.every(self.simulation_interval).seconds.do(self._scheduled_simulation)
        
        # Generate initial readings
        self.simulate_readings()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down enhanced simulator...")
            self.stop()
            self.print_statistics()
            
            # Stop WebSocket server
            if self.ws_server:
                try:
                    self.ws_server.stop()
                    logger.info("WebSocket server stopped")
                except Exception as e:
                    logger.error(f"Error stopping WebSocket server: {e}")
            
            # Cleanup connections
            if self.producer:
                try:
                    self.producer.close()
                except Exception as e:
                    logger.error(f"Error closing Kafka producer: {e}")
            
            if self.db_conn:
                try:
                    self.db_conn.close()
                except Exception as e:
                    logger.error(f"Error closing database connection: {e}")
            
            if self.influxdb_client:
                try:
                    self.influxdb_client.close()
                except Exception as e:
                    logger.error(f"Error closing InfluxDB connection: {e}")
            
            logger.info("Simulator shutdown complete")

    def _scheduled_simulation(self):
        """Scheduled simulation runner that respects pause state"""
        if self.is_running and not self.is_paused:
            self.simulate_readings()
        elif self.is_running and self.is_paused:
            logger.debug("Simulation is paused, skipping scheduled reading")


# Global simulator instance for API access
_global_simulator: Optional[SmartMeterSimulator] = None

def get_global_simulator() -> Optional[SmartMeterSimulator]:
    """Get global simulator instance"""
    return _global_simulator

def set_global_simulator(simulator: SmartMeterSimulator):
    """Set global simulator instance"""
    global _global_simulator
    _global_simulator = simulator

if __name__ == "__main__":
    simulator = SmartMeterSimulator()
    simulator.run()
