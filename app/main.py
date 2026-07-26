import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
from app.routes import items, requests, export, chat, analytics, audit

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hệ Thống Quản Lý Kho Nội Bộ (MVP)",
    description="Hệ thống quản lý vật tư & tự động hóa tạo báo cáo (PDF, Word, Excel) kèm quét mã QR/Barcode, Trợ lý AI và Phân tích Dự báo Kho",
    version="2.0.0"
)

# Ensure folders exist
exports_dir = os.path.join(os.getcwd(), "exports")
static_dir = os.path.join(os.getcwd(), "static")
uploads_dir = os.path.join(os.getcwd(), "uploads")
os.makedirs(exports_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)

# Mount exports, static & uploads folders
app.mount("/exports", StaticFiles(directory=exports_dir), name="exports")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include Routers
app.include_router(items.router)
app.include_router(requests.router)
app.include_router(export.router)
app.include_router(chat.router)
app.include_router(analytics.router)
app.include_router(audit.router)

@app.get("/")
def read_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Chào mừng đến với Hệ thống Quản lý kho Nội bộ (MVP)"}

@app.get("/scan")
def read_scan():
    scan_file = os.path.join(static_dir, "scan.html")
    if os.path.exists(scan_file):
        return FileResponse(scan_file)
    return {"message": "Trang Quét Mã QR Di Động"}

@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected"}
