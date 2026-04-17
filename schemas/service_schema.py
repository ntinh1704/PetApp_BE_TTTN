from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


class ServiceBase(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None
    images: Optional[List[str]] = None
    created_at: Optional[datetime] = None

    @field_validator("images", mode="before")
    @classmethod
    def transform_images(cls, value):
        if isinstance(value, list) and len(value) > 0 and not isinstance(value[0], str):
            return [getattr(item, "image_url", item) for item in value]
        return value

    class Config:
        from_attributes = True


class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None
    images: Optional[List[str]] = None


class ServiceUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None
    images: Optional[List[str]] = None
