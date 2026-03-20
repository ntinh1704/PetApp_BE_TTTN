from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from crud import crud
from schemas.user_schema import LoginRequest, LoginResponse, UserCreate, UserBase, UserUpdate
from setting.utils import get_offset_limit, get_pages_records, get_current_user
from db.database import get_db
from crud.crud import DatabaseApi

from db.models import User
from setting.utils import create_access_token, create_refresh_token


def login_user(data: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not user.verify_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token_data = {"user_id": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return LoginResponse(access_token=access_token, refresh_token=refresh_token, role=user.role)


def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(User)
        .filter(
            (User.username == user.username)
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    # The first user created is admin, otherwise "user"
    if db.query(User).count() == 0:
        computed_role = "admin"
    else:
        computed_role = "user"

    new_user = User(
        username=user.username,
        password="", # set later
        role=computed_role,
    )
    new_user.set_password(user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user_obj = db.query(crud.models.User).filter(crud.models.User.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return user_obj


def update_user(data: UserUpdate, db: Session = Depends(get_db), current_user=None):
    user_obj = db.query(User).filter(User.id == data.id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
        
    if isinstance(current_user, tuple) and len(current_user) == 3:
        _, token_data, _ = current_user
        current_uid = token_data.get("user_id")
        current_role = token_data.get("role")
    else:
        current_uid = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        current_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    
    if current_role != "admin" and str(current_uid) != str(user_obj.id):
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    if data.username is not None:
        existing = (
            db.query(User)
            .filter(User.username == data.username)
            .first()
        )
        if existing and existing.id != data.id:
            raise HTTPException(status_code=400, detail="Username already exists")
        user_obj.username = data.username

    if data.password is not None:
        user_obj.set_password(data.password)

    if data.name is not None:
        user_obj.name = data.name
    if data.email is not None:
        user_obj.email = data.email
    if data.phone is not None:
        user_obj.phone = data.phone
    if data.avatar is not None:
        user_obj.avatar = data.avatar
    if data.role is not None:
        user_obj.role = data.role

    db.commit()
    db.refresh(user_obj)
    return user_obj


def delete_user(user_id: int, db: Session = Depends(get_db), current_user=None):
    user_obj = db.query(User).filter(User.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
        
    if isinstance(current_user, tuple) and len(current_user) == 3:
        _, token_data, _ = current_user
        current_uid = token_data.get("user_id")
        current_role = token_data.get("role")
    else:
        current_uid = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        current_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    
    if current_role != "admin" and str(current_uid) != str(user_obj.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")

    db.delete(user_obj)
    db.commit()
    return {"detail": "User deleted successfully"}


def get_list_user(
    text_search: str = None,
    current_user=Depends(get_current_user),
    offset_limit=Depends(get_offset_limit),
):
    db = DatabaseApi(current_user)
    offset, limit = offset_limit
    data, total = db.get_list_user(offset, limit, text_search)
    if not data:
        raise HTTPException(status_code=404, detail="No users found")
    data = data, total
    return get_pages_records(data, offset_limit)
