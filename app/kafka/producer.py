import time
import json
import random
import os
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

producer_running = False  # 🔥 control flag


def create_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP"),

                security_protocol="SASL_SSL",
                sasl_mechanism="PLAIN",
                sasl_plain_username=os.getenv("KAFKA_API_KEY"),
                sasl_plain_password=os.getenv("KAFKA_API_SECRET"),

                value_serializer=lambda v: json.dumps(v).encode("utf-8"),

                # 🔥 RELIABILITY FIXES
                acks="all",
                retries=5,
                linger_ms=10,
                client_id="anomify-producer"
            )

            print("✅ Connected to Confluent Kafka")
            return producer

        except NoBrokersAvailable:
            print("❌ Kafka not reachable, retrying in 5 seconds...")
            time.sleep(5)


def start_producer():
    global producer_running

    producer = create_producer()
    print("🚀 Producer started...")

    while producer_running:
        data = {
            "device_id": random.randint(1, 5),
            "value": random.uniform(20, 100),
            "timestamp": time.time()
        }

        # 🔥 anomaly injection (10%)
        if random.random() < 0.1:
            data["value"] = random.uniform(200, 300)

        try:
            future = producer.send("sensor-data", value=data)

            # 🔥 FORCE DELIVERY CONFIRMATION
            record_metadata = future.get(timeout=10)

            print("📤 Sent:", data)

        except Exception as e:
            print("❌ Send failed:", str(e))

        time.sleep(2)

    print("🛑 Producer stopped")
