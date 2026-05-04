from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from db import models
from schemas.booking_schema import BookingCreate, BookingUpdate, BookingAddService


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

        user_label = booking.user.name or booking.user.email if booking.user else f"#{booking.user_id}"
        message = f"Bạn có lịch hẹn mới mã #{booking.id} từ {user_label}"

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
            message=f"Lịch hẹn mã #{booking.id} của bạn đã được xác nhận",
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

    def _time_to_minutes(self, t):
        """Convert time object or string HH:MM to total minutes"""
        if t is None:
            return 0
        if isinstance(t, str):
            parts = t.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        return t.hour * 60 + t.minute

    def _check_staff_conflict(self, staff_id, booking_date, booking_time, booking_end_time, exclude_booking_id=None):
        """Kiểm tra nhân viên có bị trùng lịch không. Trả về thông tin conflict nếu có."""
        if not staff_id or not booking_date or not booking_time:
            return None

        query = self.db.query(models.Booking).filter(
            models.Booking.staff_id == staff_id,
            models.Booking.booking_date == booking_date,
        )
        if exclude_booking_id:
            query = query.filter(models.Booking.id != exclude_booking_id)

        bookings_on_date = query.all()

        req_start = self._time_to_minutes(booking_time)
        req_end = self._time_to_minutes(booking_end_time) if booking_end_time else req_start + 30

        for b in bookings_on_date:
            st = (b.status or "").strip().lower()
            if st in ["cancelled", "đã hủy"]:
                continue
            if not b.booking_time:
                continue

            b_start = self._time_to_minutes(b.booking_time)
            b_end = self._time_to_minutes(b.booking_end_time) if b.booking_end_time else b_start + 30

            # Overlap: b_start < req_end && b_end > req_start
            if b_start < req_end and b_end > req_start:
                busy_from = b.booking_time.strftime("%H:%M") if hasattr(b.booking_time, 'strftime') else str(b.booking_time)[:5]
                busy_to = b.booking_end_time.strftime("%H:%M") if b.booking_end_time and hasattr(b.booking_end_time, 'strftime') else (str(b.booking_end_time)[:5] if b.booking_end_time else busy_from)
                return {
                    "booking_id": b.id,
                    "busy_from": busy_from,
                    "busy_to": busy_to,
                }
        return None

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
                "staff_id": b.staff_id,
                "staff_name": b.staff.name if b.staff else None,
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
                "services_detail": [
                    {
                        "id": bs.id,
                        "service_id": bs.service_id,
                        "service_name": bs.service.name if bs.service else None,
                        "price": float(bs.price or 0),
                        "quantity": bs.quantity or 1,
                        "is_addon": bs.is_addon or False,
                        "subtotal": float(bs.price or 0) * (bs.quantity or 1),
                    }
                    for bs in b.services
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
            "staff_id": b.staff_id,
            "staff_name": b.staff.name if b.staff else None,
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
            "services_detail": [
                {
                    "id": bs.id,
                    "service_id": bs.service_id,
                    "service_name": bs.service.name if bs.service else None,
                    "price": float(bs.price or 0),
                    "quantity": bs.quantity or 1,
                    "is_addon": bs.is_addon or False,
                    "subtotal": float(bs.price or 0) * (bs.quantity or 1),
                }
                for bs in b.services
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

        # Validate staff if provided
        if data.staff_id is not None:
            staff = self.db.query(models.Staff).filter(
                models.Staff.id == data.staff_id,
                models.Staff.is_active == True
            ).first()
            if not staff:
                raise HTTPException(status_code=400, detail="Invalid staff_id or staff is inactive.")

            # Check staff schedule conflict
            conflict = self._check_staff_conflict(
                staff_id=data.staff_id,
                booking_date=data.booking_date,
                booking_time=data.booking_time,
                booking_end_time=data.booking_end_time,
            )
            if conflict:
                raise HTTPException(
                    status_code=409,
                    detail=f"Nhân viên đã có lịch hẹn từ {conflict['busy_from']} - {conflict['busy_to']}. Vui lòng chọn nhân viên hoặc khung giờ khác."
                )

        # 2. Get Services and Calculate Price
        unique_service_ids = set(data.service_ids)
        services_from_db = self.db.query(models.Service).filter(models.Service.id.in_(unique_service_ids)).all()
        if not services_from_db or len(services_from_db) != len(unique_service_ids):
            raise HTTPException(status_code=400, detail="Invalid service_ids provided.")
            
        service_map = {s.id: s for s in services_from_db}
        services = [service_map[s_id] for s_id in data.service_ids]

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
            staff_id=data.staff_id,
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

        # 5. Create BookingService associations with quantity tracking
        from collections import Counter
        service_counts = Counter(data.service_ids)
        for s_id, qty in service_counts.items():
            s = service_map[s_id]
            bs = models.BookingService(
                booking_id=new_booking.id,
                service_id=s.id,
                price=s.price,
                quantity=qty,
                is_addon=False,
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
        if hasattr(data, "staff_id") and data.staff_id is not None:
            # Validate staff exists and is active
            staff = self.db.query(models.Staff).filter(
                models.Staff.id == data.staff_id,
                models.Staff.is_active == True
            ).first()
            if staff:
                # Check staff schedule conflict (exclude current booking)
                check_date = data.booking_date if data.booking_date is not None else booking.booking_date
                check_time = data.booking_time if data.booking_time is not None else booking.booking_time
                check_end = booking.booking_end_time
                conflict = self._check_staff_conflict(
                    staff_id=data.staff_id,
                    booking_date=check_date,
                    booking_time=check_time,
                    booking_end_time=check_end,
                    exclude_booking_id=booking.id,
                )
                if conflict:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Nhân viên đã có lịch hẹn từ {conflict['busy_from']} - {conflict['busy_to']}. Vui lòng chọn nhân viên hoặc khung giờ khác."
                    )
                booking.staff_id = data.staff_id

        if data.service_ids is not None:
            # Delete old services relation
            self.db.query(models.BookingService).filter(models.BookingService.booking_id == booking.id).delete()
            # Add new services
            unique_service_ids = set(data.service_ids)
            services_from_db = self.db.query(models.Service).filter(models.Service.id.in_(unique_service_ids)).all()
            service_map = {s.id: s for s in services_from_db}
            services = [service_map[s_id] for s_id in data.service_ids if s_id in service_map]
            
            for s in services:
                self.db.add(models.BookingService(booking_id=booking.id, service_id=s.id, price=s.price))
            # Automatically recount total price
            booking.total_price = sum(s.price for s in services)

        self.db.commit()
        self.db.refresh(booking)

        new_status = (booking.status or "").strip().lower()
        
        is_old_pending = old_status in ["pending", "đang xác nhận", "chờ thanh toán", "đã thanh toán"]
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
            msg = f"Yêu cầu hủy lịch hẹn #{booking.id} đã bị từ chối."
            if getattr(booking, "cancel_reason", None):
                msg += f" Lý do: {booking.cancel_reason}"
            else:
                msg += " Vui lòng liên hệ shop."
            self._create_user_notification(booking, "Yêu cầu bị từ chối", msg)
            
        # 5. Admin xác nhận bình thường
        elif new_status in ["confirmed", "đã xác nhận"] and old_status not in ["confirmed", "đã xác nhận", "cancel_requested"]:
            self._create_user_confirmed_notification(booking)
            
        # 6. Admin hoàn tất - recalculate total_price from all services
        elif new_status in ["completed", "hoàn thành", "đã hoàn thành"] and old_status not in ["completed", "hoàn thành", "đã hoàn thành"]:
            # Recalculate total from all BookingService (original + addon)
            total = sum(
                float(bs.price or 0) * (bs.quantity or 1)
                for bs in booking.services
            )
            booking.total_price = total
            self.db.commit()
            self.db.refresh(booking)
            self._create_user_notification(booking, "Dịch vụ đã hoàn tất", f"Dịch vụ cho lịch hẹn #{booking.id} đã hoàn thành. Tổng tiền: {int(total):,}đ. Cảm ơn bạn!")

        return booking

    def add_service_to_booking(self, data: BookingAddService):
        """Admin thêm dịch vụ phát sinh vào booking đang phục vụ"""
        if self.current_role != "admin":
            raise HTTPException(status_code=403, detail="Admin role required")

        booking = self.db.query(models.Booking).filter(models.Booking.id == data.booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        # Only allow adding services to confirmed bookings
        status = (booking.status or "").strip().lower()
        if status not in ["confirmed", "đã xác nhận"]:
            raise HTTPException(status_code=400, detail="Chỉ có thể thêm dịch vụ cho lịch hẹn đã xác nhận")

        # Validate service
        service = self.db.query(models.Service).filter(models.Service.id == data.service_id).first()
        if not service:
            raise HTTPException(status_code=400, detail="Invalid service_id")

        # Check if addon already exists for this service
        existing_addon = (
            self.db.query(models.BookingService)
            .filter(
                models.BookingService.booking_id == booking.id,
                models.BookingService.service_id == data.service_id,
                models.BookingService.is_addon == True,
            )
            .first()
        )

        if existing_addon:
            existing_addon.quantity = (existing_addon.quantity or 1) + data.quantity
        else:
            new_bs = models.BookingService(
                booking_id=booking.id,
                service_id=service.id,
                price=service.price,
                quantity=data.quantity,
                is_addon=True,
            )
            self.db.add(new_bs)

        # Recalculate total_price
        self.db.flush()
        total = sum(
            float(bs.price or 0) * (bs.quantity or 1)
            for bs in booking.services
        )
        booking.total_price = total

        # Recalculate booking_end_time
        if booking.booking_time:
            total_duration = sum(
                (bs.service.duration or 0) * (bs.quantity or 1)
                for bs in booking.services
                if bs.service
            )
            if total_duration > 0:
                start_dt = datetime.combine(datetime.today(), booking.booking_time)
                end_dt = start_dt + timedelta(minutes=total_duration)
                new_end_time = end_dt.time()

                # Check if new end_time causes conflict with next booking of same staff
                if booking.staff_id:
                    conflict = self._check_staff_conflict(
                        staff_id=booking.staff_id,
                        booking_date=booking.booking_date,
                        booking_time=booking.booking_time,
                        booking_end_time=new_end_time,
                        exclude_booking_id=booking.id,
                    )
                    if conflict:
                        raise HTTPException(
                            status_code=409,
                            detail=f"Thêm dịch vụ sẽ kéo dài thời gian và trùng với lịch hẹn từ {conflict['busy_from']} - {conflict['busy_to']} của nhân viên này."
                        )

                booking.booking_end_time = new_end_time

        self.db.commit()
        self.db.refresh(booking)

        # Notify user about addon
        self._create_user_notification(
            booking,
            "Dịch vụ phát sinh",
            f"Cửa hàng đã thêm dịch vụ \"{service.name}\" (x{data.quantity}) vào lịch hẹn #{booking.id}."
        )

        return booking

    def get_staff_availability(self, booking_date: str, booking_time: str, booking_end_time: str):
        """Trả về danh sách nhân viên kèm trạng thái rảnh/bận tại khung giờ + tất cả lịch bận trong ngày"""
        active_staff = (
            self.db.query(models.Staff)
            .filter(models.Staff.is_active == True)
            .all()
        )

        # Get all non-cancelled bookings for that date
        bookings_on_date = (
            self.db.query(models.Booking)
            .filter(
                models.Booking.booking_date == booking_date,
                models.Booking.staff_id.isnot(None),
            )
            .all()
        )

        # Filter out cancelled bookings
        active_bookings = [
            b for b in bookings_on_date
            if (b.status or "").strip().lower() not in ["cancelled", "đã hủy"]
        ]

        def time_to_minutes(t):
            if t is None:
                return 0
            if isinstance(t, str):
                parts = t.split(":")
                return int(parts[0]) * 60 + int(parts[1])
            return t.hour * 60 + t.minute

        def format_time_str(t):
            if t is None:
                return ""
            if isinstance(t, str):
                return t[:5]
            return t.strftime("%H:%M") if hasattr(t, 'strftime') else str(t)[:5]

        req_start = time_to_minutes(booking_time)
        req_end = time_to_minutes(booking_end_time)

        result = []
        for s in active_staff:
            # Thu thập TẤT CẢ khung giờ bận trong ngày của nhân viên này
            all_busy_slots = []
            overlap_info = None

            for b in active_bookings:
                if b.staff_id != s.id:
                    continue
                b_start = time_to_minutes(b.booking_time)
                b_end = time_to_minutes(b.booking_end_time) if b.booking_end_time else b_start + 30

                busy_from_str = format_time_str(b.booking_time)
                busy_to_str = format_time_str(b.booking_end_time) if b.booking_end_time else busy_from_str

                # Thêm vào danh sách tất cả lịch bận
                all_busy_slots.append({"from": busy_from_str, "to": busy_to_str})

                # Overlap check cho khung giờ đang yêu cầu
                if b_start < req_end and b_end > req_start and overlap_info is None:
                    overlap_info = {"busy_from": busy_from_str, "busy_to": busy_to_str}

            # Sắp xếp busy_slots theo thời gian
            all_busy_slots.sort(key=lambda x: x["from"])

            result.append({
                "id": s.id,
                "name": s.name,
                "specialty": s.specialty,
                "avatar": s.avatar,
                "status": "busy" if overlap_info else "available",
                **(overlap_info or {}),
                "busy_slots": all_busy_slots,
            })

        return result

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
