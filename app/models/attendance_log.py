from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"


class AttendanceEntry(BaseModel):
    """One student's status for the date being marked."""
    student_id: str
    status: AttendanceStatus


class AttendanceBulkMarkRequest(BaseModel):
    """A teacher marks their whole class for one date in a single request."""
    date: date
    entries: list[AttendanceEntry]


class AttendanceLogOut(BaseModel):
    id: str
    student_id: str
    date: str
    status: AttendanceStatus
    marked_by: str
    created_at: datetime


class AttendancePercentageOut(BaseModel):
    student_id: str
    total_days_marked: int
    days_present: int
    attendance_percent: float