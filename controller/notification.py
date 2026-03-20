from fastapi import Depends, HTTPException

from crud import notification_crud
from schemas.notification_schema import NotificationCreate, NotificationUpdate
from setting.utils import (
    get_offset_limit,
    get_pages_records,
    get_current_user,
)


def create_notification(data: NotificationCreate, current_user=Depends(get_current_user)):
    db_api = notification_crud.NotificationDatabaseApi(current_user)
    return db_api.create_notification(data)


def get_list_notification(
    text_search: str = None,
    current_user=Depends(get_current_user),
    offset_limit=Depends(get_offset_limit),
):
    db_api = notification_crud.NotificationDatabaseApi(current_user)
    offset, limit = offset_limit
    data, total = db_api.get_list_notification(offset, limit, text_search)
    return get_pages_records((data, total), offset_limit)


def get_notification_by_id(notification_id: int, current_user=Depends(get_current_user)):
    db_api = notification_crud.NotificationDatabaseApi(current_user)
    notification = db_api.get_notification_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


def update_notification(data: NotificationUpdate, current_user=Depends(get_current_user)):
    db_api = notification_crud.NotificationDatabaseApi(current_user)
    updated = db_api.update_notification(data)
    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")
    return updated


def delete_notification(notification_id: int, current_user=Depends(get_current_user)):
    db_api = notification_crud.NotificationDatabaseApi(current_user)
    deleted = db_api.delete_notification(notification_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"detail": "Notification deleted successfully"}
