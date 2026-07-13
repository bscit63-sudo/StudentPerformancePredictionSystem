import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.database import (
    students_collection,
    performance_records_collection,
    performance_scores_collection,
)
from app.security import require_role

router = APIRouter(prefix="/reports", tags=["reports"])


async def _get_visible_students(current_user: dict) -> list[dict]:
    """Admins see all students; teachers see only their own."""
    if current_user["role"] == "teacher":
        return await students_collection.find({"teacher_id": current_user["user_id"]}).to_list(length=None)
    return await students_collection.find().to_list(length=None)


def _csv_response(rows: list[dict], fieldnames: list[str], filename: str) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/summary.csv")
async def export_summary_csv(current_user: dict = Depends(require_role("admin", "teacher"))):
    """
    One row per student: their latest weighted score and category.
    """
    students = await _get_visible_students(current_user)
    student_ids = [str(s["_id"]) for s in students]
    students_by_id = {str(s["_id"]): s for s in students}

    scores = await performance_scores_collection.find(
        {"student_id": {"$in": student_ids}}
    ).to_list(length=None)

    latest_by_student = {}
    for s in scores:
        existing = latest_by_student.get(s["student_id"])
        if not existing or s["calculated_date"] > existing["calculated_date"]:
            latest_by_student[s["student_id"]] = s

    rows = []
    for student_id, student in students_by_id.items():
        score = latest_by_student.get(student_id)
        rows.append({
            "Name": student["name"],
            "Email": student["email"],
            "Program": student["program"],
            "Semester": student["semester"],
            "Weighted Score": score["weighted_score"] if score else "",
            "Category": score["category"] if score else "No data",
        })

    filename = f"summary_report_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return _csv_response(rows, ["Name", "Email", "Program", "Semester", "Weighted Score", "Category"], filename)


@router.get("/full.csv")
async def export_full_csv(current_user: dict = Depends(require_role("admin", "teacher"))):
    """
    One row per performance record: raw inputs plus the calculated score.
    """
    students = await _get_visible_students(current_user)
    student_ids = [str(s["_id"]) for s in students]
    students_by_id = {str(s["_id"]): s for s in students}

    records = await performance_records_collection.find(
        {"student_id": {"$in": student_ids}}
    ).to_list(length=None)

    scores = await performance_scores_collection.find(
        {"student_id": {"$in": student_ids}}
    ).to_list(length=None)
    score_by_record_id = {s["record_id"]: s for s in scores}

    rows = []
    for r in records:
        student = students_by_id.get(r["student_id"])
        score = score_by_record_id.get(str(r["_id"]))
        rows.append({
            "Student Name": student["name"] if student else "Unknown",
            "Student Email": student["email"] if student else "",
            "Semester": r["semester"],
            "Attendance %": r["attendance_percent"],
            "Assignment Score": r["assignment_score"],
            "Exam Score": r["exam_score"],
            "Weighted Score": score["weighted_score"] if score else "",
            "Category": score["category"] if score else "Pending",
            "Date Recorded": r["date_recorded"].strftime("%Y-%m-%d") if hasattr(r["date_recorded"], "strftime") else r["date_recorded"],
        })

    filename = f"full_report_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return _csv_response(
        rows,
        ["Student Name", "Student Email", "Semester", "Attendance %", "Assignment Score", "Exam Score", "Weighted Score", "Category", "Date Recorded"],
        filename,
    )