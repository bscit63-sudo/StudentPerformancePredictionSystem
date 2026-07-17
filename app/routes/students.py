from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from pydantic import BaseModel

from app.database import students_collection, courses_collection
from app.models.student import StudentCreate, StudentOut, StudentUpdate
from app.models.utils import serialize_document, serialize_documents
from app.security import hash_password, verify_password, create_access_token, require_role
from app.models.auth_common import ChangePasswordRequest

router = APIRouter(prefix="/students", tags=["students"])


async def _attach_course_name(student_dict: dict) -> dict:
    """Looks up the course name for display, without changing what's stored."""
    course_id = student_dict.get("course_id")
    if course_id:
        course = await courses_collection.find_one({"_id": ObjectId(course_id)})
        student_dict["course_name"] = course["course_name"] if course else None
    else:
        student_dict["course_name"] = None
    return student_dict


async def _attach_course_names(student_dicts: list[dict]) -> list[dict]:
    return [await _attach_course_name(s) for s in student_dicts]


@router.post("/", response_model=StudentOut)
async def create_student(
    student: StudentCreate,
    current_user: dict = Depends(require_role("admin", "teacher")),
):
    existing = await students_collection.find_one({"email": student.email})
    if existing:
        raise HTTPException(status_code=400, detail="A student with this email already exists")

    doc = {
        "name": student.name,
        "email": student.email,
        "semester": student.semester,
        "teacher_id": student.teacher_id,
        "phone_number": student.phone_number,
        "course_id": student.course_id,
        "program": student.program,
        "hashed_password": hash_password(student.password),
        "created_at": datetime.utcnow(),
    }
    result = await students_collection.insert_one(doc)
    created = await students_collection.find_one({"_id": result.inserted_id})
    return await _attach_course_name(serialize_document(created))


@router.get("/me/profile", response_model=StudentOut)
async def get_my_profile(current_user: dict = Depends(require_role("student"))):
    student = await students_collection.find_one({"_id": ObjectId(current_user["user_id"])})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return await _attach_course_name(serialize_document(student))


@router.get("/", response_model=list[StudentOut])
async def list_students(current_user: dict = Depends(require_role("admin", "teacher"))):
    """
    Admins see ALL students.
    Teachers only see students where teacher_id matches their own user_id.
    """
    if current_user["role"] == "teacher":
        students = await students_collection.find(
            {"teacher_id": current_user["user_id"]}
        ).to_list(length=None)
    else:
        students = await students_collection.find().to_list(length=None)
    return await _attach_course_names(serialize_documents(students))


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(
    student_id: str,
    current_user: dict = Depends(require_role("admin", "teacher", "student")),
):
    if current_user["role"] == "student" and current_user["user_id"] != student_id:
        raise HTTPException(status_code=403, detail="You can only view your own profile")

    student = await students_collection.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return await _attach_course_name(serialize_document(student))


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login_student(credentials: LoginRequest):
    student = await students_collection.find_one({"email": credentials.email})
    if not student or not verify_password(credentials.password, student["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(data={"sub": str(student["_id"]), "role": "student"})
    return {"access_token": token, "token_type": "bearer"}


@router.put("/{student_id}", response_model=StudentOut)
async def update_student(
    student_id: str,
    update: StudentUpdate,
    current_user: dict = Depends(require_role("admin", "teacher")),
):
    existing = await students_collection.find_one({"_id": ObjectId(student_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Student not found")

    if current_user["role"] == "teacher" and existing.get("teacher_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only edit your own students")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await students_collection.update_one({"_id": ObjectId(student_id)}, {"$set": update_data})

    updated = await students_collection.find_one({"_id": ObjectId(student_id)})
    return await _attach_course_name(serialize_document(updated))


@router.delete("/{student_id}")
async def delete_student(
    student_id: str,
    current_user: dict = Depends(require_role("admin", "teacher")),
):
    existing = await students_collection.find_one({"_id": ObjectId(student_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Student not found")

    if current_user["role"] == "teacher" and existing.get("teacher_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own students")

    await students_collection.delete_one({"_id": ObjectId(student_id)})
    return {"detail": "Student deleted successfully"}


@router.put("/me/profile", response_model=StudentOut)
async def update_my_student_profile(
    update: dict,
    current_user: dict = Depends(require_role("student")),
):
    allowed = {k: v for k, v in update.items() if k in ("name", "email", "phone_number") and v is not None}
    if allowed:
        await students_collection.update_one({"_id": ObjectId(current_user["user_id"])}, {"$set": allowed})
    student = await students_collection.find_one({"_id": ObjectId(current_user["user_id"])})
    return await _attach_course_name(serialize_document(student))


@router.post("/change-password")
async def change_student_password(
    payload: ChangePasswordRequest,
    current_user: dict = Depends(require_role("student")),
):
    student = await students_collection.find_one({"_id": ObjectId(current_user["user_id"])})
    if not student or not verify_password(payload.current_password, student["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    await students_collection.update_one(
        {"_id": ObjectId(current_user["user_id"])},
        {"$set": {"hashed_password": hash_password(payload.new_password)}},
    )
    return {"detail": "Password updated successfully"}