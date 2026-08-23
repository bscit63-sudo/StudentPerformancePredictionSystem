from pydantic import BaseModel, Field
from app.models.performance_score import ApprovalStatus


class ReviewDecision(BaseModel):
    decision: ApprovalStatus = Field(..., description="Must be 'approved' or 'rejected'")
    apply_grace_recalculation: bool = False