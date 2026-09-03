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
courses_collection = db["courses"]
departments_collection = db["departments"]
async def ping_database() -> bool:
    try:
        await client.admin.command("ping")
        return True
    except Exception as exc:
        print(f"[database] Could not connect to MongoDB: {exc}")
        return False


async def ensure_indexes() -> None:
    """
    Create indexes for the fields we filter on most often.
    Without these, every lookup (e.g. 'History' by student_id) is a full
    collection scan, which gets slower as records/scores grow.
    Safe to call on every startup - Mongo no-ops if the index already exists.
    """
    await performance_records_collection.create_index("student_id")
    await performance_scores_collection.create_index("student_id")
    await performance_scores_collection.create_index("record_id")
    await students_collection.create_index("teacher_id")
    await attendance_logs_collection.create_index("student_id")