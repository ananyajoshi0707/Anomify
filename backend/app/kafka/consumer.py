import json
import pandas as pd
import numpy as np
from kafka import KafkaConsumer
from sklearn.ensemble import IsolationForest
from datetime import datetime
from zoneinfo import ZoneInfo   # ✅ ADDED
from app.database.connection import SessionLocal
from app.database import models

# -----------------------------
# Timezone
# -----------------------------
IST = ZoneInfo("Asia/Kolkata")   # ✅ ADDED

# -----------------------------
# Kafka Consumer
# -----------------------------
consumer = KafkaConsumer(
    'sensor-data',
    bootstrap_servers='localhost:9092',
    group_id='anomify-consumer-live',          # ✅ add this
    auto_offset_reset='latest',              # ✅ change this
    enable_auto_commit=True,                 # ✅ optional but good
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# -----------------------------
# DB session
# -----------------------------
session = SessionLocal()

# -----------------------------
# Isolation Forest model (fit incrementally)
# -----------------------------
model = IsolationForest(contamination=0.1, random_state=42)

# -----------------------------
# Sliding window for anomaly detection
# -----------------------------
window_size = 50
df_window = pd.DataFrame(columns=["device_id", "value", "timestamp", "ts"])  # ✅ ts added

print("Consumer & ML ready. Listening for data...")

for message in consumer:
    data = message.value

    # Ensure correct types
    data['value'] = float(data['value'])

    # -----------------------------
    # FIXED TIMESTAMP HANDLING (STEP 4)
    # -----------------------------
    if isinstance(data.get('timestamp'), str):
        dt = datetime.fromisoformat(data['timestamp'])
    elif isinstance(data.get('timestamp'), datetime):
        dt = data['timestamp']
    else:
        dt = datetime.now(IST)

    # If naive → assume IST
    if dt.tzinfo is None:
        dt_ist = dt.replace(tzinfo=IST)
    else:
        dt_ist = dt.astimezone(IST)

    data['ts'] = dt_ist                           # ✅ timezone-aware (Grafana)
    data['timestamp'] = dt_ist.replace(tzinfo=None)  # ✅ naive IST (Timescale hypertable column)

    # Append to window
    df_window = pd.concat([df_window, pd.DataFrame([data])], ignore_index=True)

    # Keep only last N rows
    if len(df_window) > window_size:
        df_window = df_window.tail(window_size).reset_index(drop=True)

    # -----------------------------
    # ✅ ALWAYS insert latest record into sensor_data (NO MORE GAPS IN GRAFANA)
    # -----------------------------
    latest = df_window.iloc[-1]
    sensor_record = models.SensorData(
        device_id=str(latest['device_id']),
        value=float(latest['value']),
        timestamp=latest['timestamp'],  # naive IST (hypertable partition column)
        ts=latest['ts']                 # timezone-aware IST (Grafana uses this)
    )
    session.add(sensor_record)

    # -----------------------------
    # Train Isolation Forest if enough data (ML should NOT block ingestion)
    # -----------------------------
    if len(df_window) >= 10:
        model.fit(df_window[['value']])
        df_window['anomaly_score'] = model.decision_function(df_window[['value']])
        df_window['is_anomaly'] = model.predict(df_window[['value']])
        df_window['is_anomaly'] = df_window['is_anomaly'].map({1: False, -1: True})

        # Re-read latest after ML columns updated
        latest = df_window.iloc[-1]

        # -----------------------------
        # Insert anomaly if detected
        # -----------------------------
        if latest['is_anomaly']:
            anomaly_record = models.Anomaly(
                device_id=str(latest['device_id']),
                value=float(latest['value']),
                timestamp=latest['ts'],  # ✅ anomalies.timestamp is TIMESTAMPTZ, so use aware time
                anomaly_score=float(latest['anomaly_score']),
                is_anomaly=True
            )
            session.add(anomaly_record)
            print("Anomaly detected & saved:", latest.to_dict())
        else:
            print("Normal data:", latest.to_dict())

    # -----------------------------
    # ✅ COMMIT ALWAYS (so every message appears in Grafana Last 5 minutes)
    # -----------------------------
    session.commit()




