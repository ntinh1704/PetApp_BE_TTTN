from datetime import datetime, timedelta
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
        self.current_uid = (
            (self.user.get("id") or self.user.get("user_id"))
            if isinstance(self.user, dict)
            else (getattr(self.user, "id", None) or getattr(self.user, "user_id", None))
        )
        self.current_role = self.user.get("role") if isinstance(self.user, dict) else getattr(self.user, "role", None)

    def _get_admin_user_ids(self):
        admins = self.db.query(models.User).filter(models.User.role == "admin").all()
        return [admin.id for admin in admins]

    def _create_admin_notification(self, booking):
        admin_ids = self._get_admin_user_ids()
        if not admin_ids:
                return

        user_label = booking.user.email if booking.user else f"#{booking.user_id}"
        message = f"Bạn có lịch hẹn mới từ {user_label}"

        for admin_id in admin_ids:
            notification = models.Notification(
                user_id=admin_id,
                title="Lịch hẹn mới",
                message=message,
                is_read=False,
            )
            self.db.add(notification)

        self.db.commit()

    def _create_user_confirmed_notification(self, booking):
        if not booking.user_id:
            return

        notification = models.Notification(
            user_id=booking.user_id,
            title="Xác nhận lịch hẹn",
            message="Lịch hẹn của bạn đã được xác nhận",
            is_read=False,
        )

        self.db.add(notification)
        self.db.commit()

    def _create_notification_for_admins(self, title: str, message: str):
        admin_ids = self._get_admin_user_ids()
        if not admin_ids:
            return
        for admin_id in admin_ids:
            notification = models.Notification(
                user_id=admin_id,
                title=title,
                message=message,
                is_read=False,
            )
            self.db.add(notification)
        self.db.commit()

    def _create_user_notification(self, booking, title: str, message: str):
        if not booking.user_id:
            return
        notification = models.Notification(
            user_id=booking.user_id,
            title=title,
            message=message,
            is_read=False,
        )
        self.db.add(notification)
        self.db.commit()

    def get_list_booking(
        self, offset: int = 0, limit: int | None = 10, text_search: str = None, booking_date: str = None
    ):
        query = self.db.query(models.Booking)

        # Lọc Booking theo quyền sở hữu của User (trừ khi là admin)
        if self.current_role != "admin" and self.current_uid is not None:
            query = query.filter(models.Booking.user_id == self.current_uid)

        if text_search:
            query = query.filter(models.Booking.status.ilike(f"%{text_search}%"))

        if booking_date:
            query = query.filter(models.Booking.booking_date == booking_date)

        total = query.count()
        if limit is None:
            bookings = query.all()
        else:
            bookings = query.offset(offset).limit(limit).all()

        data = [
            {
                "id": b.id,
                "user_id": b.user_id,
                "user_name": (b.user.name or b.user.email) if b.user else None,
                "pet_id": b.pet_id,
                "pet_name": b.pet.name if b.pet else None,
                "service_name": (
                    b.services[0].service.name
                    if b.services and b.services[0].service
                    else None
                ),
                "service_icon": (
                    b.services[0].service.icon
                    if b.services and b.services[0].service
                    else None
                ),
                "service_names": [
                    bs.service.name for bs in b.services if bs.service and bs.service.name
                ],
                "booking_date": b.booking_date,
                "booking_time": b.booking_time,
                "booking_end_time": b.booking_end_time,
                "status": b.status,
                "total_price": b.total_price,
                "payment_method": b.payment_method,
                "note": b.note,
                "cancel_reason": getattr(b, "cancel_reason", None),
                "created_at": b.created_at,
            }
            for b in bookings
        ]
        return data, total

    def get_booking_by_id(self, booking_id: int):
        query = self.db.query(models.Booking).filter(models.Booking.id == booking_id)
        if self.current_role != "admin" and self.current_uid is not None:
            query = query.filter(models.Booking.user_id == self.current_uid)
        
        b = query.first()
        if not b:
            return None
            
        return {
            "id": b.id,
            "user_id": b.user_id,
            "user_name": (b.user.name or b.user.email) if b.user else None,
            "pet_id": b.pet_id,
            "pet_name": b.pet.name if b.pet else None,
            "service_name": (
                b.services[0].service.name
                if b.services and b.services[0].service
                else None
            ),
            "service_icon": (
                b.services[0].service.icon
                if b.services and b.services[0].service
                else None
            ),
            "service_names": [
                bs.service.name for bs in b.services if bs.service and bs.service.name
            ],
            "booking_date": b.booking_date,
            "booking_time": b.booking_time,
            "booking_end_time": b.booking_end_time,
            "status": b.status,
            "total_price": b.total_price,
            "payment_method": b.payment_method,
            "note": b.note,
            "cancel_reason": getattr(b, "cancel_reason", None),
            "created_at": b.created_at,
        }

    def create_booking(self, data: BookingCreate):
        if self.current_uid is None:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # 1. Validate Ownership of Pet
        pet = self.db.query(models.Pet).filter(models.Pet.id == data.pet_id, models.Pet.is_deleted == False).first()
        if not pet or pet.user_id != self.current_uid:
            raise HTTPException(status_code=400, detail="Invalid pet id or not owned by user.")

        # 2. Get Services and Calculate Price
        services = self.db.query(models.Service).filter(models.Service.id.in_(data.service_ids)).all()
        if not services or len(services) != len(data.service_ids):
            raise HTTPException(status_code=400, detail="Invalid service_ids provided.")
            
        total_price = sum(s.price for s in services)
        if data.total_price is not None:
            total_price = data.total_price

        # 3. Calculate booking_end_time
        booking_end_time = data.booking_end_time
        if not booking_end_time and data.booking_time:
            total_duration = sum(s.duration or 0 for s in services)
            if total_duration > 0:
                start_dt = datetime.combine(datetime.today(), data.booking_time)
                end_dt = start_dt + timedelta(minutes=total_duration)
                booking_end_time = end_dt.time()

        # 4. Create main booking record
        new_booking = models.Booking(
            user_id=self.current_uid,
            pet_id=data.pet_id,
            booking_date=data.booking_date,
            booking_time=data.booking_time,
            booking_end_time=booking_end_time,
            status=data.status or "pending",
            note=data.note,
            total_price=total_price,
            payment_method=data.payment_method,
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

        self._create_admin_notification(new_booking)
        return new_booking

    def update_booking(self, data: BookingUpdate):
        booking = self.db.query(models.Booking).filter(models.Booking.id == data.id).first()
        if not booking:
            return None

        # Check ownership
        if self.current_role != "admin" and self.current_uid is not None and booking.user_id != self.current_uid:
            raise HTTPException(status_code=403, detail="Not authorized to update this booking")

        old_status = (booking.status or "").strip().lower()

        # Concurrency safety: Prevent admin from confirming an already cancelled booking
        if self.current_role == "admin" and data.status is not None:
             in_status = str(data.status).strip().lower()
             if old_status in ["cancelled", "đã hủy"] and in_status in ["confirmed", "đã xác nhận"]:
                 raise HTTPException(status_code=400, detail="Lịch hẹn đã bị khách hàng hủy trước đó.")

        # Concurrency safety: Prevent user from directly cancelling an already confirmed booking
        if self.current_role != "admin" and data.status is not None:
             in_status = str(data.status).strip().lower()
             if in_status in ["cancelled", "đã hủy"] and old_status not in ["pending", "đang xác nhận"]:
                 raise HTTPException(status_code=400, detail="Lịch hẹn của bạn đã được cửa hàng xác nhận. Vui lòng tải lại trang để gửi yêu cầu hủy lịch.")

        if data.booking_date is not None:
            booking.booking_date = data.booking_date
        if data.booking_time is not None:
            booking.booking_time = data.booking_time
        if data.status is not None:
            booking.status = data.status
        if data.note is not None:
            booking.note = data.note
        if hasattr(data, "cancel_reason") and data.cancel_reason is not None:
            booking.cancel_reason = data.cancel_reason
        if hasattr(data, "payment_method") and data.payment_method is not None:
            booking.payment_method = data.payment_method

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

        new_status = (booking.status or "").strip().lower()
        
        is_old_pending = old_status in ["pending", "đang xác nhận"]
        is_new_cancelled = new_status in ["cancelled", "đã hủy"]

        # 1. User tự hủy từ pending -> cancelled
        if is_old_pending and is_new_cancelled:
            user_label = booking.user.name or booking.user.email if booking.user else "Khách"
            msg = f"Khách hàng {user_label} đã hủy lịch hẹn mã #{booking.id}."
            if getattr(booking, "cancel_reason", None):
                msg += f" Lý do: {booking.cancel_reason}"
            self._create_notification_for_admins("Khách hàng đã hủy lịch hẹn", msg)
            
        # 2. User xin hủy từ confirmed -> cancel_requested
        elif old_status in ["confirmed", "đã xác nhận"] and new_status == "cancel_requested":
            user_label = booking.user.name or booking.user.email if booking.user else "Khách"
            msg = f"Khách hàng {user_label} yêu cầu hủy lịch hẹn mã #{booking.id}."
            if getattr(booking, "cancel_reason", None):
                msg += f" Lý do: {booking.cancel_reason}"
            self._create_notification_for_admins("Yêu cầu hủy lịch hẹn", msg)
            
        # 3. Admin duyệt hủy
        elif old_status == "cancel_requested" and new_status == "cancelled":
            self._create_user_notification(booking, "Lịch hẹn đã bị hủy", f"Yêu cầu hủy lịch hẹn #{booking.id} của bạn đã được chấp nhận.")
            
        # 4. Admin từ chối hủy
        elif old_status == "cancel_requested" and new_status in ["confirmed", "đã xác nhận"]:
            self._create_user_notification(booking, "Yêu cầu bị từ chối", f"Yêu cầu hủy lịch hẹn #{booking.id} đã bị từ chối. Vui lòng liên hệ shop.")
            
        # 5. Admin xác nhận bình thường
        elif new_status in ["confirmed", "đã xác nhận"] and old_status not in ["confirmed", "đã xác nhận", "cancel_requested"]:
            self._create_user_confirmed_notification(booking)
            
        # 6. Admin hoàn tất
        elif new_status in ["completed", "hoàn thành", "đã hoàn thành"] and old_status not in ["completed", "hoàn thành", "đã hoàn thành"]:
            self._create_user_notification(booking, "Dịch vụ đã hoàn tất", f"Dịch vụ cho lịch hẹn #{booking.id} đã hoàn thành. Cảm ơn bạn!")

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
