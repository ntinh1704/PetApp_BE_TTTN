from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    # id: int
    email: str
    password: str
    role: Optional[str] = "user"


class UserCreate(UserBase):
    name: Optional[str] = None
    email: str
    password: str
    role: Optional[str] = "user"


class UserUpdate(BaseModel):
    id: int
    email: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    phone: Optional[str] = None
    email: str
    address: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    email: str = "admin@gmail.com"
    password: str = "admin"


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    role: str


class GoogleLoginRequest(BaseModel):
    google_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class VerifyOTPRequest(BaseModel):
    email: str
    otp: str


class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str
