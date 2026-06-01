#!/usr/bin/env python3
"""
InfluxDB Downsampling & Retention Setup Script.
Registers a Flux task in InfluxDB to aggregate raw 'operational_costs' measurements
into an hourly resolution, saving them into a long-term retention bucket.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, BucketRetentionRules

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Load local environment variables
load_dotenv()

# Configuration variables
INFLUX_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN", "admin_token")
INFLUX_ORG = os.getenv("INFLUXDB_ORG", "gridtokenx")
SOURCE_BUCKET = os.getenv("INFLUXDB_BUCKET", "meter_readings")
TARGET_BUCKET = "meter_readings_downsampled"
TASK_NAME = "downsample_operational_costs_hourly"


def main():
    logger.info("Initializing InfluxDB Downsampling Setup...")
    
    # 1. Connect to InfluxDB
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG, timeout=10000)
    
    try:
        # Check connection status via health check
        health = client.health()
        if health.status != "pass":
            logger.error(f"InfluxDB is not ready. Health status: {health.status}")
            sys.exit(1)
            
        logger.info(f"Connected to InfluxDB at {INFLUX_URL} successfully.")
        
        # 2. Get Organization ID
        orgs_api = client.organizations_api()
        orgs = orgs_api.find_organizations(org=INFLUX_ORG)
        if not orgs:
            logger.error(f"Organization '{INFLUX_ORG}' not found.")
            sys.exit(1)
        org_id = orgs[0].id
        logger.info(f"Using Organization ID: {org_id} for '{INFLUX_ORG}'")
        
        # 3. Verify target downsampled bucket exists (or create it with 365 days retention)
        buckets_api = client.buckets_api()
        target_bucket_obj = buckets_api.find_bucket_by_name(TARGET_BUCKET)
        
        if not target_bucket_obj:
            logger.info(f"Target bucket '{TARGET_BUCKET}' not found. Creating it...")
            # 365 days retention = 31,536,000 seconds
            retention_rules = BucketRetentionRules(type="expire", every_seconds=31536000)
            target_bucket_obj = buckets_api.create_bucket(
                bucket_name=TARGET_BUCKET,
                org_id=org_id,
                retention_rules=retention_rules
            )
            logger.info(f"Created target bucket '{TARGET_BUCKET}' with 365 days retention.")
        else:
            logger.info(f"Target bucket '{TARGET_BUCKET}' already exists.")
            
        # 4. Define and Register Flux Task for downsampling
        tasks_api = client.tasks_api()
        existing_tasks = tasks_api.find_tasks(org=INFLUX_ORG)
        task_exists = any(t.name == TASK_NAME for t in existing_tasks)
        
        flux_query = f"""option task = {{
    name: "{TASK_NAME}",
    every: 1h,
    offset: 5m
}}

from(bucket: "{SOURCE_BUCKET}")
    |> range(start: -1h)
    |> filter(fn: (r) => r._measurement == "operational_costs")
    |> aggregateWindow(every: 1h, fn: sum, createEmpty: false)
    |> to(bucket: "{TARGET_BUCKET}", org: "{INFLUX_ORG}")"""
        
        if task_exists:
            logger.info(f"Task '{TASK_NAME}' already registered. Updating task query...")
            # Retrieve specific task to update it
            task_obj = next(t for t in existing_tasks if t.name == TASK_NAME)
            task_obj.flux = flux_query
            tasks_api.update_task(task_obj)
            logger.info(f"Task '{TASK_NAME}' successfully updated.")
        else:
            logger.info(f"Registering new downsampling task '{TASK_NAME}'...")
            tasks_api.create_task(
                name=TASK_NAME,
                flux=flux_query,
                org_id=org_id
            )
            logger.info(f"Task '{TASK_NAME}' successfully created and active.")
            
        logger.info("✅ Downsampling and long-term retention policies successfully setup!")
        
    except Exception as e:
        logger.error(f"An error occurred during InfluxDB task configuration: {e}")
        logger.info("Ensure the InfluxDB instance is running and authorization token is valid.")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
