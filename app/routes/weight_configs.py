from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends

from app.database import weight_configs_collection
from app.models.weight_config import WeightConfigCreate, WeightConfigOut
from app.models.utils import serialize_document, serialize_documents
from app.security import require_role

router = APIRouter(prefix="/weight-configs", tags=["weight-configs"])


@router.post("/", response_model=WeightConfigOut)
async def create_weight_config(
    config: WeightConfigCreate,
    current_user: dict = Depends(require_role("admin")),
):
    doc = {
        "attendance_weight": config.attendance_weight,
        "assignment_weight": config.assignment_weight,
        "exam_weight": config.exam_weight,
        "admin_id": config.admin_id,
        "last_updated": datetime.utcnow(),
    }
    result = await weight_configs_collection.insert_one(doc)
    created = await weight_configs_collection.find_one({"_id": result.inserted_id})
    return serialize_document(created)


@router.get("/", response_model=list[WeightConfigOut])
async def list_weight_configs(current_user: dict = Depends(require_role("admin", "teacher"))):
    configs = await weight_configs_collection.find().to_list(length=None)
    return serialize_documents(configs)


@router.get("/latest", response_model=WeightConfigOut)
async def get_latest_weight_config(current_user: dict = Depends(require_role("admin", "teacher"))):
    latest = await weight_configs_collection.find_one(sort=[("last_updated", -1)])
    if not latest:
        raise HTTPException(status_code=404, detail="No weight configuration has been set yet")
    return serialize_document(latest)