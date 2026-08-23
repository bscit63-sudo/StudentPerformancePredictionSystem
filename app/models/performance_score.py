from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class PerformanceCategory(str, Enum):
    TOP_PERFORMER = "Top Performer"
    AVERAGE_PERFORMER = "Average Performer"
    AT_RISK = "At-Risk"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PerformanceScoreBase(BaseModel):
    student_id: str
    record_id: str
    config_id: str
    weighted_score: float = Field(..., ge=0, le=100)
    category: PerformanceCategory
    is_flagged: bool = False
    flag_reason: str | None = None
    evidence_file_path: str | None = None
    approval_status: ApprovalStatus | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None


class PerformanceScoreCreate(PerformanceScoreBase):
    pass


class PerformanceScoreInDB(PerformanceScoreBase):
    calculated_date: datetime = Field(default_factory=datetime.utcnow)


class PerformanceScoreOut(PerformanceScoreBase):
    id: str
    calculated_date: datetime