import re
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Booking

router = APIRouter(prefix="/sepay", tags=["SePay"])

@router.post("/webhook")
async def sepay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook endpoint to receive payment notifications from SePay.
    """
    try:
        data = await request.json()
    except Exception:
        return {"success": False, "message": "Invalid JSON"}

    # Chỉ xử lý các giao dịch chuyển tiền VÀO
    if data.get("transferType") == "in":
        content = data.get("content", "")
        
        # Tìm mã booking với Regex: "BK123"
        match = re.search(r"bk(\d+)", content, re.IGNORECASE)
        if match:
            booking_id = int(match.group(1))
            
            # Tìm booking trong database
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            
            # Nếu booking tồn tại, cập nhật phương thức thanh toán và trạng thái
            if booking:
                booking.payment_method = "sepay"
                
                # Danh sách các trạng thái chờ xử lý (cả tiếng Anh và tiếng Việt)
                pending_statuses = [
                    "Chờ thanh toán", "awaiting_payment", 
                    "Đang xác nhận", "pending", 
                    "Đang chờ"
                ]
                
                if booking.status in pending_statuses:
                    booking.status = "Đã xác nhận"
                
                db.commit()
                return {"success": True, "message": f"Updated booking {booking_id} to SePay"}
    
    return {"success": True, "message": "Ignored"}
