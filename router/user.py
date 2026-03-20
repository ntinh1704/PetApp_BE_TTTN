from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from controller import user
from db.database import get_db
from schemas.user_schema import (
    LoginResponse,
    LoginRequest,
    UserBase,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from setting.utils import get_current_user
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
def get_list_user(
    data=Depends(user.get_list_user),
    _current_user=Depends(get_current_user),
):
    return data


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    return user.get_user_by_id(user_id, db)


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return user.login_user(data, db)


@router.post("/create", response_model=UserResponse)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    return user.create_user(data, db)


@router.put("/", response_model=UserResponse)
def update_user(
    data: UserUpdate,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    return user.update_user(data, db, _current_user)


@router.delete("/")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    return user.delete_user(user_id, db, _current_user)
