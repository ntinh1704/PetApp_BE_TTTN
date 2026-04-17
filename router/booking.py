from fastapi import APIRouter, Depends

from controller import booking
from schemas.booking_schema import BookingBase, BookingCreate, BookingUpdate
from setting.utils import get_current_user

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("")
def get_list_booking(
    data=Depends(booking.get_list_booking),
    # _current_user=Depends(get_current_user),
):
    return data


@router.get("/{booking_id}")
def get_booking_by_id(
    booking_id: int,
    _current_user=Depends(get_current_user),
):
    return booking.get_booking_by_id(booking_id, _current_user)


@router.post("/", response_model=BookingBase)
def create_booking(
    data: BookingCreate,
    _current_user=Depends(get_current_user),
):
    return booking.create_booking(data, _current_user)


@router.put("/", response_model=BookingBase)
def update_booking(
    data: BookingUpdate,
    _current_user=Depends(get_current_user),
):
    return booking.update_booking(data, _current_user)


@router.delete("/")
def delete_booking(
    booking_id: int,
    _current_user=Depends(get_current_user),
):
    return booking.delete_booking(booking_id, _current_user)
