from datetime import datetime
from pydantic import BaseModel, Field


class CourseBase(BaseModel):
    course_name: str = Field(..., min_length=2, max_length=100)
    course_code: str | None = None
    teacher_id: str | None = None  # the teacher assigned to teach this course


class CourseCreate(CourseBase):
    pass


class CourseInDB(CourseBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CourseOut(CourseBase):
    id: str
    created_at: datetime


class CourseUpdate(BaseModel):
    course_name: str | None = None
    course_code: str | None = None
    teacher_id: str | None = None