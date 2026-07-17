from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class StudentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    semester: int = Field(..., ge=1, le=10)
    teacher_id: str
    phone_number: str | None = None
    course_id: str | None = None
    program: str | None = None  # legacy free-text field, kept so old records don't break


class StudentCreate(StudentBase):
    password: str = Field(..., min_length=8)


class StudentInDB(StudentBase):
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StudentOut(StudentBase):
    id: str
    created_at: datetime
    course_name: str | None = None  # filled in by the route, not stored directly


class StudentUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    semester: int | None = Field(None, ge=1, le=10)
    teacher_id: str | None = None
    phone_number: str | None = None
    course_id: str | None = None