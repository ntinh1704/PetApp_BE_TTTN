from sqlalchemy.orm import Session

from db import models
from schemas.service_schema import ServiceCreate, ServiceUpdate
from fastapi import HTTPException

class ServiceDatabaseApi:
    def __init__(self, current_user):
        db, token_data, _ = current_user
        self.db: Session = db
        self.user = token_data

    def get_list_service(
        self, offset: int = 0, limit: int = 10, text_search: str = None
    ):
        query = self.db.query(models.Service)

        if text_search:
            query = query.filter(models.Service.name.ilike(f"%{text_search}%"))

        total = query.count()
        services = query.offset(offset).limit(limit).all()

        data = [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "icon": s.icon,
                "price": s.price,
                "duration": s.duration,
                "created_at": s.created_at,
            }
            for s in services
        ]
        return data, total

    def get_service_by_id(self, service_id: int):
        return (
            self.db.query(models.Service)
            .filter(models.Service.id == service_id)
            .first()
        )

    def create_service(self, data: ServiceCreate):
        current_role = self.user.get("role") if isinstance(self.user, dict) else getattr(self.user, "role", None)
        if current_role != "admin":
            raise HTTPException(status_code=403, detail="Admin role required")

        new_service = models.Service(
            name=data.name,
            description=data.description,
            icon=data.icon,
            price=data.price,
            duration=data.duration,
        )

        self.db.add(new_service)
        self.db.commit()
        self.db.refresh(new_service)
        return new_service

    def update_service(self, data: ServiceUpdate):
        current_role = self.user.get("role") if isinstance(self.user, dict) else getattr(self.user, "role", None)
        if current_role != "admin":
            raise HTTPException(status_code=403, detail="Admin role required")

        service = (
            self.db.query(models.Service).filter(models.Service.id == data.id).first()
        )
        if not service:
            return None

        if data.name is not None:
            service.name = data.name
        if data.description is not None:
            service.description = data.description
        if data.icon is not None:
            service.icon = data.icon
        if data.price is not None:
            service.price = data.price
        if data.duration is not None:
            service.duration = data.duration

        self.db.commit()
        self.db.refresh(service)
        return service

    def delete_service(self, service_id: int):
        current_role = self.user.get("role") if isinstance(self.user, dict) else getattr(self.user, "role", None)
        if current_role != "admin":
            raise HTTPException(status_code=403, detail="Admin role required")

        service = (
            self.db.query(models.Service)
            .filter(models.Service.id == service_id)
            .first()
        )
        if not service:
            return None

        self.db.delete(service)
        self.db.commit()
        return service
