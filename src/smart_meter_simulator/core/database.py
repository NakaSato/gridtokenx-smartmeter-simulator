import sqlite3
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str = "smart_meter.db"):
        import os

        # If path is relative, make it absolute relative to project root
        if not os.path.isabs(db_path):
            # Get project root (3 levels up from this file: core -> smart_meter_simulator -> src -> root)
            base_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            print(f"DEBUG: DataBaseManager __file__: {__file__}")
            print(f"DEBUG: DataBaseManager base_dir: {base_dir}")
            self.db_path = os.path.join(base_dir, db_path)
            print(f"DEBUG: DataBaseManager resolved db_path: {self.db_path}")
        else:
            self.db_path = db_path
            print(f"DEBUG: DataBaseManager absolute db_path: {self.db_path}")

        logger.info(f"Using database at: {self.db_path}")
        self.init_db()

    def init_db(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Meters table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS meters (
                        meter_id TEXT PRIMARY KEY,
                        meter_type TEXT,
                        location TEXT,
                        latitude REAL,
                        longitude REAL,
                        zone_id INTEGER,
                        config TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Readings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS readings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meter_id TEXT,
                        timestamp TIMESTAMP,
                        energy_generated REAL,
                        energy_consumed REAL,
                        battery_level REAL,
                        temperature REAL,
                        voltage REAL,
                        current REAL,
                        frequency REAL,
                        surplus_energy REAL,
                        deficit_energy REAL,
                        weather_condition TEXT,
                        FOREIGN KEY (meter_id) REFERENCES meters (meter_id)
                    )
                """)

                # Check for net_emission column and add if missing (Migration)
                try:
                    cursor.execute("SELECT net_emission FROM readings LIMIT 1")
                except sqlite3.OperationalError:
                    logger.info("Migrating database: Adding net_emission column")
                    cursor.execute("ALTER TABLE readings ADD COLUMN net_emission REAL")
                    conn.commit()

                # Check for zone_id column in meters table (Migration)
                try:
                    cursor.execute("SELECT zone_id FROM meters LIMIT 1")
                except sqlite3.OperationalError:
                    logger.info("Migrating database: Adding zone_id column to meters")
                    cursor.execute("ALTER TABLE meters ADD COLUMN zone_id INTEGER")
                    conn.commit()

                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def save_meter(self, meter_config: Dict[str, Any]):
        """Save or update meter configuration"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                meter_id = meter_config.get("meter_id")
                meter_type = meter_config.get("meter_type")
                location = meter_config.get("location")
                latitude = meter_config.get("latitude")
                longitude = meter_config.get("longitude")

                # Serialize full config to JSON
                config_json = json.dumps(meter_config)

                cursor.execute(
                    """
                    INSERT INTO meters (meter_id, meter_type, location, latitude, longitude, config, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(meter_id) DO UPDATE SET
                        meter_type=excluded.meter_type,
                        location=excluded.location,
                        latitude=excluded.latitude,
                        longitude=excluded.longitude,
                        config=excluded.config,
                        updated_at=CURRENT_TIMESTAMP
                """,
                    (meter_id, meter_type, location, latitude, longitude, config_json),
                )

                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save meter {meter_config.get('meter_id')}: {e}")

    def save_reading(self, reading: Any):
        """Save a single energy reading"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO readings (
                        meter_id, timestamp, energy_generated, energy_consumed, 
                        battery_level, temperature, voltage, current, frequency,
                        surplus_energy, deficit_energy, weather_condition, net_emission
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        reading.meter_id,
                        reading.timestamp,
                        reading.energy_generated,
                        reading.energy_consumed,
                        reading.battery_level,
                        reading.temperature,
                        reading.voltage,
                        reading.current,
                        reading.frequency,
                        reading.surplus_energy,
                        reading.deficit_energy,
                        getattr(reading, "weather_condition", "Unknown"),
                        getattr(reading, "net_emission", 0.0),
                    ),
                )

                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save reading for {reading.meter_id}: {e}")

    def save_readings_batch(self, readings: list):
        """Save multiple energy readings in a single transaction for better performance."""
        if not readings:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                data = [
                    (
                        r.meter_id,
                        r.timestamp,
                        r.energy_generated,
                        r.energy_consumed,
                        r.battery_level,
                        r.temperature,
                        r.voltage,
                        r.current,
                        r.frequency,
                        r.surplus_energy,
                        r.deficit_energy,
                        getattr(r, "weather_condition", "Unknown"),
                        getattr(r, "net_emission", 0.0),
                    )
                    for r in readings
                ]
                
                cursor.executemany(
                    """
                    INSERT INTO readings (
                        meter_id, timestamp, energy_generated, energy_consumed, 
                        battery_level, temperature, voltage, current, frequency,
                        surplus_energy, deficit_energy, weather_condition, net_emission
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    data,
                )
                
                conn.commit()
                logger.debug(f"Batch saved {len(readings)} readings")
        except Exception as e:
            logger.error(f"Failed to save readings batch: {e}")

    def delete_meter(self, meter_id: str):
        """Delete a meter and its readings"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM readings WHERE meter_id = ?", (meter_id,))
                cursor.execute("DELETE FROM meters WHERE meter_id = ?", (meter_id,))

                conn.commit()
                logger.info(f"Deleted meter {meter_id} from database")
        except Exception as e:
            logger.error(f"Failed to delete meter {meter_id}: {e}")

    def load_meters(self) -> List[Dict[str, Any]]:
        """Load all meters from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT config FROM meters")
                rows = cursor.fetchall()

                meters = []
                for row in rows:
                    try:
                        meters.append(json.loads(row["config"]))
                    except json.JSONDecodeError:
                        logger.error("Failed to decode meter config")

                logger.info(f"Loaded {len(meters)} meters from database")
                return meters
        except Exception as e:
            logger.error(f"Failed to load meters: {e}")
            return []
