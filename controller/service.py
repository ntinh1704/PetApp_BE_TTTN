from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from crud import service_crud
from db.database import get_db
from schemas.service_schema import ServiceCreate, ServiceUpdate
from setting.utils import (
    get_offset_limit,
    get_pages_records,
    get_current_user,
)


def create_service(data: ServiceCreate, current_user=Depends(get_current_user)):
    db_api = service_crud.ServiceDatabaseApi(current_user)
    return db_api.create_service(data)


def get_list_service(
    text_search: str = None,
    current_user=Depends(get_current_user),
    offset_limit=Depends(get_offset_limit),
):
    db_api = service_crud.ServiceDatabaseApi(current_user)
    offset, limit = offset_limit
    data, total = db_api.get_list_service(offset, limit, text_search)
    return get_pages_records((data, total), offset_limit)


def get_service_by_id(service_id: int, current_user=Depends(get_current_user)):
    db_api = service_crud.ServiceDatabaseApi(current_user)
    service = db_api.get_service_by_id(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


def update_service(data: ServiceUpdate, current_user=Depends(get_current_user)):
    db_api = service_crud.ServiceDatabaseApi(current_user)
    updated = db_api.update_service(data)
    if not updated:
        raise HTTPException(status_code=404, detail="Service not found")
    return updated


def delete_service(service_id: int, current_user=Depends(get_current_user)):
    db_api = service_crud.ServiceDatabaseApi(current_user)
    deleted = db_api.delete_service(service_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"detail": "Service deleted successfully"}
