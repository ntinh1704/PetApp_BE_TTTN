from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ServiceBase(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None


class ServiceUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None
