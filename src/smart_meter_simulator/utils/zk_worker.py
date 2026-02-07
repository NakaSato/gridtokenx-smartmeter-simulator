import logging
import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, Any, List, Optional
import functools

logger = logging.getLogger(__name__)

# This function must be at the top level for multiprocessing serialization
def _generate_zk_proof_worker(amount_u64: int, price_u64: int) -> tuple:
    """Worker function to generate ZK proofs in a separate process."""
    try:
        from gridtokenx_py import ZkProver
        return ZkProver.generate_bid_data(amount_u64, price_u64)
    except Exception as e:
        logger.error(f"Error in ZK worker process: {e}")
        return None, None, None

class ZkWorkerPool:
    """Manages a pool of processes for ZK proof generation."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ZkWorkerPool, cls).__new__(cls)
            cls._instance._executor = ProcessPoolExecutor(max_workers=None) # Defaults to CPU count
            logger.info("Initialized ZKWorkerPool with ProcessPoolExecutor")
        return cls._instance

    async def generate_bid_data_async(self, amount_u64: int, price_u64: int) -> tuple:
        """Asynchronously dispatch ZK proof generation to the process pool."""
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                self._executor, 
                _generate_zk_proof_worker, 
                amount_u64, 
                price_u64
            )
        except Exception as e:
            logger.error(f"Failed to dispatch ZK task: {e}")
            return None, None, None

    def shutdown(self):
        """Shutdown the process pool."""
        if self._executor:
            self._executor.shutdown(wait=True)
            logger.info("ZKWorkerPool shutdown complete")

# Global singleton
zk_pool = ZkWorkerPool()
