from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    # id: int
    username: str
    password: str
    role: Optional[str] = "user"


class UserCreate(UserBase):
    username: str
    password: str
    role: Optional[str] = "user"


class UserUpdate(BaseModel):
    id: int
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    username: str = "admin"
    password: str = "admin"


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    # token_type: str = "bearer"
