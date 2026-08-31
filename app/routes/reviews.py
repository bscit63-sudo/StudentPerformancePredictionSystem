import os
import uuid
from datetime import datetime
from fastapi.responses import FileResponse

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.database import performance_scores_collection, students_collection
from app.models.review import ReviewDecision
from app.security import require_role

router = APIRouter(prefix="/reviews", tags=["reviews"])

UPLOAD_DIR = "uploads/evidence"
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_MB = 5


@router.get("/flagged")
async def list_flagged_cases(current_user: dict = Depends(require_role("admin", "teacher"))):
    """
    Returns all pending flagged cases.
    Teachers only see cases for their own students; admins see all.
    """
    query = {"is_flagged": True, "approval_status": "pending"}

    if current_user["role"] == "teacher":
        my_students = await students_collection.find(
            {"teacher_id": current_user["user_id"]}
        ).to_list(length=None)
        my_student_ids = [str(s["_id"]) for s in my_students]
        query["student_id"] = {"$in": my_student_ids}

    cases = await performance_scores_collection.find(query).to_list(length=None)
    for case in cases:
        case["id"] = str(case.pop("_id"))
        student = await students_collection.find_one({"_id": ObjectId(case["student_id"])})
        case["student_name"] = student["name"] if student else "Unknown"

    return cases


@router.post("/{score_id}/evidence")
async def upload_evidence(
    score_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role("admin", "teacher", "student")),
):
    score = await performance_scores_collection.find_one({"_id": ObjectId(score_id)})
    if not score:
        raise HTTPException(status_code=404, detail="Performance score not found")

    if current_user["role"] == "student" and current_user["user_id"] != score["student_id"]:
        raise HTTPException(status_code=403, detail="You can only upload evidence for your own record")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF, JPG, or PNG files are allowed")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File must be under {MAX_FILE_SIZE_MB}MB")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_filename = f"{score_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    await performance_scores_collection.update_one(
        {"_id": ObjectId(score_id)},
        {"$set": {"evidence_file_path": file_path}},
    )

    return {"detail": "Evidence uploaded successfully", "file_path": file_path}

@router.get("/{score_id}/evidence")
async def get_evidence(
    score_id: str,
    current_user: dict = Depends(require_role("admin", "teacher", "student")),
):
    score = await performance_scores_collection.find_one({"_id": ObjectId(score_id)})
    if not score:
        raise HTTPException(status_code=404, detail="Performance score not found")

    if current_user["role"] == "student" and current_user["user_id"] != score["student_id"]:
        raise HTTPException(status_code=403, detail="You can only view evidence for your own record")

    if current_user["role"] == "teacher":
        student = await students_collection.find_one({"_id": ObjectId(score["student_id"])})
        if not student or student.get("teacher_id") != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="You can only view evidence for your own students")

    file_path = score.get("evidence_file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="No evidence file found for this case")

    return FileResponse(file_path)
@router.post("/{score_id}/decision")
async def review_flagged_case(
    score_id: str,
    payload: ReviewDecision,
    current_user: dict = Depends(require_role("teacher", "admin")),
):
    score = await performance_scores_collection.find_one({"_id": ObjectId(score_id)})
    if not score:
        raise HTTPException(status_code=404, detail="Performance score not found")

    if current_user["role"] == "teacher":
        student = await students_collection.find_one({"_id": ObjectId(score["student_id"])})
        if not student or student.get("teacher_id") != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="You can only review your own students' cases")

    update_data = {
        "approval_status": payload.decision.value,
        "approved_by": current_user["user_id"],
        "approved_at": datetime.utcnow(),
    }

    if payload.decision.value == "approved" and payload.apply_grace_recalculation:
        from app.database import performance_records_collection, weight_configs_collection
        record = await performance_records_collection.find_one({"_id": ObjectId(score["record_id"])})
        if record:
            peer_records = await performance_records_collection.find(
                {"semester": record["semester"], "student_id": {"$ne": score["student_id"]}}
            ).to_list(length=None)
            if peer_records:
                exam_scores = sorted(r["exam_score"] for r in peer_records)
                mid = len(exam_scores) // 2
                class_median = (
                    exam_scores[mid] if len(exam_scores) % 2 == 1
                    else (exam_scores[mid - 1] + exam_scores[mid]) / 2
                )

                config = await weight_configs_collection.find_one(sort=[("last_updated", -1)])
                if config:
                    from app.scoring import calculate_weighted_score, classify_score
                    new_weighted_score = calculate_weighted_score(
                        attendance_percent=record["attendance_percent"],
                        assignment_score=record["assignment_score"],
                        exam_score=class_median,
                        attendance_weight=config["attendance_weight"],
                        assignment_weight=config["assignment_weight"],
                        exam_weight=config["exam_weight"],
                    )
                    new_category = classify_score(new_weighted_score)
                    update_data["weighted_score"] = new_weighted_score
                    update_data["category"] = new_category.value
                    update_data["flag_reason"] = (score.get("flag_reason") or "") + \
                        f" [Grace recalculation applied: exam substituted with class median {class_median:.1f}]"

    await performance_scores_collection.update_one({"_id": ObjectId(score_id)}, {"$set": update_data})
    updated = await performance_scores_collection.find_one({"_id": ObjectId(score_id)})
    updated["id"] = str(updated.pop("_id"))
    return updated
