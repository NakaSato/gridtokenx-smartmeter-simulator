import asyncio
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from smart_meter_simulator.utils.zk_worker import zk_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_shutdown():
    logger.info("Starting ZKWorkerPool test...")
    
    # 1. Dispatch a task (this initializes the pool)
    logger.info("Dispatching task...")
    result = await zk_pool.generate_bid_data_async(100, 200)
    logger.info(f"Task result received (dummy or real): {result}")
    
    # 2. Shutdown the pool
    logger.info("Shutting down pool...")
    zk_pool.shutdown()
    
    # 3. Verify it's shutdown (executor should be None)
    if zk_pool._executor is None and zk_pool._shutdown is True:
        logger.info("SUCCESS: Pool marked as shutdown and executor cleared.")
    else:
        logger.error("FAILURE: Pool state incorrect after shutdown.")
        sys.exit(1)
        
    # 4. Try to dispatch another task - should be rejected
    logger.info("Attempting to dispatch task after shutdown...")
    result = await zk_pool.generate_bid_data_async(100, 200)
    if result == (None, None, None):
        logger.info("SUCCESS: Task rejected after shutdown.")
    else:
        logger.error("FAILURE: Task not rejected after shutdown.")
        sys.exit(1)

    logger.info("Test complete.")

if __name__ == "__main__":
    asyncio.run(test_shutdown())
