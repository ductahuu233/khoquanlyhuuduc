import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Item, RequestDetail, Transaction, log_audit
from app.schemas import ItemCreate, ItemUpdate, ItemResponse
from app.services.qr_pdf_maker import generate_qr_decal_pdf

router = APIRouter(prefix="/api/items", tags=["Items"])

UPLOADS_DIR = os.path.join(os.getcwd(), "uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg"}

def check_admin_role(x_user_role: Optional[str] = Header("admin")):
    if x_user_role and x_user_role.lower() not in ["admin", "storekeeper"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền quản trị để thực hiện thao tác này (Chỉ dành cho Admin)."
        )
    return x_user_role

def validate_image_url(url: Optional[str]):
    if not url:
        return
    url_str = url.strip().lower()
    if not (url_str.startswith("http://") or url_str.startswith("https://") or url_str.startswith("/uploads/")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LỖI ĐỊNH DẠNG: Đường dẫn hình ảnh không hợp lệ (Phải bắt đầu bằng http://, https:// hoặc /uploads/). Vui lòng chọn lại ảnh!"
        )

@router.post("/upload-image")
def upload_item_image(
    file: UploadFile = File(...)
):
    if not os.path.exists(UPLOADS_DIR):
        os.makedirs(UPLOADS_DIR, exist_ok=True)

    # 1. Check Content-Type header
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LỖI ĐỊNH DẠNG: Tập tin được chọn không phải là hình ảnh (Chỉ chấp nhận JPG, PNG, WEBP, GIF). Vui lòng chọn lại ảnh!"
        )
    
    # 2. Check File Extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LỖI ĐỊNH DẠNG: Đuôi file '{ext}' không hợp lệ. Vui lòng chọn file ảnh (JPG, PNG, WEBP, GIF, SVG, BMP)."
        )
    
    filename = f"img_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOADS_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"url": f"/uploads/{filename}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lưu hình ảnh lên máy tính/server: {e}"
        )

@router.get("/export-qr-pdf")
def export_qr_pdf(
    db: Session = Depends(get_db),
    role: str = Depends(check_admin_role)
):
    items = db.query(Item).all()
    items_data = [
        {
            "item_code": item.item_code,
            "name": item.name,
            "unit": item.unit
        } for item in items
    ]
    pdf_path = generate_qr_decal_pdf(items_data)
    log_audit(db, role, "IN TEM DECAL QR", "Bộ Tem QR A4", f"Sinh file PDF A4 chứa {len(items)} tem QR Decal")
    return FileResponse(
        path=pdf_path, 
        filename="tem_nhan_ma_qr_A4.pdf",
        media_type="application/pdf"
    )

@router.get("", response_model=List[ItemResponse])
def get_items(
    search: Optional[str] = Query(None, description="Tìm kiếm theo mã hoặc tên vật tư"),
    db: Session = Depends(get_db)
):
    query = db.query(Item)
    if search:
        query = query.filter(
            (Item.item_code.ilike(f"%{search}%")) | (Item.name.ilike(f"%{search}%"))
        )
    return query.all()

@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_in: ItemCreate, 
    db: Session = Depends(get_db),
    role: str = Depends(check_admin_role)
):
    existing = db.query(Item).filter(Item.item_code == item_in.item_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã vật tư '{item_in.item_code}' đã tồn tại trong hệ thống."
        )
    
    validate_image_url(item_in.image_url)

    db_item = Item(
        item_code=item_in.item_code,
        name=item_in.name,
        unit=item_in.unit,
        current_stock=item_in.current_stock,
        image_url=item_in.image_url
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    log_audit(db, role, "THÊM VẬT TƯ MỚI", db_item.item_code, f"Khởi tạo vật tư '{db_item.name}' số lượng ban đầu {db_item.current_stock} {db_item.unit}")
    return db_item

@router.get("/scan/{item_code}", response_model=ItemResponse)
def scan_item(item_code: str, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.item_code.ilike(item_code)).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vật tư có mã '{item_code}' trong kho."
        )
    return item

@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vật tư có ID {item_id}"
        )
    return item

@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int, 
    item_in: ItemUpdate, 
    db: Session = Depends(get_db),
    role: str = Depends(check_admin_role)
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vật tư có ID {item_id}"
        )
    
    if item_in.image_url is not None:
        validate_image_url(item_in.image_url)

    if item_in.name is not None:
        item.name = item_in.name
    if item_in.unit is not None:
        item.unit = item_in.unit
    if item_in.current_stock is not None:
        item.current_stock = item_in.current_stock
    if item_in.image_url is not None:
        item.image_url = item_in.image_url

    db.commit()
    db.refresh(item)
    log_audit(db, role, "SỬA VẬT TƯ", item.item_code, f"Cập nhật thông tin vật tư '{item.name}' tồn kho {item.current_stock} {item.unit}")
    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int, 
    db: Session = Depends(get_db),
    role: str = Depends(check_admin_role)
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vật tư có ID {item_id}"
        )
    
    code = item.item_code
    name = item.name

    # Delete child dependencies in RequestDetail and Transaction first to ensure deletion always succeeds
    db.query(RequestDetail).filter(RequestDetail.item_id == item_id).delete(synchronize_session=False)
    db.query(Transaction).filter(Transaction.item_id == item_id).delete(synchronize_session=False)

    db.delete(item)
    db.commit()
    log_audit(db, role, "XÓA VẬT TƯ", code, f"Xóa hoàn toàn vật tư '{name}' khỏi hệ thống kho")
    return None
