from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Session
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="storekeeper")  # admin, storekeeper, approver

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    current_stock = Column(Integer, default=0, nullable=False)
    image_url = Column(String, nullable=True)

    request_details = relationship("RequestDetail", back_populates="item")
    transactions = relationship("Transaction", back_populates="item")

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_name = Column(String, nullable=False)
    destination = Column(String, nullable=True)  # Xuất đi đâu / Nơi nhận
    reason = Column(String, nullable=True)       # Lý do / Mục đích xuất kho
    status = Column(String, default="pending")   # pending, approved, exported
    created_at = Column(DateTime, default=utc_now)

    # Lịch sử file báo cáo đã xuất kho
    pdf_path = Column(String, nullable=True)
    excel_path = Column(String, nullable=True)
    word_path = Column(String, nullable=True)
    exported_at = Column(DateTime, nullable=True)

    details = relationship("RequestDetail", back_populates="request", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="request")

class RequestDetail(Base):
    __tablename__ = "request_details"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    request = relationship("Request", back_populates="details")
    item = relationship("Item", back_populates="request_details")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=True)
    type = Column(String, nullable=False)  # export, import
    quantity = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=utc_now)

    item = relationship("Item", back_populates="transactions")
    request = relationship("Request", back_populates="transactions")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_role = Column(String, default="admin")
    action = Column(String, nullable=False)  # THÊM VẬT TƯ, XUẤT KHO, SỬA FILE, XÓA...
    target = Column(String, nullable=False)  # Tên/Mã đối tượng
    details = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

def log_audit(db: Session, user_role: str, action: str, target: str, details: str = None):
    try:
        log = AuditLog(
            user_role=user_role or "admin",
            action=action,
            target=target,
            details=details
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Error writing audit log: {e}")
