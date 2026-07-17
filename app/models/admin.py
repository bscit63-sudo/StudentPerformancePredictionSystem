from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class AdminBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    phone_number: str | None = None


class AdminCreate(AdminBase):
    """Used when registering a new admin - plain password, hashed before saving."""
    password: str = Field(..., min_length=8)


class AdminInDB(AdminBase):
    """Shape of the document actually stored in MongoDB."""
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AdminOut(AdminBase):
    """Safe shape to return in API responses - never includes the password."""
    id: str
    created_at: datetime