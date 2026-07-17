from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from app.database import admins_collection
from app.models.admin import AdminCreate, AdminOut
from app.models.utils import serialize_document
from app.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/admin/register", response_model=AdminOut)
async def register_admin(admin: AdminCreate):
    existing = await admins_collection.find_one({"email": admin.email})
    if existing:
        raise HTTPException(status_code=400, detail="An admin with this email already exists")

    from datetime import datetime

    doc = {
        "username": admin.username,
        "email": admin.email,
        "hashed_password": hash_password(admin.password),
        "created_at": datetime.utcnow(),
    }
    result = await admins_collection.insert_one(doc)
    created = await admins_collection.find_one({"_id": result.inserted_id})
    return serialize_document(created)


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/admin/login")
async def login_admin(credentials: LoginRequest):
    admin = await admins_collection.find_one({"email": credentials.email})
    if not admin or not verify_password(credentials.password, admin["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(data={"sub": str(admin["_id"]), "role": "admin"})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user

from app.models.auth_common import ChangePasswordRequest

@router.get("/admin/me/profile", response_model=AdminOut)
async def get_my_admin_profile(current_user: dict = Depends(get_current_user)):
    admin = await admins_collection.find_one({"_id": ObjectId(current_user["user_id"])})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return serialize_document(admin)


@router.put("/admin/me/profile", response_model=AdminOut)
async def update_my_admin_profile(
    update: dict,
    current_user: dict = Depends(get_current_user),
):
    allowed = {k: v for k, v in update.items() if k in ("username", "email", "phone_number") and v is not None}
    if allowed:
        await admins_collection.update_one({"_id": ObjectId(current_user["user_id"])}, {"$set": allowed})
    admin = await admins_collection.find_one({"_id": ObjectId(current_user["user_id"])})
    return serialize_document(admin)


@router.post("/admin/change-password")
async def change_admin_password(
    payload: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    admin = await admins_collection.find_one({"_id": ObjectId(current_user["user_id"])})
    if not admin or not verify_password(payload.current_password, admin["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    await admins_collection.update_one(
        {"_id": ObjectId(current_user["user_id"])},
        {"$set": {"hashed_password": hash_password(payload.new_password)}},
    )
    return {"detail": "Password updated successfully"}