from fastapi import APIRouter, HTTPException, Depends

from app.database import performance_scores_collection, students_collection
from app.models.performance_score import PerformanceScoreOut
from app.models.utils import serialize_documents
from app.security import require_role

router = APIRouter(prefix="/scores", tags=["performance-scores"])

@router.get("/me", response_model=list[PerformanceScoreOut])
async def get_my_scores(current_user: dict = Depends(require_role("student"))):
    """A logged-in student fetches their own scores."""
    scores = await performance_scores_collection.find(
        {"student_id": current_user["user_id"]}
    ).to_list(length=None)
    return serialize_documents(scores)

@router.get("/", response_model=list[PerformanceScoreOut])
async def list_scores(current_user: dict = Depends(require_role("admin", "teacher"))):
    if current_user["role"] == "teacher":
        my_students = await students_collection.find(
            {"teacher_id": current_user["user_id"]}
        ).to_list(length=None)
        my_student_ids = [str(s["_id"]) for s in my_students]
        scores = await performance_scores_collection.find(
            {"student_id": {"$in": my_student_ids}}
        ).to_list(length=None)
    else:
        scores = await performance_scores_collection.find().to_list(length=None)
    return serialize_documents(scores)


@router.get("/student/{student_id}", response_model=list[PerformanceScoreOut])
async def get_scores_for_student(
    student_id: str,
    current_user: dict = Depends(require_role("admin", "teacher", "student")),
):
    if current_user["role"] == "student" and current_user["user_id"] != student_id:
        raise HTTPException(status_code=403, detail="You can only view your own scores")

    scores = await performance_scores_collection.find({"student_id": student_id}).to_list(length=None)
    return serialize_documents(scores)