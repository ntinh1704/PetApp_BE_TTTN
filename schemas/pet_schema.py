from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PetBase(BaseModel):
    id: int
    user_id: int
    name: str
    breed: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    color: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    image: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PetCreate(BaseModel):
    user_id: int
    name: str
    breed: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    color: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    image: Optional[str] = None


class PetUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    breed: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    color: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    image: Optional[str] = None
