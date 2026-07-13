from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class StudentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    program: str = Field(..., max_length=100)
    semester: int = Field(..., ge=1, le=12)
    teacher_id: str  # references a Teacher document's _id


class StudentCreate(StudentBase):
    password: str = Field(..., min_length=8)


class StudentInDB(StudentBase):
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StudentOut(StudentBase):
    id: str
    created_at: datetime


class StudentUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    program: str | None = None
    semester: int | None = None
    teacher_id: str | None = None