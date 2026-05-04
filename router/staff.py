from fastapi import APIRouter, Depends

from controller import staff
from schemas.staff_schema import StaffBase, StaffCreate, StaffUpdate
from setting.utils import get_current_user

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.get("")
def get_list_staff(
    data=Depends(staff.get_list_staff),
):
    return data


@router.get("/active")
def get_active_staff(
    _current_user=Depends(get_current_user),
):
    return staff.get_active_staff(_current_user)


@router.get("/{staff_id}")
def get_staff_by_id(
    staff_id: int,
    _current_user=Depends(get_current_user),
):
    return staff.get_staff_by_id(staff_id, _current_user)


@router.post("/", response_model=StaffBase)
def create_staff(
    data: StaffCreate,
    _current_user=Depends(get_current_user),
):
    return staff.create_staff(data, _current_user)


@router.put("/", response_model=StaffBase)
def update_staff(
    data: StaffUpdate,
    _current_user=Depends(get_current_user),
):
    return staff.update_staff(data, _current_user)


@router.delete("/")
def delete_staff(
    staff_id: int,
    _current_user=Depends(get_current_user),
):
    return staff.delete_staff(staff_id, _current_user)
