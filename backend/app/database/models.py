from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from app.database.connection import Base

# -----------------------------
# RAW SENSOR DATA (STREAM INPUT)
# -----------------------------
class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    device_id = Column(String, index=True)
    value = Column(Float)
    ts = Column(DateTime(timezone=True), nullable=False)

# -----------------------------
# ANOMALY OUTPUT (ML RESULTS)
# -----------------------------
class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    device_id = Column(String, index=True)
    value = Column(Float)
    anomaly_score = Column(Float)
    is_anomaly = Column(Boolean, default=True)



