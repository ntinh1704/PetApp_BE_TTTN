from sqlalchemy.orm import Session
from fastapi import HTTPException
from db import models
from schemas.booking_schema import BookingCreate, BookingUpdate


class BookingDatabaseApi:
    def __init__(self, current_user):
        db, token_data, _ = current_user
        self.db: Session = db
        self.user = token_data
        
        # Safely get current user ID and role
        self.current_uid = self.user.get("id") if isinstance(self.user, dict) else getattr(self.user, "id", None)
        self.current_role = self.user.get("role") if isinstance(self.user, dict) else getattr(self.user, "role", None)

    def get_list_booking(
        self, offset: int = 0, limit: int = 10, text_search: str = None
    ):
        query = self.db.query(models.Booking)

        # Lọc Booking theo quyền sở hữu của User (trừ khi là admin)
        if self.current_role != "admin" and self.current_uid is not None:
            query = query.filter(models.Booking.user_id == self.current_uid)

        if text_search:
            query = query.filter(models.Booking.status.ilike(f"%{text_search}%"))

        total = query.count()
        bookings = query.offset(offset).limit(limit).all()

        data = [
            {
                "id": b.id,
                "user_id": b.user_id,
                "pet_id": b.pet_id,
                "booking_date": b.booking_date,
                "booking_time": b.booking_time,
                "status": b.status,
                "total_price": b.total_price,
                "note": b.note,
                "created_at": b.created_at,
            }
            for b in bookings
        ]
        return data, total

    def get_booking_by_id(self, booking_id: int):
        query = self.db.query(models.Booking).filter(models.Booking.id == booking_id)
        if self.current_role != "admin" and self.current_uid is not None:
            query = query.filter(models.Booking.user_id == self.current_uid)
        return query.first()

    def create_booking(self, data: BookingCreate):
        # 1. Validate Ownership of Pet
        pet = self.db.query(models.Pet).filter(models.Pet.id == data.pet_id).first()
        if not pet or pet.user_id != data.user_id:
            raise HTTPException(status_code=400, detail="Invalid pet id or not owned by user.")
            
        # 2. Get Services and Calculate Price
        services = self.db.query(models.Service).filter(models.Service.id.in_(data.service_ids)).all()
        if not services or len(services) != len(data.service_ids):
            raise HTTPException(status_code=400, detail="Invalid service_ids provided.")
            
        total_price = sum(s.price for s in services)
        if data.total_price is not None:
            total_price = data.total_price

        # 3. Create main booking record
        new_booking = models.Booking(
            user_id=data.user_id,
            pet_id=data.pet_id,
            booking_date=data.booking_date,
            booking_time=data.booking_time,
            status=data.status or "pending",
            note=data.note,
            total_price=total_price,
        )

        self.db.add(new_booking)
        self.db.flush() # flush to get new_booking.id

        # 4. Create BookingService associations
        for s in services:
            bs = models.BookingService(
                booking_id=new_booking.id,
                service_id=s.id,
                price=s.price
            )
            self.db.add(bs)

        self.db.commit()
        self.db.refresh(new_booking)
        return new_booking

    def update_booking(self, data: BookingUpdate):
        booking = self.db.query(models.Booking).filter(models.Booking.id == data.id).first()
        if not booking:
            return None
        
        # Check ownership
        if self.current_role != "admin" and self.current_uid is not None and booking.user_id != self.current_uid:
            raise HTTPException(status_code=403, detail="Not authorized to update this booking")

        if data.booking_date is not None:
            booking.booking_date = data.booking_date
        if data.booking_time is not None:
            booking.booking_time = data.booking_time
        if data.status is not None:
            booking.status = data.status
        if data.note is not None:
            booking.note = data.note
            
        if data.service_ids is not None:
            # Delete old services relation
            self.db.query(models.BookingService).filter(models.BookingService.booking_id == booking.id).delete()
            # Add new services
            services = self.db.query(models.Service).filter(models.Service.id.in_(data.service_ids)).all()
            for s in services:
                self.db.add(models.BookingService(booking_id=booking.id, service_id=s.id, price=s.price))
            # Automatically recount total price
            booking.total_price = sum(s.price for s in services)

        self.db.commit()
        self.db.refresh(booking)
        return booking

    def delete_booking(self, booking_id: int):
        booking = self.db.query(models.Booking).filter(models.Booking.id == booking_id).first()
        if not booking:
            return None
            
        # Check ownership
        if self.current_role != "admin" and self.current_uid is not None and booking.user_id != self.current_uid:
            raise HTTPException(status_code=403, detail="Not authorized to delete this booking")

        self.db.delete(booking)
        self.db.commit()
        return booking
