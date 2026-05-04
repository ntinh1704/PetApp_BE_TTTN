from sqlalchemy.orm import Session
from fastapi import HTTPException

from db import models
from schemas.staff_schema import StaffCreate, StaffUpdate


class StaffDatabaseApi:
    def __init__(self, current_user):
        db, token_data, _ = current_user
        self.db: Session = db
        self.user = token_data
        self.current_role = (
            self.user.get("role") if isinstance(self.user, dict)
            else getattr(self.user, "role", None)
        )

    def _require_admin(self):
        if self.current_role != "admin":
            raise HTTPException(status_code=403, detail="Admin role required")

    def get_list_staff(
        self, offset: int = 0, limit: int | None = 10, text_search: str = None
    ):
        query = self.db.query(models.Staff)

        if text_search:
            query = query.filter(models.Staff.name.ilike(f"%{text_search}%"))

        total = query.count()
        if limit is None:
            staff_list = query.all()
        else:
            staff_list = query.offset(offset).limit(limit).all()

        data = [
            {
                "id": s.id,
                "name": s.name,
                "phone": s.phone,
                "avatar": s.avatar,
                "specialty": s.specialty,
                "is_active": s.is_active,
                "created_at": s.created_at,
            }
            for s in staff_list
        ]
        return data, total

    def get_active_staff(self):
        """Danh sách nhân viên đang hoạt động (cho dropdown chọn)"""
        staff_list = (
            self.db.query(models.Staff)
            .filter(models.Staff.is_active == True)
            .all()
        )
        return [
            {
                "id": s.id,
                "name": s.name,
                "phone": s.phone,
                "avatar": s.avatar,
                "specialty": s.specialty,
            }
            for s in staff_list
        ]

    def get_staff_by_id(self, staff_id: int):
        s = self.db.query(models.Staff).filter(models.Staff.id == staff_id).first()
        if not s:
            return None
        return {
            "id": s.id,
            "name": s.name,
            "phone": s.phone,
            "avatar": s.avatar,
            "specialty": s.specialty,
            "is_active": s.is_active,
            "created_at": s.created_at,
        }

    def create_staff(self, data: StaffCreate):
        self._require_admin()

        new_staff = models.Staff(
            name=data.name,
            phone=data.phone,
            avatar=data.avatar,
            specialty=data.specialty,
        )
        self.db.add(new_staff)
        self.db.commit()
        self.db.refresh(new_staff)
        return new_staff

    def update_staff(self, data: StaffUpdate):
        self._require_admin()

        staff = self.db.query(models.Staff).filter(models.Staff.id == data.id).first()
        if not staff:
            return None

        if data.name is not None:
            staff.name = data.name
        if data.phone is not None:
            staff.phone = data.phone
        if data.avatar is not None:
            staff.avatar = data.avatar
        if data.specialty is not None:
            staff.specialty = data.specialty
        if data.is_active is not None:
            staff.is_active = data.is_active

        self.db.commit()
        self.db.refresh(staff)
        return staff

    def delete_staff(self, staff_id: int):
        self._require_admin()

        staff = self.db.query(models.Staff).filter(models.Staff.id == staff_id).first()
        if not staff:
            return None

        # Soft delete
        staff.is_active = False
        self.db.commit()
        self.db.refresh(staff)
        return staff
