from pydantic import BaseModel, Field


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class ProfileUpdateRequest(BaseModel):
    """Self-service profile edit - only name/email, not role-managed fields
    like program, semester, or teacher assignment."""
    name: str | None = Field(None, min_length=2, max_length=100)
    email: str | None = None