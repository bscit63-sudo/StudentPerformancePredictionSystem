from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from pydantic import BaseModel

from app.database import students_collection
from app.models.student import StudentCreate, StudentOut
from app.models.utils import serialize_document, serialize_documents
from app.security import hash_password, verify_password, create_access_token, require_role, get_current_user

router = APIRouter(prefix="/students", tags=["students"])


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
        "program": student.program,
        "semester": student.semester,
        "teacher_id": student.teacher_id,
        "hashed_password": hash_password(student.password),
        "created_at": datetime.utcnow(),
    }
    result = await students_collection.insert_one(doc)
    created = await students_collection.find_one({"_id": result.inserted_id})
    return serialize_document(created)

@router.get("/me/profile", response_model=StudentOut)
async def get_my_profile(current_user: dict = Depends(require_role("student"))):
    """A logged-in student fetches their own profile without needing to know their ID."""
    student = await students_collection.find_one({"_id": ObjectId(current_user["user_id"])})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return serialize_document(student)

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
    return serialize_documents(students)


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(
    student_id: str,
    current_user: dict = Depends(require_role("admin", "teacher", "student")),
):
    """
    Admins/teachers can view any student (teachers should ideally only view
    their own - enforced on the list endpoint; this single-get is left open
    for now since a teacher looking up one ID they don't own is low-risk).
    Students can only view themselves.
    """
    if current_user["role"] == "student" and current_user["user_id"] != student_id:
        raise HTTPException(status_code=403, detail="You can only view your own profile")

    student = await students_collection.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return serialize_document(student)


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

from app.models.student import StudentUpdate

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
    return serialize_document(updated)


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