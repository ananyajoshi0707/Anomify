from dotenv import load_dotenv
load_dotenv()  # ✅ load env FIRST

import os
import threading
import importlib
from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.routes.anomaly_routes import router as anomaly_router
from app.database.connection import engine
from app.database import models

# ✅ Create tables
print("📦 Creating database tables...")
models.Base.metadata.create_all(bind=engine)

# ✅ Mode (demo / prod)
MODE = os.getenv("MODE", "demo")

# ✅ Router for producer APIs
router = APIRouter()

# ✅ Thread reference
producer_thread = None


# -----------------------------
# 🚀 Lifespan (startup logic)
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting Anomify in {MODE.upper()} mode...")

    if MODE == "demo":
        from app.demo.simulator import start_demo_stream

        thread = threading.Thread(target=start_demo_stream)
        thread.daemon = True
        thread.start()

        print("📡 Demo data stream started...")

    elif MODE == "prod":
        from app.kafka.consumer import start_consumer

        thread = threading.Thread(target=start_consumer)
        thread.daemon = True
        thread.start()

        print("📡 Kafka consumer started...")

    else:
        print("⚠️ Unknown MODE")

    yield

    print("🛑 Shutting down Anomify...")


# -----------------------------
# 🚀 FastAPI App
# -----------------------------
app = FastAPI(
    title="Anomify - Real Time Anomaly Detection",
    lifespan=lifespan
)


# -----------------------------
# 🚀 Producer APIs (FIXED)
# -----------------------------
@router.post("/start-producer")
def start_producer_api():
    global producer_thread

    # 🔥 Always load fresh module (fix reload bug)
    prod = importlib.import_module("app.kafka.producer")

    # Safety check
    if not hasattr(prod, "producer_running"):
        prod.producer_running = False

    if not prod.producer_running:
        prod.producer_running = True

        producer_thread = threading.Thread(target=prod.start_producer)
        producer_thread.daemon = True
        producer_thread.start()

        return {"message": "Producer started"}

    return {"message": "Already running"}


@router.post("/stop-producer")
def stop_producer_api():
    prod = importlib.import_module("app.kafka.producer")

    prod.producer_running = False
    return {"message": "Producer stopped"}


# -----------------------------
# 🚀 Routes
# -----------------------------
app.include_router(anomaly_router, prefix="/anomaly")
app.include_router(router)


# -----------------------------
# 🚀 CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)