from fastapi import HTTPException, Depends, Query
from sqlalchemy.orm import Session
from crud import crud
from schemas.user_schema import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserBase,
    UserUpdate,
    ForgotPasswordRequest,
    VerifyOTPRequest,
    ResetPasswordRequest
)
from setting.utils import get_offset_limit, get_pages_records, get_current_user
from db.database import get_db
from crud.crud import DatabaseApi

from db.models import User
from setting.utils import create_access_token, create_refresh_token, send_reset_password_email
import random
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse


def _delete_local_uploaded_file(image_url: str | None):
    if not image_url:
        return

    try:
        parsed = urlparse(image_url)
        image_path = Path(parsed.path.lstrip("/"))
        if (
            image_path.parts
            and image_path.parts[0] == "uploads"
            and image_path.exists()
        ):
            image_path.unlink()
    except Exception:
        pass


def login_user(data: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.verify_password(data.password):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không chính xác")

    if not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=403,
            detail="Tài khoản đã bị vô hiệu hóa. Vui lòng liên hệ admin.",
        )

    token_data = {"user_id": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return LoginResponse(
        access_token=access_token, refresh_token=refresh_token, role=user.role
    )


def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter((User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email này đã tồn tại trong hệ thống")

    # The first user created is admin, otherwise "user"
    if db.query(User).count() == 0:
        computed_role = "admin"
    else:
        computed_role = "user"

    new_user = User(
        email=user.email,
        password="",  # set later
        name=getattr(user, "name", None),
        phone=getattr(user, "phone", None),
        gender=getattr(user, "gender", None),
        dob=getattr(user, "dob", None),
        address=getattr(user, "address", None),
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
        current_uid = (
            current_user.get("id")
            if isinstance(current_user, dict)
            else getattr(current_user, "id", None)
        )
        current_role = (
            current_user.get("role")
            if isinstance(current_user, dict)
            else getattr(current_user, "role", None)
        )

    if current_role != "admin" and str(current_uid) != str(user_obj.id):
        raise HTTPException(
            status_code=403, detail="Not authorized to update this user"
        )

    if data.email is not None:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing and existing.id != data.id:
            raise HTTPException(status_code=400, detail="Email already exists")
        user_obj.email = data.email

    if data.password is not None:
        user_obj.set_password(data.password)

    if data.name is not None:
        user_obj.name = data.name
    if data.gender is not None:
        user_obj.gender = data.gender
    if data.dob is not None:
        user_obj.dob = data.dob
    if data.phone is not None:
        user_obj.phone = data.phone
    if data.address is not None:
        user_obj.address = data.address
    if data.avatar is not None and data.avatar != user_obj.avatar:
        old_avatar = user_obj.avatar
        user_obj.avatar = data.avatar
        _delete_local_uploaded_file(old_avatar)
    if data.role is not None:
        user_obj.role = data.role
    if data.is_active is not None:
        user_obj.is_active = data.is_active

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
        current_uid = (
            current_user.get("id")
            if isinstance(current_user, dict)
            else getattr(current_user, "id", None)
        )
        current_role = (
            current_user.get("role")
            if isinstance(current_user, dict)
            else getattr(current_user, "role", None)
        )

    if current_role != "admin" and str(current_uid) != str(user_obj.id):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this user"
        )

    db.delete(user_obj)
    db.commit()
    return {"detail": "User deleted successfully"}


def get_list_user(
    text_search: str = None,
    all: bool = Query(False, description="Return all users without pagination"),
    current_user=Depends(get_current_user),
    offset_limit=Depends(get_offset_limit),
):
    db = DatabaseApi(current_user)

    if all:
        data, total = db.get_list_user(offset=None, limit=None, text_search=text_search)
        return data

    offset, limit = offset_limit
    data, total = db.get_list_user(offset, limit, text_search)
    if not data:
        raise HTTPException(status_code=404, detail="No users found")
    data = data, total
    return get_pages_records(data, offset_limit)


def forgot_password_logic(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        # Prevent email enumeration by returning a success-like message anyway, 
        # but in this case we'll throw 404 for clarity on frontend since it's an internal app.
        raise HTTPException(status_code=404, detail="Email không tồn tại trong hệ thống")
    
    otp = str(random.randint(100000, 999999))
    user.reset_otp = otp
    user.reset_otp_expire = datetime.utcnow() + timedelta(minutes=10)
    
    db.commit()
    
    send_reset_password_email(user.email, otp)
    
    return {"message": "Mã OTP đã được gửi đến email của bạn."}


def verify_otp_logic(data: VerifyOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại")
        
    if not user.reset_otp or user.reset_otp != data.otp:
        raise HTTPException(status_code=400, detail="Mã OTP không hợp lệ")
        
    if not user.reset_otp_expire or datetime.utcnow() > user.reset_otp_expire:
        raise HTTPException(status_code=400, detail="Mã OTP đã hết hạn")
        
    return {"message": "Mã OTP hợp lệ"}


def reset_password_logic(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại")
        
    if not user.reset_otp or user.reset_otp != data.otp:
        raise HTTPException(status_code=400, detail="Mã OTP không hợp lệ")
        
    if not user.reset_otp_expire or datetime.utcnow() > user.reset_otp_expire:
        raise HTTPException(status_code=400, detail="Mã OTP đã hết hạn")
        
    user.set_password(data.new_password)
    user.reset_otp = None
    user.reset_otp_expire = None
    
    db.commit()
    return {"message": "Mật khẩu đã được cập nhật thành công"}
