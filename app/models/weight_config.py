from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class WeightConfigBase(BaseModel):
    attendance_weight: float = Field(..., ge=0, le=1)
    assignment_weight: float = Field(..., ge=0, le=1)
    exam_weight: float = Field(..., ge=0, le=1)

    @model_validator(mode="after")
    def weights_must_sum_to_one(self):
        total = self.attendance_weight + self.assignment_weight + self.exam_weight
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0 (got {total})")
        return self


class WeightConfigCreate(WeightConfigBase):
    admin_id: str


class WeightConfigInDB(WeightConfigBase):
    admin_id: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class WeightConfigOut(WeightConfigBase):
    id: str
    admin_id: str
    last_updated: datetime