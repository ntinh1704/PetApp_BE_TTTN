from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationBase(BaseModel):
    id: int
    user_id: int
    title: Optional[str] = None
    message: Optional[str] = None
    is_read: Optional[bool] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    user_id: int
    title: Optional[str] = None
    message: Optional[str] = None
    is_read: Optional[bool] = False


class NotificationUpdate(BaseModel):
    id: int
    title: Optional[str] = None
    message: Optional[str] = None
    is_read: Optional[bool] = None
