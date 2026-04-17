# crud/user_crud.py
from sqlalchemy.orm import Session
from db import models
from schemas import user_schema
from fastapi import UploadFile
import shutil
import os
from fastapi import HTTPException, Depends
from datetime import datetime, timedelta
import uuid


class DatabaseApi:
    def __init__(self, current_user):
        db, token_data, _ = current_user
        self.db: Session = db
        self.user = token_data

    def get_list_user(
        self,
        offset: int = None,
        limit: int = None,
        text_search: str = None,
    ):
        data = self.db.query(models.User)
        if text_search is not None:
            data = data.filter(models.User.email.ilike(f"%{text_search.lower()}%"))
        total = data.count()
        if offset != None and limit != None:
            data = data.offset(offset).limit(limit)
        data = data.all()
        rc = [
            {
                "id": str(record.id),
                "role": record.role,
                "email": record.email,
                "name": record.name,
                "gender": record.gender,
                "dob": record.dob,
                "phone": record.phone,
                "address": record.address,
                "avatar": record.avatar,
                "is_active": getattr(record, "is_active", True),
                "created_at": record.created_at,
            }
            for record in data
        ]
        return rc, total

    def get_user_by_id(self, user_id: int):
        return self.db.query(models.User).filter(models.User.id == user_id).first()

    def create_user(self, data: user_schema.UserCreate):
        new_user = models.User(
            email=data.email,
            password="",  # set later
            role=data.role or "user",
        )
        new_user.set_password(data.password)
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def update_user(self, data: user_schema.UserUpdate):
        user = self.db.query(models.User).filter(models.User.id == data.id).first()
        if not user:
            return None

        if data.email is not None:
            user.email = data.email
        if data.password is not None:
            user.set_password(data.password)
        if data.role is not None:
            user.role = data.role

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int):
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return None

        self.db.delete(user)
        self.db.commit()
        return user
