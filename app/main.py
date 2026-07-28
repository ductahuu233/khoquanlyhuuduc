import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
from app.routes import items, requests, export, chat, analytics, audit, inbound, assets, reports, auth

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hệ Thống Quản Lý Kho & Vòng Đời Tài Sản (v3.0 Security Edition)",
    description="Hệ thống quản lý vật tư & vòng đời tài sản chuyên nghiệp bảo mật mạng nội bộ - Đoàn Nghi lễ CAND",
    version="3.0.0"
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
app.include_router(auth.router)
app.include_router(items.router)
app.include_router(requests.router)
app.include_router(export.router)
app.include_router(chat.router)
app.include_router(analytics.router)
app.include_router(audit.router)
app.include_router(inbound.router)
app.include_router(assets.router)
app.include_router(reports.router)

@app.get("/")
def read_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Chào mừng đến với Hệ thống Quản lý Kho & Tài sản v3.0 - Đoàn Nghi lễ CAND"}

@app.get("/login")
def read_login():
    login_file = os.path.join(static_dir, "login.html")
    if os.path.exists(login_file):
        return FileResponse(login_file)
    return {"message": "Trang Đăng nhập Nội bộ"}

@app.get("/scan")
def read_scan():
    scan_file = os.path.join(static_dir, "scan.html")
    if os.path.exists(scan_file):
        return FileResponse(scan_file)
    return {"message": "Trang Quét Mã QR Di Động"}

@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected"}
