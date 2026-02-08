import os
import asyncio
import logging
from datetime import datetime
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_influx():
    url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    token = os.getenv("INFLUXDB_TOKEN")
    org = os.getenv("INFLUXDB_ORG", "gridtokenx")
    bucket = os.getenv("INFLUXDB_BUCKET", "energy_readings")

    if not token:
        logger.error("INFLUXDB_TOKEN not set in environment")
        return False

    logger.info(f"Connecting to InfluxDB at {url}...")
    
    try:
        with InfluxDBClient(url=url, token=token, org=org) as client:
            # Check health
            health = client.health()
            if health.status != "pass":
                logger.error(f"InfluxDB health check failed: {health.message}")
                return False
            
            logger.info("InfluxDB health check PASSED")
            
            # Query latest grid status
            query_api = client.query_api()
            query = f'from(bucket: "{bucket}") |> range(start: -30d) |> filter(fn: (r) => r._measurement == "grid_status") |> last()'
            
            logger.info(f"Querying latest grid_status from bucket '{bucket}'...")
            result = query_api.query(org=org, query=query)
            
            if not result:
                logger.warning("No grid_status records found in the last hour. Is the simulator running?")
                return False
                
            for table in result:
                for record in table.records:
                    logger.info(f"Found record: {record.get_field()} = {record.get_value()} at {record.get_time()}")
            
            return True
    except Exception as e:
        logger.error(f"Error verifying InfluxDB: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_influx())
    if success:
        print("\n✅ InfluxDB Persistence Verified!")
    else:
        print("\n❌ InfluxDB Verification FAILED")
