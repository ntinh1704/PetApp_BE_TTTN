from datetime import datetime
from db.database import Base

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    DECIMAL,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import relationship

import bcrypt as bcrypt_lib

MAX_BCRYPT_LENGTH = 72


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    gender = Column(String(255), nullable=True)
    dob = Column(String(255), nullable=True)
    phone = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    avatar = Column(String(255), nullable=True)
    role = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    reset_otp = Column(String(255), nullable=True)
    reset_otp_expire = Column(DateTime, nullable=True)

    pets = relationship("Pet", back_populates="owner", cascade="all, delete-orphan")
    bookings = relationship(
        "Booking", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    cart = relationship(
        "Cart", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def verify_password(self, password: str) -> bool:
        truncated_password = password.encode("utf-8")[:MAX_BCRYPT_LENGTH]
        return bcrypt_lib.checkpw(truncated_password, self.password.encode("utf-8"))

    def set_password(self, password: str):
        truncated_password = password.encode("utf-8")[:MAX_BCRYPT_LENGTH]
        self.password = bcrypt_lib.hashpw(
            truncated_password, bcrypt_lib.gensalt()
        ).decode("utf-8")


class Pet(Base):
    __tablename__ = "pet"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    breed = Column(String(255), nullable=True)
    gender = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    color = Column(String(255), nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    image = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    owner = relationship("User", back_populates="pets")
    bookings = relationship(
        "Booking", back_populates="pet", cascade="all, delete-orphan"
    )


class Service(Base):
    __tablename__ = "service"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(255), nullable=True)
    price = Column(DECIMAL(10, 2), nullable=True)
    duration = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    booking_services = relationship(
        "BookingService", back_populates="service", cascade="all, delete-orphan"
    )
    images = relationship(
        "ServiceImage", back_populates="service", cascade="all, delete-orphan"
    )
    cart_items = relationship(
        "CartItem", back_populates="service", cascade="all, delete-orphan"
    )


class Booking(Base):
    __tablename__ = "booking"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pet.id", ondelete="CASCADE"), nullable=False)
    booking_date = Column(Date, nullable=True)
    booking_time = Column(Time, nullable=True)
    booking_end_time = Column(Time, nullable=True)
    status = Column(String(255), nullable=True)
    note = Column(Text, nullable=True)
    cancel_reason = Column(String(255), nullable=True)
    payment_method = Column(String(255), nullable=True)
    total_price = Column(DECIMAL(12, 2), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="bookings")
    pet = relationship("Pet", back_populates="bookings")
    services = relationship(
        "BookingService", back_populates="booking", cascade="all, delete-orphan"
    )


class BookingService(Base):
    __tablename__ = "booking_service"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_id = Column(
        Integer, ForeignKey("booking.id", ondelete="CASCADE"), nullable=False
    )
    service_id = Column(
        Integer, ForeignKey("service.id", ondelete="CASCADE"), nullable=False
    )
    price = Column(DECIMAL(10, 2), nullable=True)

    booking = relationship("Booking", back_populates="services")
    service = relationship("Service", back_populates="booking_services")


class Notification(Base):
    __tablename__ = "notification"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="notifications")


class ServiceImage(Base):
    __tablename__ = "service_image"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_id = Column(
        Integer, ForeignKey("service.id", ondelete="CASCADE"), nullable=False
    )
    image_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    service = relationship("Service", back_populates="images")


class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="cart")
    items = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(Base):
    __tablename__ = "cart_item"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey("cart.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(
        Integer, ForeignKey("service.id", ondelete="CASCADE"), nullable=False
    )
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())

    cart = relationship("Cart", back_populates="items")
    service = relationship("Service", back_populates="cart_items")
