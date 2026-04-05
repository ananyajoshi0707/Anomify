import random
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from sklearn.ensemble import IsolationForest

from app.database.connection import SessionLocal
from app.database import models

IST = ZoneInfo("Asia/Kolkata")

def start_demo_stream():
    print("🟣 DEMO MODE: Generating fake data...")

    session = SessionLocal()
    model = IsolationForest(contamination=0.1, random_state=42)

    window_size = 50
    df_window = pd.DataFrame(columns=["device_id", "value", "timestamp", "ts"])

    while True:
        try:
            # 🔥 simulate sensor data
            data = {
                "device_id": random.randint(1, 5),
                "value": random.uniform(20, 100),
            }

            dt_ist = datetime.now(IST)

            data["ts"] = dt_ist
            data["timestamp"] = dt_ist.replace(tzinfo=None)

            df_window.loc[len(df_window)] = data

            if len(df_window) > window_size:
                df_window = df_window.tail(window_size).reset_index(drop=True)

            latest = df_window.iloc[-1]

            # ✅ Insert sensor data
            sensor_record = models.SensorData(
                device_id=str(latest["device_id"]),
                value=float(latest["value"]),
                timestamp=latest["timestamp"],
                ts=latest["ts"],
            )
            session.add(sensor_record)

            # 🤖 ML logic
            if len(df_window) >= 10:
                model.fit(df_window[["value"]])
                df_window["anomaly_score"] = model.decision_function(df_window[["value"]])
                df_window["is_anomaly"] = model.predict(df_window[["value"]])
                df_window["is_anomaly"] = df_window["is_anomaly"].map({1: False, -1: True})

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

                    print("🚨 DEMO Anomaly:", latest.to_dict())
                else:
                    print("✅ DEMO Normal:", latest.to_dict())

            session.commit()

            time.sleep(2)

        except Exception as e:
            print("❌ DEMO Error:", e)
            session.rollback()