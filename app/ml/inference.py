import numpy as np
from sklearn.ensemble import IsolationForest

model = IsolationForest(contamination=0.05)
model.fit(np.array([[10], [12], [11], [13], [12]]))  # baseline

def detect_anomaly(data):
    value = np.array([[data["value"]]])
    prediction = model.predict(value)

    if prediction[0] == -1:
        print("🚨 ANOMALY DETECTED:", data)
    else:
        print("✅ Normal:", data)

