from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class TeacherBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    department: str = Field(..., max_length=100)


class TeacherCreate(TeacherBase):
    password: str = Field(..., min_length=8)


class TeacherInDB(TeacherBase):
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TeacherOut(TeacherBase):
    id: str
    created_at: datetime


class TeacherUpdate(BaseModel):
    """All fields optional - only send what you want to change."""
    name: str | None = None
    email: EmailStr | None = None
    department: str | None = None