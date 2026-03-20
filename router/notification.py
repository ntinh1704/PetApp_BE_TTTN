from fastapi import APIRouter, Depends

from controller import notification
from schemas.notification_schema import NotificationBase, NotificationCreate, NotificationUpdate
from setting.utils import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def get_list_notification(
    data=Depends(notification.get_list_notification),
    # _current_user=Depends(get_current_user),
):
    return data


@router.get("/{notification_id}", response_model=NotificationBase)
def get_notification_by_id(
    notification_id: int,
    _current_user=Depends(get_current_user),
):
    return notification.get_notification_by_id(notification_id, _current_user)


@router.post("/", response_model=NotificationBase)
def create_notification(
    data: NotificationCreate,
    _current_user=Depends(get_current_user),
):
    return notification.create_notification(data, _current_user)


@router.put("/", response_model=NotificationBase)
def update_notification(
    data: NotificationUpdate,
    _current_user=Depends(get_current_user),
):
    return notification.update_notification(data, _current_user)


@router.delete("/")
def delete_notification(
    notification_id: int,
    _current_user=Depends(get_current_user),
):
    return notification.delete_notification(notification_id, _current_user)