from datetime import datetime
from pydantic import BaseModel, Field


class PerformanceRecordBase(BaseModel):
    student_id: str
    attendance_percent: float = Field(..., ge=0, le=100)
    assignment_score: float = Field(..., ge=0, le=100)
    exam_score: float = Field(..., ge=0, le=100)
    semester: str = Field(..., max_length=20)


class PerformanceRecordCreate(PerformanceRecordBase):
    pass


class PerformanceRecordInDB(PerformanceRecordBase):
    date_recorded: datetime = Field(default_factory=datetime.utcnow)


class PerformanceRecordOut(PerformanceRecordBase):
    id: str
    date_recorded: datetime


class PerformanceRecordUpdate(BaseModel):
    attendance_percent: float | None = Field(None, ge=0, le=100)
    assignment_score: float | None = Field(None, ge=0, le=100)
    exam_score: float | None = Field(None, ge=0, le=100)