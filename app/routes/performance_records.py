from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from app.database import (
    performance_records_collection,
    performance_scores_collection,
    weight_configs_collection,
    students_collection,
)
from app.models.performance_record import (
    PerformanceRecordCreate,
    PerformanceRecordOut,
    PerformanceRecordUpdate,
)
from app.models.utils import serialize_document, serialize_documents
from app.security import require_role
from app.scoring import calculate_weighted_score, classify_score

router = APIRouter(prefix="/records", tags=["performance-records"])


async def _recalculate_score(student_id: str, record: dict, record_id: str):
    """Shared helper: recompute and store the weighted score for a given record."""
    config = await weight_configs_collection.find_one(sort=[("last_updated", -1)])
    if not config:
        raise HTTPException(
            status_code=400,
            detail="No weight configuration exists yet - ask an admin to set one first",
        )

    weighted_score = calculate_weighted_score(
        attendance_percent=record["attendance_percent"],
        assignment_score=record["assignment_score"],
        exam_score=record["exam_score"],
        attendance_weight=config["attendance_weight"],
        assignment_weight=config["assignment_weight"],
        exam_weight=config["exam_weight"],
    )
    category = classify_score(weighted_score)

    # Remove any previous score tied to this exact record, then insert a fresh one
    await performance_scores_collection.delete_many({"record_id": record_id})
    score_doc = {
        "student_id": student_id,
        "record_id": record_id,
        "config_id": str(config["_id"]),
        "weighted_score": weighted_score,
        "category": category.value,
        "calculated_date": datetime.utcnow(),
    }
    await performance_scores_collection.insert_one(score_doc)

@router.get("/me", response_model=list[PerformanceRecordOut])
async def get_my_records(current_user: dict = Depends(require_role("student"))):
    """A logged-in student fetches their own performance records."""
    records = await performance_records_collection.find(
        {"student_id": current_user["user_id"]}
    ).to_list(length=None)
    return serialize_documents(records)

@router.post("/", response_model=PerformanceRecordOut)
async def create_performance_record(
    record: PerformanceRecordCreate,
    current_user: dict = Depends(require_role("admin", "teacher")),
):
    student = await students_collection.find_one({"_id": ObjectId(record.student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if current_user["role"] == "teacher" and student.get("teacher_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only add records for your own students")

    record_doc = {
        "student_id": record.student_id,
        "attendance_percent": record.attendance_percent,
        "assignment_score": record.assignment_score,
        "exam_score": record.exam_score,
        "semester": record.semester,
        "date_recorded": datetime.utcnow(),
    }
    result = await performance_records_collection.insert_one(record_doc)
    created_record = await performance_records_collection.find_one({"_id": result.inserted_id})

    await _recalculate_score(record.student_id, record_doc, str(result.inserted_id))

    return serialize_document(created_record)


@router.get("/", response_model=list[PerformanceRecordOut])
async def list_records(current_user: dict = Depends(require_role("admin", "teacher"))):
    if current_user["role"] == "teacher":
        my_students = await students_collection.find(
            {"teacher_id": current_user["user_id"]}
        ).to_list(length=None)
        my_student_ids = [str(s["_id"]) for s in my_students]
        records = await performance_records_collection.find(
            {"student_id": {"$in": my_student_ids}}
        ).to_list(length=None)
    else:
        records = await performance_records_collection.find().to_list(length=None)
    return serialize_documents(records)


@router.get("/student/{student_id}", response_model=list[PerformanceRecordOut])
async def get_records_for_student(
    student_id: str,
    current_user: dict = Depends(require_role("admin", "teacher", "student")),
):
    if current_user["role"] == "student" and current_user["user_id"] != student_id:
        raise HTTPException(status_code=403, detail="You can only view your own records")

    records = await performance_records_collection.find({"student_id": student_id}).to_list(length=None)
    return serialize_documents(records)


@router.put("/{record_id}", response_model=PerformanceRecordOut)
async def update_performance_record(
    record_id: str,
    update: PerformanceRecordUpdate,
    current_user: dict = Depends(require_role("admin", "teacher")),
):
    existing = await performance_records_collection.find_one({"_id": ObjectId(record_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Record not found")

    if current_user["role"] == "teacher":
        student = await students_collection.find_one({"_id": ObjectId(existing["student_id"])})
        if not student or student.get("teacher_id") != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="You can only edit records for your own students")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await performance_records_collection.update_one(
            {"_id": ObjectId(record_id)}, {"$set": update_data}
        )

    updated = await performance_records_collection.find_one({"_id": ObjectId(record_id)})
    await _recalculate_score(updated["student_id"], updated, record_id)

    return serialize_document(updated)


@router.delete("/{record_id}")
async def delete_performance_record(
    record_id: str,
    current_user: dict = Depends(require_role("admin", "teacher")),
):
    existing = await performance_records_collection.find_one({"_id": ObjectId(record_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Record not found")

    if current_user["role"] == "teacher":
        student = await students_collection.find_one({"_id": ObjectId(existing["student_id"])})
        if not student or student.get("teacher_id") != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="You can only delete records for your own students")

    await performance_records_collection.delete_one({"_id": ObjectId(record_id)})
    await performance_scores_collection.delete_many({"record_id": record_id})

    return {"detail": "Record deleted successfully"}