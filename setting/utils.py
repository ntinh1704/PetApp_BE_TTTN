from typing import List, Any, Dict
from fastapi import Query
from typing import Tuple
from fastapi import Depends, HTTPException, Request, status
import math
from sqlalchemy.orm import Session
from db.database import get_db
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from db.models import User

JWT_SECRET = "mysecretkey"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_MINUTES = 1440

security = HTTPBearer()


def create_access_token(data: dict, expires_minutes=ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_minutes=REFRESH_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return (db, {"user_id": user.id, "username": user.username, "role": user.role}, token)

def get_offset_limit(page_size: int = 10, page: int = 0):
    if page_size <= 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Incorrect page link page size '{page_size}'. Page size must be greater than zero.",
        )
    if page < 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Incorrect page '{page}'. Page must be positive number.",
        )
    offset = page * page_size
    return offset, page_size


def get_pages_records(data, offset_limit):
    offset, limit = offset_limit
    records, total = data
    return {
        "total_pages": math.ceil(total / limit),
        "total_elements": total,
        "has_next": offset + len(records) < total,
        "data": records,
    }
