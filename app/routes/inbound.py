import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Item, Asset, InboundReceipt, InboundDetail, AssetHistory, log_audit
from app.schemas import InboundCreatePayload
from app.services.qr_pdf_maker import generate_qr_decal_pdf

router = APIRouter(prefix="/api/inbound", tags=["Inbound Batch & Assets"])

EXPORTS_DIR = os.path.join(os.getcwd(), "exports")

def check_storekeeper_role(x_user_role: str = Header("admin")):
    if x_user_role and x_user_role.lower() not in ["admin", "storekeeper"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Thao tác nhập kho yêu cầu quyền Thủ kho hoặc Admin."
        )
    return x_user_role

@router.post("")
def create_inbound_receipt(
    payload: InboundCreatePayload,
    db: Session = Depends(get_db),
    role: str = Depends(check_storekeeper_role)
):
    """
    Lập Phiếu Nhập Kho Theo Lô:
    - Vật tư tiêu hao: Cộng dồn tồn kho tổng.
    - Tài sản cố định: Sinh mã QR định danh độc lập (TS-0001, TS-0002...) gắn với Số Serial/MAC.
    """
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phiếu nhập kho phải chứa ít nhất 1 vật tư."
        )

    # 1. Sinh Mã Phiếu Nhập Kho (PNK-...)
    receipt_count = db.query(InboundReceipt).count() + 1
    receipt_code = f"PNK-{receipt_count:04d}"

    receipt = InboundReceipt(
        receipt_code=receipt_code,
        source=payload.source or "Cục cấp",
        supplier_or_unit=payload.supplier_or_unit or "Đơn vị cấp",
        created_by=payload.created_by or "Thủ kho",
        status="completed"
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)

    total_items_added = 0
    created_asset_codes = []

    # 2. Xử lý từng dòng vật tư
    for detail in payload.items:
        # Tìm hoặc tạo Item trong danh mục
        item = db.query(Item).filter(Item.item_code == detail.item_code).first()
        if not item:
            item = Item(
                item_code=detail.item_code,
                name=detail.name,
                unit=detail.unit,
                category=detail.category,
                current_stock=0,
                location=payload.location or "Kho Kỹ Thuật"
            )
            db.add(item)
            db.commit()
            db.refresh(item)

        # Cộng dồn tồn kho
        item.current_stock += detail.quantity
        total_items_added += detail.quantity

        # Ghi nhận chi tiết phiếu nhập
        inbound_detail = InboundDetail(
            receipt_id=receipt.id,
            item_id=item.id,
            quantity=detail.quantity,
            unit_price=detail.unit_price
        )
        db.add(inbound_detail)

        # Nếu là Tài sản cố định (fixed_asset): Sinh từng bản ghi Asset độc lập với mã QR TS-xxxx
        if detail.category == "fixed_asset":
            serials = detail.serial_numbers or []
            for i in range(detail.quantity):
                serial_no = serials[i] if i < len(serials) else f"SN-{item.item_code}-{datetime.now().strftime('%M%S')}{i+1}"
                
                asset_count = db.query(Asset).count() + 1
                asset_code = f"TS-{asset_count:04d}"

                asset = Asset(
                    asset_code=asset_code,
                    item_id=item.id,
                    serial_number=serial_no,
                    status="available",
                    location=payload.location or "Kho Kỹ Thuật",
                    inbound_receipt_id=receipt.id
                )
                db.add(asset)
                db.commit()
                db.refresh(asset)

                created_asset_codes.append({"code": asset_code, "name": item.name, "serial": serial_no})

                # Thẻ Kho dấu vết
                history = AssetHistory(
                    item_id=item.id,
                    asset_id=asset.id,
                    action_type="inbound",
                    performer=payload.created_by or "Thủ kho",
                    details=f"Nhập mới kho theo phiếu {receipt_code} từ nguồn {receipt.source} (Serial: {serial_no})"
                )
                db.add(history)
        else:
            # Thẻ Kho dấu vết cho vật tư tiêu hao
            history = AssetHistory(
                item_id=item.id,
                action_type="inbound",
                performer=payload.created_by or "Thủ kho",
                details=f"Nhập thêm {detail.quantity} {item.unit} theo phiếu {receipt_code} từ nguồn {receipt.source}"
            )
            db.add(history)

    db.commit()
    log_audit(db, role, "NHẬP KHO LÔ HÀNG", receipt_code, f"Nhập kho thành công {total_items_added} sản phẩm từ {receipt.source}")

    return {
        "success": True,
        "message": f"Đã lập phiếu nhập kho {receipt_code} thành công!",
        "receipt_id": receipt.id,
        "receipt_code": receipt_code,
        "total_quantity": total_items_added,
        "created_assets": created_asset_codes
    }

@router.get("/receipts")
def get_inbound_receipts(db: Session = Depends(get_db)):
    receipts = db.query(InboundReceipt).order_by(InboundReceipt.id.desc()).all()
    return [
        {
            "id": r.id,
            "receipt_code": r.receipt_code,
            "source": r.source,
            "supplier_or_unit": r.supplier_or_unit,
            "created_by": r.created_by,
            "created_at": r.created_at.isoformat(),
            "items_count": sum(d.quantity for d in r.details)
        } for r in receipts
    ]

@router.get("/export-qr-pdf/{receipt_id}")
def export_inbound_qr_pdf(receipt_id: int, db: Session = Depends(get_db)):
    receipt = db.query(InboundReceipt).filter(InboundReceipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy phiếu nhập kho #{receipt_id}"
        )

    # Lấy danh sách tem QR của đợt nhập
    qr_items = []
    for asset in receipt.assets:
        qr_items.append({
            "item_code": asset.asset_code,
            "name": asset.item.name if asset.item else "Tài sản",
            "unit": f"Serial: {asset.serial_number or 'N/A'}"
        })

    if not qr_items:
        # Nếu không có asset, lấy item tiêu hao
        for detail in receipt.details:
            if detail.item:
                qr_items.append({
                    "item_code": detail.item.item_code,
                    "name": detail.item.name,
                    "unit": detail.item.unit
                })

    pdf_path = generate_qr_decal_pdf(qr_items)
    return FileResponse(
        path=pdf_path,
        filename=f"tem_qr_lo_nhap_{receipt.receipt_code}.pdf",
        media_type="application/pdf"
    )
