from datetime import date, datetime, time
from typing import Optional, List

from pydantic import BaseModel


class BookingBase(BaseModel):
    id: int
    user_id: int
    pet_id: int
    booking_date: Optional[date] = None
    booking_time: Optional[time] = None
    status: Optional[str] = None
    note: Optional[str] = None
    total_price: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BookingCreate(BaseModel):
    user_id: int
    pet_id: int
    service_ids: List[int]
    booking_date: Optional[date] = None
    booking_time: Optional[time] = None
    status: Optional[str] = None
    note: Optional[str] = None
    total_price: Optional[float] = None


class BookingUpdate(BaseModel):
    id: int
    service_ids: Optional[List[int]] = None
    booking_date: Optional[date] = None
    booking_time: Optional[time] = None
    status: Optional[str] = None
    note: Optional[str] = None
    total_price: Optional[float] = None
