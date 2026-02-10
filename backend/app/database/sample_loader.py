from app.database.connection import engine
from app.database.models import Base, SensorData
from sqlalchemy.orm import Session

# Create tables
Base.metadata.create_all(bind=engine)

# Insert sample data
def insert_sample_data():
    db = Session(bind=engine)
    sample = SensorData(device_id="device_1", value=23.5)
    db.add(sample)
    db.commit()
    db.close()

if __name__ == "__main__":
    insert_sample_data()
    print("Sample data inserted successfully")
