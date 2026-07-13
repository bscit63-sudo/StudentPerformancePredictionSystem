from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.database import attendance_logs_collection, students_collection
from app.models.attendance_log import AttendanceBulkMarkRequest, AttendanceLogOut, AttendancePercentageOut
from app.models.utils import serialize_documents
from app.security import require_role

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/mark")
async def mark_attendance(
    payload: AttendanceBulkMarkRequest,
    current_user: dict = Depends(require_role("admin", "teacher")),
):
    """
    A teacher marks present/absent for some or all of their students on one date.
    Marking the same student + date again overwrites the previous entry
    (upsert) rather than creating a duplicate.
    """
    date_str = payload.date.isoformat()
    results = []

    for entry in payload.entries:
        student = await students_collection.find_one({"_id": ObjectId(entry.student_id)})
        if not student:
            continue
        if current_user["role"] == "teacher" and student.get("teacher_id") != current_user["user_id"]:
            continue  # skip students that don't belong to this teacher

        await attendance_logs_collection.update_one(
            {"student_id": entry.student_id, "date": date_str},
            {
                "$set": {
                    "student_id": entry.student_id,
                    "date": date_str,
                    "status": entry.status.value,
                    "marked_by": current_user["user_id"],
                    "created_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
        results.append(entry.student_id)

    return {"marked_for_date": date_str, "students_marked": len(results)}


@router.get("/student/{student_id}", response_model=list[AttendanceLogOut])
async def get_attendance_for_student(
    student_id: str,
    current_user: dict = Depends(require_role("admin", "teacher", "student")),
):
    if current_user["role"] == "student" and current_user["user_id"] != student_id:
        raise HTTPException(status_code=403, detail="You can only view your own attendance")

    logs = await attendance_logs_collection.find({"student_id": student_id}).sort("date", -1).to_list(length=None)
    return serialize_documents(logs)


@router.get("/me", response_model=list[AttendanceLogOut])
async def get_my_attendance(current_user: dict = Depends(require_role("student"))):
    logs = await attendance_logs_collection.find(
        {"student_id": current_user["user_id"]}
    ).sort("date", -1).to_list(length=None)
    return serialize_documents(logs)


@router.get("/percentage/{student_id}", response_model=AttendancePercentageOut)
async def get_attendance_percentage(
    student_id: str,
    current_user: dict = Depends(require_role("admin", "teacher", "student")),
):
    if current_user["role"] == "student" and current_user["user_id"] != student_id:
        raise HTTPException(status_code=403, detail="You can only view your own attendance")

    logs = await attendance_logs_collection.find({"student_id": student_id}).to_list(length=None)
    total = len(logs)
    present = sum(1 for log in logs if log["status"] == "present")
    percent = round((present / total) * 100, 2) if total > 0 else 0.0

    return {
        "student_id": student_id,
        "total_days_marked": total,
        "days_present": present,
        "attendance_percent": percent,
    }