from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.db_name]

# Collections - matches the 6 entities from the ERD
admins_collection = db["admins"]
teachers_collection = db["teachers"]
students_collection = db["students"]
performance_records_collection = db["performance_records"]
weight_configs_collection = db["weight_configs"]
performance_scores_collection = db["performance_scores"]
attendance_logs_collection = db["attendance_logs"]

async def ping_database() -> bool:
    try:
        await client.admin.command("ping")
        return True
    except Exception as exc:
        print(f"[database] Could not connect to MongoDB: {exc}")
        return False