from datetime import datetime
from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    department_name: str = Field(..., min_length=2, max_length=100)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentInDB(DepartmentBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DepartmentOut(DepartmentBase):
    id: str
    created_at: datetime


class DepartmentUpdate(BaseModel):
    department_name: str | None = None