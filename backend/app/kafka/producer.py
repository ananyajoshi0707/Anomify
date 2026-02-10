import json
import time
import random
from kafka import KafkaProducer
from datetime import datetime, timezone

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def generate_sensor_data():
    return {
        "device_id": f"sensor-{random.randint(1, 5)}",
        "value": round(random.uniform(10, 100), 2),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    while True:
        data = generate_sensor_data()
        producer.send("sensor-data", value=data)
        print("Sent:", data)
        time.sleep(2)



