from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.database import departments_collection, teachers_collection
from app.models.department import DepartmentCreate, DepartmentOut, DepartmentUpdate
from app.models.utils import serialize_document, serialize_documents
from app.security import require_role

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("/", response_model=DepartmentOut)
async def create_department(
    department: DepartmentCreate,
    current_user: dict = Depends(require_role("admin")),
):
    existing = await departments_collection.find_one({"department_name": department.department_name})
    if existing:
        raise HTTPException(status_code=400, detail="This department already exists")

    doc = {
        "department_name": department.department_name,
        "created_at": datetime.utcnow(),
    }
    result = await departments_collection.insert_one(doc)
    created = await departments_collection.find_one({"_id": result.inserted_id})
    return serialize_document(created)


@router.get("/", response_model=list[DepartmentOut])
async def list_departments(current_user: dict = Depends(require_role("admin", "teacher"))):
    departments = await departments_collection.find().to_list(length=None)
    return serialize_documents(departments)


@router.put("/{department_id}", response_model=DepartmentOut)
async def update_department(
    department_id: str,
    update: DepartmentUpdate,
    current_user: dict = Depends(require_role("admin")),
):
    existing = await departments_collection.find_one({"_id": ObjectId(department_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Department not found")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await departments_collection.update_one({"_id": ObjectId(department_id)}, {"$set": update_data})

    updated = await departments_collection.find_one({"_id": ObjectId(department_id)})
    return serialize_document(updated)


@router.delete("/{department_id}")
async def delete_department(
    department_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    existing = await departments_collection.find_one({"_id": ObjectId(department_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Department not found")

    teachers_using = await teachers_collection.count_documents({"department": existing["department_name"]})
    if teachers_using > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {teachers_using} teacher(s) are assigned to this department.",
        )

    await departments_collection.delete_one({"_id": ObjectId(department_id)})
    return {"detail": "Department deleted successfully"}