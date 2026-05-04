from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from crud import staff_crud
from db.database import get_db
from schemas.staff_schema import StaffCreate, StaffUpdate
from setting.utils import (
    get_offset_limit,
    get_pages_records,
    get_current_user,
)


def get_list_staff(
    text_search: str = None,
    all: bool = Query(False, description="Return all staff without pagination"),
    current_user=Depends(get_current_user),
    offset_limit=Depends(get_offset_limit),
):
    db_api = staff_crud.StaffDatabaseApi(current_user)

    if all:
        data, total = db_api.get_list_staff(offset=0, limit=None, text_search=text_search)
        return data

    offset, limit = offset_limit
    data, total = db_api.get_list_staff(offset, limit, text_search)
    return get_pages_records((data, total), offset_limit)


def get_active_staff(current_user=Depends(get_current_user)):
    db_api = staff_crud.StaffDatabaseApi(current_user)
    return db_api.get_active_staff()


def get_staff_by_id(staff_id: int, current_user=Depends(get_current_user)):
    db_api = staff_crud.StaffDatabaseApi(current_user)
    staff = db_api.get_staff_by_id(staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff


def create_staff(data: StaffCreate, current_user=Depends(get_current_user)):
    db_api = staff_crud.StaffDatabaseApi(current_user)
    return db_api.create_staff(data)


def update_staff(data: StaffUpdate, current_user=Depends(get_current_user)):
    db_api = staff_crud.StaffDatabaseApi(current_user)
    updated = db_api.update_staff(data)
    if not updated:
        raise HTTPException(status_code=404, detail="Staff not found")
    return updated


def delete_staff(staff_id: int, current_user=Depends(get_current_user)):
    db_api = staff_crud.StaffDatabaseApi(current_user)
    deleted = db_api.delete_staff(staff_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Staff not found")
    return {"detail": "Staff deactivated successfully"}
