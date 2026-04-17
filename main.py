from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid

from db import models
from db.database import engine
from router import user, pet, booking, service, notification, chatbot, sepay, cart
from setting.config import settings

from contextlib import asynccontextmanager
import asyncio
from scheduler import auto_cancel_unpaid_bookings

models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background task to clean up old unpaid bookings
    scheduler_task = asyncio.create_task(auto_cancel_unpaid_bookings())
    yield
    # Stop the background task on shutdown
    scheduler_task.cancel()

app = FastAPI(title=settings.APP_NAME, debug=settings.APP_DEBUG, lifespan=lifespan)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(user.router)
app.include_router(pet.router)
app.include_router(booking.router)
app.include_router(service.router)
app.include_router(notification.router)
app.include_router(chatbot.router)
app.include_router(sepay.router)
app.include_router(cart.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    ext = Path(file.filename).suffix or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / filename
    with file_path.open("wb") as f:
        f.write(await file.read())

    # Trả về đường dẫn tương đối để đảm bảo đồng bộ chéo thiết bị
    url = f"/uploads/{filename}"
    return {"url": url}


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} is running!"}
