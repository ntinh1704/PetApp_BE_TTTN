from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from crud import booking_crud
from db.database import get_db
from schemas.booking_schema import BookingCreate, BookingUpdate
from setting.utils import (
    get_offset_limit,
    get_pages_records,
    get_current_user,
)


def create_booking(data: BookingCreate, current_user=Depends(get_current_user)):
    db_api = booking_crud.BookingDatabaseApi(current_user)
    return db_api.create_booking(data)


def get_list_booking(
    text_search: str = None,
    current_user=Depends(get_current_user),
    offset_limit=Depends(get_offset_limit),
):
    db_api = booking_crud.BookingDatabaseApi(current_user)
    offset, limit = offset_limit
    data, total = db_api.get_list_booking(offset, limit, text_search)
    return get_pages_records((data, total), offset_limit)


def get_booking_by_id(booking_id: int, current_user=Depends(get_current_user)):
    db_api = booking_crud.BookingDatabaseApi(current_user)
    booking = db_api.get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


def update_booking(data: BookingUpdate, current_user=Depends(get_current_user)):
    db_api = booking_crud.BookingDatabaseApi(current_user)
    updated = db_api.update_booking(data)
    if not updated:
        raise HTTPException(status_code=404, detail="Booking not found")
    return updated


def delete_booking(booking_id: int, current_user=Depends(get_current_user)):
    db_api = booking_crud.BookingDatabaseApi(current_user)
    deleted = db_api.delete_booking(booking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"detail": "Booking deleted successfully"}
