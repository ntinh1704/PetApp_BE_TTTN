from sqlalchemy.orm import Session
from fastapi import HTTPException
from db import models
from schemas.notification_schema import NotificationCreate, NotificationUpdate


class NotificationDatabaseApi:
    def __init__(self, current_user):
        db, token_data, _ = current_user
        self.db: Session = db
        self.user = token_data

    def get_list_notification(self, offset: int = 0, limit: int = 10, text_search: str = None):
        current_uid = self.user.get("id") if isinstance(self.user, dict) else getattr(self.user, "id", None)
        current_role = self.user.get("role") if isinstance(self.user, dict) else getattr(self.user, "role", None)

        query = self.db.query(models.Notification)
        if current_role != "admin" and current_uid is not None:
            query = query.filter(models.Notification.user_id == current_uid)

        if text_search:
            query = query.filter(models.Notification.message.ilike(f"%{text_search}%"))

        total = query.count()
        notifications = query.offset(offset).limit(limit).all()

        data = [
            {
                "id": n.id,
                "user_id": n.user_id,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in notifications
        ]
        return data, total

    def get_notification_by_id(self, notification_id: int):
        current_uid = self.user.get("id") if isinstance(self.user, dict) else getattr(self.user, "id", None)
        current_role = self.user.get("role") if isinstance(self.user, dict) else getattr(self.user, "role", None)
        
        query = self.db.query(models.Notification).filter(models.Notification.id == notification_id)
        if current_role != "admin" and current_uid is not None:
            query = query.filter(models.Notification.user_id == current_uid)
        return query.first()

    def create_notification(self, data: NotificationCreate):
        new_notification = models.Notification(
            user_id=data.user_id,
            title=data.title,
            message=data.message,
            is_read=data.is_read,
        )

        self.db.add(new_notification)
        self.db.commit()
        self.db.refresh(new_notification)
        return new_notification

    def update_notification(self, data: NotificationUpdate):
        notification = self.db.query(models.Notification).filter(models.Notification.id == data.id).first()
        if not notification:
            return None
            
        current_uid = self.user.get("id") if isinstance(self.user, dict) else getattr(self.user, "id", None)
        current_role = self.user.get("role") if isinstance(self.user, dict) else getattr(self.user, "role", None)
        
        if current_role != "admin" and current_uid is not None and notification.user_id != current_uid:
            raise HTTPException(status_code=403, detail="Not authorized to update this notification")

        if data.title is not None:
            notification.title = data.title
        if data.message is not None:
            notification.message = data.message
        if data.is_read is not None:
            notification.is_read = data.is_read

        self.db.commit()
        self.db.refresh(notification)
        return notification

    def delete_notification(self, notification_id: int):
        notification = self.db.query(models.Notification).filter(models.Notification.id == notification_id).first()
        if not notification:
            return None
            
        current_uid = self.user.get("id") if isinstance(self.user, dict) else getattr(self.user, "id", None)
        current_role = self.user.get("role") if isinstance(self.user, dict) else getattr(self.user, "role", None)
        
        if current_role != "admin" and current_uid is not None and notification.user_id != current_uid:

            raise HTTPException(status_code=403, detail="Not authorized to delete this notification")

        self.db.delete(notification)
        self.db.commit()
        return notification
