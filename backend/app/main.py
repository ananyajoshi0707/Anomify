from fastapi import FastAPI
from app.routes.anomaly_routes import router as anomaly_router

app = FastAPI(title="Anomify - Real Time Anomaly Detection")

app.include_router(anomaly_router, prefix="/anomaly")
