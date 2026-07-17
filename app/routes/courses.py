from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.database import courses_collection, students_collection
from app.models.course import CourseCreate, CourseOut, CourseUpdate
from app.models.utils import serialize_document, serialize_documents
from app.security import require_role

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("/", response_model=CourseOut)
async def create_course(
    course: CourseCreate,
    current_user: dict = Depends(require_role("admin")),
):
    doc = course.model_dump()
    from datetime import datetime
    doc["created_at"] = datetime.utcnow()
    result = await courses_collection.insert_one(doc)
    created = await courses_collection.find_one({"_id": result.inserted_id})
    return serialize_document(created)


@router.get("/", response_model=list[CourseOut])
async def list_courses(current_user: dict = Depends(require_role("admin", "teacher"))):
    """Admins see all courses; teachers only see courses assigned to them."""
    if current_user["role"] == "teacher":
        courses = await courses_collection.find({"teacher_id": current_user["user_id"]}).to_list(length=None)
    else:
        courses = await courses_collection.find().to_list(length=None)
    return serialize_documents(courses)


@router.put("/{course_id}", response_model=CourseOut)
async def update_course(
    course_id: str,
    update: CourseUpdate,
    current_user: dict = Depends(require_role("admin")),
):
    existing = await courses_collection.find_one({"_id": ObjectId(course_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Course not found")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await courses_collection.update_one({"_id": ObjectId(course_id)}, {"$set": update_data})

    updated = await courses_collection.find_one({"_id": ObjectId(course_id)})
    return serialize_document(updated)


@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    existing = await courses_collection.find_one({"_id": ObjectId(course_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Course not found")

    students_enrolled = await students_collection.count_documents({"course_id": course_id})
    if students_enrolled > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {students_enrolled} student(s) are enrolled in this course.",
        )

    await courses_collection.delete_one({"_id": ObjectId(course_id)})
    return {"detail": "Course deleted successfully"}