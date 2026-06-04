import asyncio
import logging
import time
import os
import sys
from datetime import datetime
from typing import List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from smart_meter_simulator.meter_generator import MeterGenerator
from smart_meter_simulator.devices.ami import SmartMeter
from smart_meter_simulator.transport.grpc import GrpcTransport
from smart_meter_simulator.core.reading_manager import ReadingManager
from smart_meter_simulator.config import get_config
import redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("load_test_100k")

async def run_load_test(num_meters: int, interval: int = 5):
    config = get_config()
    logger.info(f"🚀 Initializing 100k Scale Load Test: meters={num_meters}, interval={interval}s")
    
    # 1. Generate Meter Configs
    generator = MeterGenerator(num_meters)
    meter_configs = generator.generate_meters()
    
    # 2. Instantiate Meters (Memory Intensive)
    logger.info(f"📦 Creating {num_meters} SmartMeter objects...")
    start_time = time.time()
    meters = [SmartMeter(cfg) for cfg in meter_configs]
    logger.info(f"✅ Created in {time.time() - start_time:.2f}s")
    
    # 3. Register Keys in Redis (Batch)
    logger.info("🔑 Registering public keys in Redis...")
    try:
        r = redis.from_url(config.redis_url)
        # Fast check if redis is up
        r.ping()
        pipe = r.pipeline()
        for m in meters:
            key = f"gridtokenx:devices:{m.meter_id}:pubkey"
            pipe.set(key, m.key_manager.get_public_key_hex())
        pipe.execute()
        logger.info(f"✅ Registered {num_meters} keys")
    except Exception as e:
        logger.warning(f"⚠️ Redis registration skipped (likely down): {e}")

    # 4. Initialize Transport & Manager
    transport = GrpcTransport(host=config.grpc_gateway_host, port=config.grpc_gateway_port)
    await transport.connect()
    from smart_meter_simulator.core.data_source import ProfileDataSource
    data_source = ProfileDataSource()
    manager = ReadingManager(data_source=data_source)
    
    logger.info(f"🔥 Starting simulation loop...")
    tick = 0
    try:
        while True:
            tick += 1
            now = datetime.now()
            logger.info(f"--- Tick {tick} start ---")
            
            # 5. Generate Raw Batch (Rust Accelerated)
            start_gen = time.time()
            packed_frames = manager.generate_v4_batch_raw(
                meters=meters,
                timestamp=now,
                interval=900,
                weather_mode="Sunny"
            )
            gen_duration = time.time() - start_gen
            logger.info(f"🧬 Generated {len(packed_frames)} frames in {gen_duration*1000:.2f}ms")
            
            if not packed_frames:
                logger.error("❌ Generation failed (Rust engine might not be loaded)")
                break
                
            # 6. Flatten and Send (Bulk gRPC)
            start_send = time.time()
            if packed_frames and isinstance(packed_frames[0], list):
                logger.info("Converting list of ints to bytes...")
                packed_frames = [bytes(f) for f in packed_frames]
            
            # Each item in packed_frames is [Len(1)] + [Frame] + [Sig(64)]
            bulk_payload = b"".join(packed_frames)
            
            success = await transport.send_bulk_raw(bulk_payload, len(meters))
            send_duration = time.time() - start_send
            
            total_duration = gen_duration + send_duration
            tps = len(meters) / total_duration if total_duration > 0 else 0
            
            logger.info(f"📤 Sent in {send_duration*1000:.2f}ms. Total={total_duration*1000:.2f}ms. Effective TPS={tps:.2f}")
            
            if total_duration > interval:
                logger.warning(f"⚠️ Loop lag: tick took {total_duration:.2f}s (interval={interval}s)")
            
            await asyncio.sleep(max(0.1, interval - total_duration))
            
    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")
    finally:
        await transport.disconnect()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--meters", type=int, default=100000)
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()
    
    asyncio.run(run_load_test(args.meters, args.interval))
