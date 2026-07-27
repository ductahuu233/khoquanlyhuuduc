from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
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
    
    # New V3 Fields
    category = Column(String, default="consumable")  # consumable (tiêu hao) | fixed_asset (tài sản cố định)
    min_stock_alert = Column(Integer, default=5)     # Ngưỡng tồn kho tối thiểu cảnh báo đỏ
    location = Column(String, default="Kho Kỹ Thuật") # Kho Kỹ Thuật, Kho Văn Phòng Phẩm, Kho Phế Phẩm

    request_details = relationship("RequestDetail", back_populates="item")
    transactions = relationship("Transaction", back_populates="item")
    assets = relationship("Asset", back_populates="item")
    history_records = relationship("AssetHistory", back_populates="item")

class Asset(Base):
    """Bảng quản lý từng thiết bị/tài sản cố định độc lập có mã Serial/MAC và tem QR riêng"""
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_code = Column(String, unique=True, index=True, nullable=False) # Mã tem QR: TS-0001, TS-0002...
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    serial_number = Column(String, nullable=True, index=True)
    mac_address = Column(String, nullable=True)
    status = Column(String, default="available") # available (Trong kho), in_use (Đang dùng), maintenance (Bảo hành), damaged (Hỏng), disposed (Thanh lý)
    assigned_to = Column(String, nullable=True)  # Cán bộ / Đội quản lý sử dụng
    location = Column(String, default="Kho Kỹ Thuật")
    inbound_receipt_id = Column(Integer, ForeignKey("inbound_receipts.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    item = relationship("Item", back_populates="assets")
    inbound_receipt = relationship("InboundReceipt", back_populates="assets")
    history_records = relationship("AssetHistory", back_populates="asset")

class InboundReceipt(Base):
    """Phiếu Nhập Kho Theo Lô"""
    __tablename__ = "inbound_receipts"

    id = Column(Integer, primary_key=True, index=True)
    receipt_code = Column(String, unique=True, index=True, nullable=False) # PNK-001
    source = Column(String, default="Cục cấp") # Cục cấp, Mua sắm nội bộ, Biếu tặng
    supplier_or_unit = Column(String, nullable=True)
    created_by = Column(String, default="Thủ kho")
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=utc_now)

    details = relationship("InboundDetail", back_populates="receipt", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="inbound_receipt")

class InboundDetail(Base):
    __tablename__ = "inbound_details"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("inbound_receipts.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, default=0.0)

    receipt = relationship("InboundReceipt", back_populates="details")
    item = relationship("Item")

class AssetHistory(Base):
    """Thẻ Kho Dấu Vết Vòng Đời Tài Sản"""
    __tablename__ = "asset_history"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    action_type = Column(String, nullable=False) # inbound, export, transfer, damaged, recover, disposed
    performer = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now)

    item = relationship("Item", back_populates="history_records")
    asset = relationship("Asset", back_populates="history_records")

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

class AuditSheet(Base):
    """Phiếu Kiểm Kê Kho Định Kỳ"""
    __tablename__ = "audit_sheets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    inspector_name = Column(String, nullable=False)
    location = Column(String, default="Kho Kỹ Thuật")
    status = Column(String, default="completed") # draft, completed
    scanned_count = Column(Integer, default=0)
    expected_count = Column(Integer, default=0)
    discrepancy_details = Column(Text, nullable=True) # JSON lưu chi tiết chênh lệch thừa/thiếu
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
