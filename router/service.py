from fastapi import APIRouter, Depends

from controller import service
from schemas.service_schema import ServiceBase, ServiceCreate, ServiceUpdate
from setting.utils import get_current_user

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("")
def get_list_service(
    data=Depends(service.get_list_service),
    # _current_user=Depends(get_current_user),
):
    return data


@router.get("/{service_id}", response_model=ServiceBase)
def get_service_by_id(
    service_id: int,
    _current_user=Depends(get_current_user),
):
    return service.get_service_by_id(service_id, _current_user)


@router.post("/", response_model=ServiceBase)
def create_service(
    data: ServiceCreate,
    _current_user=Depends(get_current_user),
):
    return service.create_service(data, _current_user)


@router.put("/", response_model=ServiceBase)
def update_service(
    data: ServiceUpdate,
    _current_user=Depends(get_current_user),
):
    return service.update_service(data, _current_user)


@router.delete("/")
def delete_service(
    service_id: int,
    _current_user=Depends(get_current_user),
):
    return service.delete_service(service_id, _current_user)