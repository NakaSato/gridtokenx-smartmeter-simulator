
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import importlib.util

# Add project root to path (optional, for dependencies but data_source has none internal)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

def load_data_source_module():
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src/smart_meter_simulator/core/data_source.py'))
    spec = importlib.util.spec_from_file_location("data_source", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["data_source"] = module
    spec.loader.exec_module(module)
    return module

try:
    ds_module = load_data_source_module()
    ProfileDataSource = ds_module.ProfileDataSource
except Exception as e:
    logger.error(f"Failed to load ProfileDataSource: {e}")
    sys.exit(1)

def main():
    logger.info("Generating missing SLP profile 'slp_h0'...")
    
    # Initialize Data Source (defaults to data/profiles)
    # Ensure we are in the project root context or specify absolute path if needed.
    # The default "data/profiles" is relative to CWD.
    # If run from project root: python scripts/generate_slp.py -> CWD is root.
    
    data_source = ProfileDataSource()
    
    # Generate H0 profile for 7 days
    # We add some dummy meter IDs. It doesn't matter if they match the simulation exactly
    # because the forecaster falls back gracefully if meter ID is not found in profile,
    # as long as the profile FILE exists to avoid the error log.
    meter_ids = ["M1", "M2", "M3"] 
    
    success = data_source.generate_slp(
        name="slp_h0",
        profile_type="H0",
        annual_kwh=3500,
        days=7,
        meter_ids=meter_ids
    )
    
    if success:
        logger.info("Successfully generated 'slp_h0'")
    else:
        logger.error("Failed to generate 'slp_h0'")

if __name__ == "__main__":
    main()
