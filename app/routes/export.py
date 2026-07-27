import os
import time
import zipfile
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Request, Item, Transaction, log_audit
from app.services.pdf_maker import generate_pdf
from app.services.excel_maker import generate_excel
from app.services.word_maker import generate_word
from app.services.inventory_audit_maker import generate_inventory_audit_pdf
from pydantic import BaseModel

router = APIRouter(tags=["Export"])

def check_admin_role(x_user_role: Optional[str] = Header("admin")):
    if x_user_role and x_user_role.lower() not in ["admin", "storekeeper"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Thao tác xuất kho yêu cầu quyền Admin hoặc Thủ Kho."
        )
    return x_user_role

class ExportExecutePayload(BaseModel):
    request_id: int

EXPORTS_DIR = os.path.join(os.getcwd(), "exports")

@router.get("/api/export/audit-pdf")
def export_audit_pdf(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    items_data = [
        {
            "item_code": i.item_code,
            "name": i.name,
            "unit": i.unit,
            "current_stock": i.current_stock
        } for i in items
    ]
    pdf_path = generate_inventory_audit_pdf(items_data)
    log_audit(db, "admin", "IN BIÊN BẢN KIỂM KÊ", "Biên Bản Kiểm Kê Tồn Kho A4", f"Xuất báo cáo kiểm kê {len(items)} vật tư")
    return FileResponse(
        path=pdf_path,
        filename=f"bien_ban_kiem_ke_kho_{datetime.now().strftime('%Y%m%d')}.pdf",
        media_type="application/pdf"
    )

@router.get("/api/export/history/{request_id}/zip")
def download_request_zip(
    request_id: int,
    db: Session = Depends(get_db)
):
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req or req.status != "exported":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phiếu xuất kho #{request_id} chưa được xuất kho hoặc không tồn tại."
        )

    zip_filename = f"HoSo_XuatKho_PXK_{req.id}.zip"
    zip_path = os.path.join(EXPORTS_DIR, zip_filename)

    # Re-generate word before compressing to guarantee latest Decree 30 format
    try:
        export_items_list = [
            {
                "item_code": d.item.item_code if d.item else f"VT-{d.item_id}",
                "name": d.item.name if d.item else "Vật tư",
                "unit": d.item.unit if d.item else "Cái",
                "quantity": d.quantity
            } for d in req.details
        ]
        export_data = {
            "request_id": req.id,
            "requester_name": req.requester_name,
            "destination": req.destination or "Đơn vị tiếp nhận",
            "reason": req.reason or "Phục vụ công tác chuyên môn",
            "export_date": (req.exported_at or datetime.now()).strftime("%d/%m/%Y"),
            "items": export_items_list
        }
        generate_word(export_data)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for attr in ['pdf_path', 'excel_path', 'word_path']:
                path_val = getattr(req, attr)
                if path_val:
                    actual_filename = os.path.basename(path_val.split('?')[0])
                    actual_filepath = os.path.join(EXPORTS_DIR, actual_filename)
                    if os.path.exists(actual_filepath):
                        zipf.write(actual_filepath, arcname=actual_filename)
        
        log_audit(db, "admin", "TẢI FILE ZIP HỒ SƠ", f"#PXK-{req.id}", f"Nén & Tải bộ 3 file hồ sơ xuất kho #{req.id}")
        return FileResponse(path=zip_path, filename=zip_filename, media_type="application/zip")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi đóng gói file ZIP: {e}"
        )

@router.post("/api/export")
def execute_export(
    payload: ExportExecutePayload, 
    db: Session = Depends(get_db),
    role: str = Depends(check_admin_role)
):
    request_id = payload.request_id

    # 1. Fetch Request
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy phiếu xuất kho ID #{request_id}"
        )
    
    if req.status == "exported":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phiếu xuất kho #{request_id} đã được thực thi xuất kho trước đó."
        )

    if not req.details:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phiếu xuất kho #{request_id} không có chi tiết vật tư."
        )

    # 2. Check stock sufficiency for all items in transaction
    for detail in req.details:
        item = detail.item
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vật tư ID {detail.item_id} không còn tồn tại."
            )
        if item.current_stock < detail.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không đủ tồn kho cho vật tư '{item.name}' (Mã: {item.item_code}). Tồn kho hiện tại: {item.current_stock}, Cần xuất: {detail.quantity}"
            )

    # 3. Database Transaction: Deduct stock & create Transaction log
    try:
        export_items_list = []
        for detail in req.details:
            item = detail.item
            # Deduct stock
            item.current_stock -= detail.quantity
            
            # Log transaction
            trans = Transaction(
                request_id=req.id,
                item_id=item.id,
                type="export",
                quantity=detail.quantity
            )
            db.add(trans)

            export_items_list.append({
                "item_code": item.item_code,
                "name": item.name,
                "unit": item.unit,
                "quantity": detail.quantity
            })

        # Update Request Status
        req.status = "exported"
        req.exported_at = datetime.now()
        db.commit()
        db.refresh(req)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi cơ sở dữ liệu khi trừ tồn kho: {e}"
        )

    # 4. Generate PDF, Excel, and Word files
    export_data = {
        "request_id": req.id,
        "requester_name": req.requester_name,
        "destination": req.destination or "Đơn vị tiếp nhận",
        "reason": req.reason or "Phục vụ công tác chuyên môn",
        "export_date": req.exported_at.strftime("%d/%m/%Y"),
        "items": export_items_list
    }

    try:
        pdf_path = generate_pdf(export_data)
        excel_path = generate_excel(export_data)
        word_path = generate_word(export_data)

        ts = int(time.time())
        req.pdf_path = f"/api/download/{os.path.basename(pdf_path)}?t={ts}"
        req.excel_path = f"/api/download/{os.path.basename(excel_path)}?t={ts}"
        req.word_path = f"/api/download/{os.path.basename(word_path)}?t={ts}"
        db.commit()

        log_audit(db, role, "DUYỆT XUẤT KHO", f"#PXK-{req.id}", f"Xuất kho thành công cho cán bộ '{req.requester_name}' - Đơn vị nhận '{req.destination}'")

        return {
            "success": True,
            "message": f"Đã phê duyệt xuất kho & tự động tạo bộ 3 file (PDF, Excel, Word) thành công!",
            "request_id": req.id,
            "requester_name": req.requester_name,
            "files": {
                "pdf": req.pdf_path,
                "excel": req.excel_path,
                "word": req.word_path
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tự động tạo bộ 3 file báo cáo: {e}"
        )

@router.get("/api/export/history")
def get_export_history(db: Session = Depends(get_db)):
    exported_requests = db.query(Request).filter(Request.status == "exported").order_by(Request.exported_at.desc()).all()
    ts = int(time.time())
    return [
        {
            "id": req.id,
            "requester_name": req.requester_name,
            "destination": req.destination,
            "reason": req.reason,
            "exported_at": req.exported_at.isoformat() if req.exported_at else req.created_at.isoformat(),
            "files": {
                "pdf": f"/api/download/phieu_xuat_kho_{req.id}.pdf?t={ts}",
                "excel": f"/api/download/so_nhat_ky_xuat_kho_{req.id}.xlsx?t={ts}",
                "word": f"/api/download/to_trinh_xuat_kho_{req.id}.docx?t={ts}"
            }
        } for req in exported_requests
    ]

class RequestEditPayload(BaseModel):
    requester_name: Optional[str] = None
    destination: Optional[str] = None
    reason: Optional[str] = None

@router.put("/api/export/history/{request_id}")
def edit_and_regenerate_export(
    request_id: int,
    payload: RequestEditPayload,
    db: Session = Depends(get_db),
    role: str = Depends(check_admin_role)
):
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy phiếu xuất kho ID #{request_id}"
        )

    if payload.requester_name is not None:
        req.requester_name = payload.requester_name
    if payload.destination is not None:
        req.destination = payload.destination
    if payload.reason is not None:
        req.reason = payload.reason

    db.commit()
    db.refresh(req)

    # Re-generate all 3 report files with corrected info
    export_items_list = [
        {
            "item_code": d.item.item_code if d.item else f"VT-{d.item_id}",
            "name": d.item.name if d.item else "Vật tư",
            "unit": d.item.unit if d.item else "Cái",
            "quantity": d.quantity
        } for d in req.details
    ]

    export_data = {
        "request_id": req.id,
        "requester_name": req.requester_name,
        "destination": req.destination or "Đơn vị tiếp nhận",
        "reason": req.reason or "Phục vụ công tác chuyên môn",
        "export_date": (req.exported_at or datetime.now()).strftime("%d/%m/%Y"),
        "items": export_items_list
    }

    try:
        pdf_path = generate_pdf(export_data)
        excel_path = generate_excel(export_data)
        word_path = generate_word(export_data)

        ts = int(time.time())
        req.pdf_path = f"/api/download/{os.path.basename(pdf_path)}?t={ts}"
        req.excel_path = f"/api/download/{os.path.basename(excel_path)}?t={ts}"
        req.word_path = f"/api/download/{os.path.basename(word_path)}?t={ts}"
        db.commit()

        log_audit(db, role, "SỬA FILE BÁO CÁO", f"#PXK-{req.id}", f"Cập nhật lại thông tin phiếu #{req.id} & tự động tạo lại bộ 3 file")

        return {
            "success": True,
            "message": "Đã cập nhật thông tin và tự động tạo lại bộ 3 file báo cáo mới thành công!",
            "request_id": req.id,
            "files": {
                "pdf": req.pdf_path,
                "excel": req.excel_path,
                "word": req.word_path
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tạo lại file báo cáo: {e}"
        )

@router.get("/api/download/{filename}")
def download_file(filename: str, db: Session = Depends(get_db)):
    actual_filename = filename.split('?')[0]
    file_path = os.path.join(EXPORTS_DIR, actual_filename)

    # Auto-regenerate Word document dynamically on download to guarantee 100% Decree 30 formatting
    if actual_filename.startswith("to_trinh_xuat_kho_") and actual_filename.endswith(".docx"):
        try:
            req_id_str = actual_filename.replace("to_trinh_xuat_kho_", "").replace(".docx", "")
            req_id = int(req_id_str)
            req = db.query(Request).filter(Request.id == req_id).first()
            if req:
                export_items_list = [
                    {
                        "item_code": d.item.item_code if d.item else f"VT-{d.item_id}",
                        "name": d.item.name if d.item else "Vật tư",
                        "unit": d.item.unit if d.item else "Cái",
                        "quantity": d.quantity
                    } for d in req.details
                ]
                export_data = {
                    "request_id": req.id,
                    "requester_name": req.requester_name,
                    "destination": req.destination or "Đơn vị tiếp nhận",
                    "reason": req.reason or "Phục vụ công tác chuyên môn",
                    "export_date": (req.exported_at or datetime.now()).strftime("%d/%m/%Y"),
                    "items": export_items_list
                }
                generate_word(export_data)
        except Exception as e:
            print("Auto-regenerate word error:", e)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{actual_filename}' không tồn tại hoặc đã bị xóa."
        )

    return FileResponse(
        path=file_path,
        filename=actual_filename,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )
