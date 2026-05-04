from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StaffBase(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    specialty: Optional[str] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StaffCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    specialty: Optional[str] = None


class StaffUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    specialty: Optional[str] = None
    is_active: Optional[bool] = None
