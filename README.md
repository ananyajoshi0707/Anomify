# 🚨 Anomify — Real-Time Anomaly Detection System

Anomify is a **real-time anomaly detection platform** designed to monitor streaming data and automatically identify unusual patterns using unsupervised machine learning models.  
It is built to be **scalable, production-ready, and cloud-native**, making it suitable for modern data-intensive systems.

## 🔍 Problem Statement
In real-time systems (IoT sensors, transactions, logs), anomalies often go unnoticed until they cause failures or losses.  
Traditional batch-based analysis is slow and ineffective for streaming data.

**Anomify solves this by detecting anomalies instantly as data flows through the system.**

---

## ✨ Key Features
- 📡 Real-time data ingestion using **Apache Kafka**
- 🧠 Unsupervised ML-based anomaly detection
  - Isolation Forest
  - Autoencoder / VAE-based models
- ⚡ Real-time inference & alerting
- 📊 Live visualization using **Grafana**
- 🐳 Dockerized microservices
- ☸️ Kubernetes-ready deployment
- 🕒 Timezone-aware processing (IST supported)
- 🔐 Secure handling of secrets via environment variables

---

## 🏗️ System Architecture (High Level)
1. **Producer** streams live data to Kafka
2. **Kafka Consumer** ingests data
3. **ML Engine** detects anomalies in real time
4. **PostgreSQL** stores sensor data & anomalies
5. **Grafana** visualizes trends and anomalies live

---

## 🧑‍💻 Tech Stack

### Backend & ML
- Python
- FastAPI
- Scikit-learn
- PyTorch (Autoencoders / VAEs)

### Streaming & Storage
- Apache Kafka
- PostgreSQL

### DevOps & Infra
- Docker
- Docker Compose
- Kubernetes
- Grafana

---

🎉 **Project Highlight:**  
> **Anomify has been selected under the CSTUP (Council of Science & Technology, Uttar Pradesh) Project Grant Scheme**, recognizing its innovation and real-world applicability.

---
