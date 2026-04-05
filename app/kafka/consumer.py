def start_consumer():
    print("🚀 Consumer starting...")

    import time
    import json
    import pandas as pd
    from kafka import KafkaConsumer
    from kafka.errors import NoBrokersAvailable
    from sklearn.ensemble import IsolationForest
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from app.database.connection import SessionLocal
    from app.database import models

    IST = ZoneInfo("Asia/Kolkata")

    # -----------------------------
    # 🔁 Retry until Kafka is ready
    # -----------------------------
    while True:
        try:
            consumer = KafkaConsumer(
                'sensor-data',
                bootstrap_servers='kafka:9092',
                group_id='anomify-consumer-live',
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            print("✅ Connected to Kafka (Consumer)")
            break
        except NoBrokersAvailable:
            print("❌ Kafka not ready for consumer, retrying in 5 sec...")
            time.sleep(5)

    # -----------------------------
    # DB + ML setup
    # -----------------------------
    session = SessionLocal()
    model = IsolationForest(contamination=0.1, random_state=42)

    window_size = 50
    df_window = pd.DataFrame(columns=["device_id", "value", "timestamp", "ts"])

    print("✅ Consumer & ML ready. Listening for data...")

    # -----------------------------
    # Main consumption loop
    # -----------------------------
    for message in consumer:
        try:
            data = message.value

            # Ensure correct type
            data['value'] = float(data['value'])

            # -----------------------------
            # Timestamp handling (IST)
            # -----------------------------
            if isinstance(data.get('timestamp'), str):
                dt = datetime.fromisoformat(data['timestamp'])
            elif isinstance(data.get('timestamp'), datetime):
                dt = data['timestamp']
            else:
                dt = datetime.now(IST)

            if dt.tzinfo is None:
                dt_ist = dt.replace(tzinfo=IST)
            else:
                dt_ist = dt.astimezone(IST)

            data['ts'] = dt_ist
            data['timestamp'] = dt_ist.replace(tzinfo=None)

            # -----------------------------
            # Sliding window update
            # -----------------------------
            df_window.loc[len(df_window)] = data

            if len(df_window) > window_size:
                df_window = df_window.tail(window_size).reset_index(drop=True)

            latest = df_window.iloc[-1]

            # -----------------------------
            # ALWAYS insert sensor data
            # -----------------------------
            sensor_record = models.SensorData(
                device_id=str(latest['device_id']),
                value=float(latest['value']),
                timestamp=latest['timestamp'],
                ts=latest['ts']
            )
            session.add(sensor_record)

            # -----------------------------
            # ML anomaly detection
            # -----------------------------
            if len(df_window) >= 10:
                model.fit(df_window[['value']])

                df_window['anomaly_score'] = model.decision_function(df_window[['value']])
                df_window['is_anomaly'] = model.predict(df_window[['value']])
                df_window['is_anomaly'] = df_window['is_anomaly'].map({1: False, -1: True})

                latest = df_window.iloc[-1]

                if latest['is_anomaly']:
                    anomaly_record = models.Anomaly(
                        device_id=str(latest['device_id']),
                        value=float(latest['value']),
                        timestamp=latest['ts'],
                        anomaly_score=float(latest['anomaly_score']),
                        is_anomaly=True
                    )
                    session.add(anomaly_record)

                    print("🚨 Anomaly detected:", latest.to_dict())
                else:
                    print("✅ Normal:", latest.to_dict())

            # -----------------------------
            # Commit to DB
            # -----------------------------
            session.commit()

        except Exception as e:
            print("❌ Error processing message:", str(e))
            session.rollback()