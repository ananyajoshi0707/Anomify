import time
import json
import random
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

def create_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("✅ Connected to Kafka")
            return producer
        except NoBrokersAvailable:
            print("❌ Kafka not ready, retrying in 5 seconds...")
            time.sleep(5)

producer = create_producer()

while True:
    data = {
        "device_id": random.randint(1, 5),
        "value": random.uniform(20, 100)
    }

    producer.send("sensor-data", data)
    print("Sent:", data)

    time.sleep(2)



