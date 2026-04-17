import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from db.database import SessionLocal
from db.models import Booking

async def auto_cancel_unpaid_bookings():
    """
    Background task that runs periodically to cancel unpaid bookings
    that have been pending for more than X minutes.
    """
    CHECK_INTERVAL_SECONDS = 60 * 5  # Check every 5 minutes
    EXPIRATION_MINUTES = 15
    
    print(f"[Scheduler] Đã khởi động tác vụ dọn dẹp đơn hàng chưa thanh toán mỗi {CHECK_INTERVAL_SECONDS // 60} phút.")
    while True:
        try:
            db: Session = SessionLocal()
            try:
                # Calculate expiration time
                expiration_time = datetime.now() - timedelta(minutes=EXPIRATION_MINUTES)
                
                # Find expired pending bookings for SePay (case-insensitive status comparison)
                expired_bookings = db.query(Booking).filter(
                    or_(
                        func.lower(Booking.status) == 'pending',
                        func.lower(Booking.status) == 'đang xác nhận',
                        func.lower(Booking.status) == 'chờ thanh toán'
                    ),
                    func.lower(Booking.payment_method) == 'sepay',
                    Booking.created_at <= expiration_time
                ).all()
                
                if expired_bookings:
                    for booking in expired_bookings:
                        booking.status = 'cancelled'
                        booking.cancel_reason = f'Hệ thống đã tự động hủy do quá hạn thanh toán {EXPIRATION_MINUTES} phút'
                    
                    db.commit()
                    print(f"[Scheduler] Đã tự động hủy {len(expired_bookings)} lịch hẹn chưa thanh toán quá tạn.")
            except Exception as e:
                db.rollback()
                print(f"[Scheduler] Lỗi khi đang truy xuất cơ sở dữ liệu: {e}")
            finally:
                db.close()
                pass
                
        except Exception as e:
            print(f"[Scheduler] Vòng lặp scheduler gặp sự cố: {e}")
            
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
