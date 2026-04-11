import os
import time
import json
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from sklearn.ensemble import IsolationForest

from app.database.connection import SessionLocal
from app.database import models


IST = ZoneInfo("Asia/Kolkata")


def start_consumer():
    print("🚀 Consumer starting...")

    # -----------------------------
    # 🔁 Retry until Kafka is ready
    # -----------------------------
    while True:
        try:
            consumer = KafkaConsumer(
                "sensor-data",
                bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP"),

                # 🔥 IMPORTANT FIXES
                group_id=None,
                auto_offset_reset="earliest",
                enable_auto_commit=True,

                # 🔐 Confluent Cloud config
                security_protocol="SASL_SSL",
                sasl_mechanism="PLAIN",
                sasl_plain_username=os.getenv("KAFKA_API_KEY"),
                sasl_plain_password=os.getenv("KAFKA_API_SECRET"),

                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                consumer_timeout_ms=1000,
            )

            print("✅ Connected to Confluent Kafka (Consumer)")
            break

        except NoBrokersAvailable:
            print("❌ Kafka not ready, retrying in 5 sec...")
            time.sleep(5)

    # -----------------------------
    # 🧠 ML + DB setup
    # -----------------------------
    session = SessionLocal()
    model = IsolationForest(contamination=0.1, random_state=42)

    window_size = 50
    df_window = pd.DataFrame(columns=["device_id", "value", "timestamp", "ts"])

    print("✅ Consumer & ML ready. Listening for data...")

    # -----------------------------
    # 🔄 POLL LOOP (FIXED)
    # -----------------------------
    while True:
        try:
            msg_pack = consumer.poll(timeout_ms=1000)

            for tp, messages in msg_pack.items():
                for message in messages:
                    data = message.value

                    print("📥 RECEIVED:", data)  # 🔥 DEBUG
                    # 🔥 VALIDATION FIX
                    if not data or "value" not in data or "device_id" not in data:
                     print("⚠️ Skipping invalid message:", data)
                     continue

                    try:
                      data["value"] = float(data["value"])
                    except Exception:
                      print("⚠️ Invalid value format:", data)
                      continue
                    # -----------------------------
                    # Ensure correct type
                    # -----------------------------
                    data["value"] = float(data["value"])
        
                    # -----------------------------
                    # Timestamp handling
                    # -----------------------------
                    if isinstance(data.get("timestamp"), (int, float)):
                        dt = datetime.fromtimestamp(data["timestamp"], IST)
                    elif isinstance(data.get("timestamp"), str):
                        dt = datetime.fromisoformat(data["timestamp"])
                    else:
                        dt = datetime.now(IST)

                    if dt.tzinfo is None:
                        dt_ist = dt.replace(tzinfo=IST)
                    else:
                        dt_ist = dt.astimezone(IST)

                    data["ts"] = dt_ist
                    data["timestamp"] = dt_ist.replace(tzinfo=None)

                    # -----------------------------
                    # Sliding window
                    # -----------------------------
                    df_window.loc[len(df_window)] = data

                    if len(df_window) > window_size:
                        df_window = df_window.tail(window_size).reset_index(drop=True)

                    latest = df_window.iloc[-1]

                    # -----------------------------
                    # Store sensor data
                    # -----------------------------
                    sensor_record = models.SensorData(
                        device_id=str(latest["device_id"]),
                        value=float(latest["value"]),
                        timestamp=latest["timestamp"],
                        ts=latest["ts"],
                    )
                    session.add(sensor_record)

                    # -----------------------------
                    # ML anomaly detection
                    # -----------------------------
                    if len(df_window) >= 10:
                        model.fit(df_window[["value"]])

                        df_window["anomaly_score"] = model.decision_function(
                            df_window[["value"]]
                        )
                        df_window["is_anomaly"] = model.predict(
                            df_window[["value"]]
                        )
                        df_window["is_anomaly"] = df_window["is_anomaly"].map(
                            {1: False, -1: True}
                        )

                        latest = df_window.iloc[-1]

                        if latest["is_anomaly"]:
                            anomaly_record = models.Anomaly(
                                device_id=str(latest["device_id"]),
                                value=float(latest["value"]),
                                timestamp=latest["ts"],
                                anomaly_score=float(latest["anomaly_score"]),
                                is_anomaly=True,
                            )
                            session.add(anomaly_record)

                            print("🚨 Anomaly detected:", latest.to_dict())
                        else:
                            print("✅ Normal:", latest.to_dict())

                    # -----------------------------
                    # Commit DB
                    # -----------------------------
                    session.commit()

        except Exception as e:
            print("❌ Error processing message:", str(e))
            session.rollback()