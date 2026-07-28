import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, log_audit

router = APIRouter(prefix="/api/auth", tags=["Authentication & Security"])

SECRET_KEY = "CA_NGHI_LE_KHO_QUAN_LY_SECRET_KEY_2026"

def hash_password(password: str) -> str:
    """Hàm băm mật khẩu SHA-256 (tương thích mọi môi trường không cần cài thêm thư viện mã hóa nặng)"""
    return hashlib.sha256((password + SECRET_KEY).encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

class LoginPayload(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    """Đăng nhập mạng nội bộ dành cho Cán bộ / Thủ kho / Lãnh đạo"""
    user = db.query(User).filter(User.username == payload.username.strip()).first()
    
    # Nếu chưa có tài khoản trong DB, cho phép nạp tài khoản mặc định
    if not user:
        if payload.username == "admin" and payload.password == "admin123":
            user = User(username="admin", hashed_password=hash_password("admin123"), full_name="Trưởng Đoàn Nghi Lễ CAND", role="admin", department="Ban Chỉ Huy Đoàn")
            db.add(user)
            db.commit()
            db.refresh(user)
        elif payload.username == "thukho" and payload.password == "thukho123":
            user = User(username="thukho", hashed_password=hash_password("thukho123"), full_name="Thủ Kho Kỹ Thuật Vật Tư", role="storekeeper", department="Kho Kỹ Thuật")
            db.add(user)
            db.commit()
            db.refresh(user)
        elif payload.username == "canbo" and payload.password == "canbo123":
            user = User(username="canbo", hashed_password=hash_password("canbo123"), full_name="Cán Bộ Đội Nghi Lễ", role="user", department="Đội Nghi Lễ CAND")
            db.add(user)
            db.commit()
            db.refresh(user)

    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        log_audit(db, "guest", "ĐĂNG NHẬP THẤT BẠI", payload.username, "Mật khẩu không chính xác")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu nội bộ không chính xác."
        )

    log_audit(db, user.role, "ĐĂNG NHẬP THÀNH CÔNG", user.username, f"Cán bộ: {user.full_name}")

    return {
        "success": True,
        "message": f"Xin chào {user.full_name} ({user.username})!",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department
        }
    }

@router.post("/seed-users")
def seed_users(db: Session = Depends(get_db)):
    """Nạp sẵn 3 tài khoản mẫu bảo mật mạng nội bộ"""
    users_data = [
        ("admin", "admin123", "Trưởng Đoàn Nghi Lễ CAND", "admin", "Ban Chỉ Huy Đoàn"),
        ("thukho", "thukho123", "Thượng úy Trần Văn B (Thủ Kho)", "storekeeper", "Kho Kỹ Thuật"),
        ("canbo", "canbo123", "Đại úy Phạm Văn C (Cán Bộ)", "user", "Đội Kỹ Thuật & Trang Bị")
    ]
    
    created = []
    for un, pw, fn, rl, dp in users_data:
        existing = db.query(User).filter(User.username == un).first()
        if not existing:
            u = User(username=un, hashed_password=hash_password(pw), full_name=fn, role=rl, department=dp)
            db.add(u)
            created.append(un)
        else:
            existing.hashed_password = hash_password(pw)
            existing.full_name = fn
            existing.role = rl
            existing.department = dp
            created.append(f"{un} (updated)")
            
    db.commit()
    return {"success": True, "seeded": created}
