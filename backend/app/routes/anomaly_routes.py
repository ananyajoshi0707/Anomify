from fastapi import APIRouter
from pydantic import BaseModel
from app.kafka.producer import send_sensor_data

router = APIRouter()

class SensorData(BaseModel):
    device_id: str
    value: float

@router.post("/")
def ingest_data(data: SensorData):
    send_sensor_data(data.dict())
    return {"status": "data sent to kafka"}

