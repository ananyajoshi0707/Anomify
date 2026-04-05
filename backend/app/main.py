import os
import threading
from fastapi import FastAPI
from contextlib import asynccontextmanager

from backend.app.routes.anomaly_routes import router as anomaly_router
from backend.app.database.connection import engine
from backend.app.routes.anomaly_routes import router
from backend.app.database import models


# ✅ Create tables
print("📦 Creating database tables...")
models.Base.metadata.create_all(bind=engine)

# ✅ Mode (demo / prod)
MODE = os.getenv("MODE", "demo")  # default = demo


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting Anomify in {MODE.upper()} mode...")

    # 🔥 DEMO MODE → Fake data generator (no Kafka)
    if MODE == "demo":
        from app.demo.simulator import start_demo_stream

        thread = threading.Thread(target=start_demo_stream)
        thread.daemon = True
        thread.start()

        print("📡 Demo data stream started...")

    # 🔥 PROD MODE → Kafka consumer
    elif MODE == "prod":
        from app.kafka.consumer import start_consumer

        thread = threading.Thread(target=start_consumer)
        thread.daemon = True
        thread.start()

        print("📡 Kafka consumer started...")

    else:
        print("⚠️ Unknown MODE, nothing started")

    yield  # ✅ IMPORTANT (app runs here)

    print("🛑 Shutting down Anomify...")


# ✅ FastAPI app
app = FastAPI(
    title="Anomify - Real Time Anomaly Detection",
    lifespan=lifespan
)

# ✅ Routes
app.include_router(anomaly_router, prefix="/anomaly")