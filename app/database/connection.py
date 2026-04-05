import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
load_dotenv()
# -----------------------------
# Mode (docker / demo)
# -----------------------------
MODE = os.getenv("MODE", "docker")

# Always read from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL is not set")

print(f"📦 Running in {MODE.upper()} mode")

# Hide password in logs (IMPORTANT)
safe_db_url = DATABASE_URL.split("@")[0].split(":")[0] + ":****@" + DATABASE_URL.split("@")[1]
print(f"📦 Connecting to DB: {safe_db_url}")
# -----------------------------
# Retry logic (VERY IMPORTANT)
# -----------------------------
def create_db_engine():
    for i in range(10):
        try:
            engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                connect_args={"sslmode": "require"}
            )
            # test connection
            conn = engine.connect()
            conn.close()
            print("✅ Database connected")
            return engine
        except Exception as e:
            print(f"❌ DB not ready, retrying... ({i+1}/10)")
            time.sleep(3)

    raise Exception("❌ Could not connect to DB")

engine = create_db_engine()

# -----------------------------
# Session
# -----------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# -----------------------------
# Dependency
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
