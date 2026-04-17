from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from .service_schema import ServiceBase

class CartItemBase(BaseModel):
    service_id: int
    quantity: int

class CartItemUpdate(BaseModel):
    service_id: int
    quantity: int

class CartItemResponse(BaseModel):
    id: int
    service: ServiceBase
    quantity: int
    created_at: datetime

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    created_at: datetime

    class Config:
        from_attributes = True
