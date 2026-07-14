
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from app.database import teachers_collection, students_collection
from app.models.teacher import TeacherCreate, TeacherOut
from app.models.utils import serialize_document, serialize_documents
from app.security import hash_password, verify_password, create_access_token, require_role
from bson import ObjectId
from app.models.teacher import TeacherUpdate

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.post("/", response_model=TeacherOut)
async def create_teacher(
    teacher: TeacherCreate,
    current_user: dict = Depends(require_role("admin")),
):
    """Only an admin can create teacher accounts."""
    existing = await teachers_collection.find_one({"email": teacher.email})
    if existing:
        raise HTTPException(status_code=400, detail="A teacher with this email already exists")

    doc = {
        "name": teacher.name,
        "email": teacher.email,
        "department": teacher.department,
        "hashed_password": hash_password(teacher.password),
        "created_at": datetime.utcnow(),
    }
    result = await teachers_collection.insert_one(doc)
    created = await teachers_collection.find_one({"_id": result.inserted_id})
    return serialize_document(created)


@router.get("/", response_model=list[TeacherOut])
async def list_teachers(current_user: dict = Depends(require_role("admin"))):
    teachers = await teachers_collection.find().to_list(length=None)
    return serialize_documents(teachers)


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login_teacher(credentials: LoginRequest):
    teacher = await teachers_collection.find_one({"email": credentials.email})
    if not teacher or not verify_password(credentials.password, teacher["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(data={"sub": str(teacher["_id"]), "role": "teacher"})
    return {"access_token": token, "token_type": "bearer"}

from bson import ObjectId
from app.models.teacher import TeacherUpdate

@router.put("/{teacher_id}", response_model=TeacherOut)
async def update_teacher(
    teacher_id: str,
    update: TeacherUpdate,
    current_user: dict = Depends(require_role("admin")),
):
    existing = await teachers_collection.find_one({"_id": ObjectId(teacher_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Teacher not found")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await teachers_collection.update_one({"_id": ObjectId(teacher_id)}, {"$set": update_data})

    updated = await teachers_collection.find_one({"_id": ObjectId(teacher_id)})
    return serialize_document(updated)


@router.delete("/{teacher_id}")
async def delete_teacher(
    teacher_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    existing = await teachers_collection.find_one({"_id": ObjectId(teacher_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Teacher not found")

    students_assigned = await students_collection.count_documents({"teacher_id": teacher_id})
    if students_assigned > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {students_assigned} student(s) are still assigned to this teacher. Reassign them first.",
        )

    await teachers_collection.delete_one({"_id": ObjectId(teacher_id)})
    return {"detail": "Teacher deleted successfully"}

from app.models.auth_common import ChangePasswordRequest

@router.get("/me/profile", response_model=TeacherOut)
async def get_my_teacher_profile(current_user: dict = Depends(require_role("teacher"))):
    teacher = await teachers_collection.find_one({"_id": ObjectId(current_user["user_id"])})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return serialize_document(teacher)


@router.put("/me/profile", response_model=TeacherOut)
async def update_my_teacher_profile(
    update: dict,
    current_user: dict = Depends(require_role("teacher")),
):
    allowed = {k: v for k, v in update.items() if k in ("name", "email") and v}
    if allowed:
        await teachers_collection.update_one({"_id": ObjectId(current_user["user_id"])}, {"$set": allowed})
    teacher = await teachers_collection.find_one({"_id": ObjectId(current_user["user_id"])})
    return serialize_document(teacher)


@router.post("/change-password")
async def change_teacher_password(
    payload: ChangePasswordRequest,
    current_user: dict = Depends(require_role("teacher")),
):
    teacher = await teachers_collection.find_one({"_id": ObjectId(current_user["user_id"])})
    if not teacher or not verify_password(payload.current_password, teacher["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    await teachers_collection.update_one(
        {"_id": ObjectId(current_user["user_id"])},
        {"$set": {"hashed_password": hash_password(payload.new_password)}},
    )
    return {"detail": "Password updated successfully"}