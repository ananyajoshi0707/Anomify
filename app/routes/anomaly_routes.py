from fastapi import APIRouter
from pydantic import BaseModel
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import json
import time

router = APIRouter()

class SensorData(BaseModel):
    device_id: str
    value: float

def get_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("✅ API connected to Kafka")
            return producer
        except NoBrokersAvailable:
            print("❌ Kafka not ready (API), retrying...")
            time.sleep(5)

@router.post("/")
def ingest_data(data: SensorData):
    producer = get_producer()
    producer.send("sensor-data", data.dict())
    return {"status": "data sent to kafka"}

