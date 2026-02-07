
import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def consume_readings(bootstrap_servers, topic, timeout=60):
    """
    Consume readings from Kafka and verify they are coming through.
    """
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        group_id='verify-durability-group'
    )
    
    # Get cluster layout and join group
    await consumer.start()
    logger.info(f"Started Kafka consumer on topic: {topic}")
    
    count = 0
    try:
        # We'll wait for messages for a specific duration
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                # Use a short timeout for each fetch to check the loop condition
                result = await consumer.getmany(timeout_ms=1000)
                for tp, messages in result.items():
                    for msg in messages:
                        payload = json.loads(msg.value.decode('utf-8'))
                        count += 1
                        if count % 20 == 0:
                            logger.info(f"Received {count} readings. Latest meter_id: {payload.get('meter_id')}")
                
                if count > 0 and (asyncio.get_event_loop().time() - start_time > 10):
                    # If we've got some data and 10s passed, we can stop early if we want
                    # but let's just keep going to see the flow
                    pass
                    
            except Exception as e:
                logger.error(f"Error consuming: {e}")
                break
                
    finally:
        await consumer.stop()
        logger.info(f"Consumer stopped. Total received: {count}")
    
    return count

if __name__ == "__main__":
    KAFKA_SERVERS = "localhost:29092"
    KAFKA_TOPIC = "meter-readings"
    
    print(f"--- Kafka Durability Verification ---")
    print(f"Servers: {KAFKA_SERVERS}")
    print(f"Topic: {KAFKA_TOPIC}")
    
    try:
        count = asyncio.run(consume_readings(KAFKA_SERVERS, KAFKA_TOPIC))
        
        if count > 0:
            print(f"\nSUCCESS: Received {count} messages from Kafka.")
        else:
            print(f"\nFAILURE: No messages received from Kafka. Is the simulator sending them?")
    except Exception as e:
        print(f"\nERROR: {e}")
