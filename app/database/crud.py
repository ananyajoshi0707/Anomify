from sqlalchemy.orm import Session
from app.database import models
from datetime import datetime


# -----------------------------
# SENSOR DATA OPERATIONS
# -----------------------------
def create_sensor_data(
    db: Session,
    device_id: str,
    value: float,
    timestamp: datetime | None = None
):
    sensor_data = models.SensorData(
        device_id=device_id,
        value=value,
        timestamp=timestamp or datetime.utcnow()
    )

    db.add(sensor_data)
    db.commit()
    db.refresh(sensor_data)
    return sensor_data


def get_recent_sensor_data(
    db: Session,
    device_id: str,
    limit: int = 100
):
    return (
        db.query(models.SensorData)
        .filter(models.SensorData.device_id == device_id)
        .order_by(models.SensorData.timestamp.desc())
        .limit(limit)
        .all()
    )


# -----------------------------
# ANOMALY OPERATIONS
# -----------------------------
def create_anomaly(
    db: Session,
    metric_name: str,
    value: float,
    anomaly_score: float,
    is_anomaly: bool,
    timestamp: datetime | None = None
):
    anomaly = models.Anomaly(
        metric_name=metric_name,
        value=value,
        anomaly_score=anomaly_score,
        is_anomaly=is_anomaly,
        timestamp=timestamp or datetime.utcnow()
    )

    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    return anomaly


def get_recent_anomalies(
    db: Session,
    metric_name: str,
    limit: int = 50
):
    return (
        db.query(models.Anomaly)
        .filter(models.Anomaly.metric_name == metric_name)
        .order_by(models.Anomaly.timestamp.desc())
        .limit(limit)
        .all()
    )
