from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuditLog, Item, Request

router = APIRouter(prefix="/api/audit", tags=["Audit & Security Logs"])

@router.get("/logs")
def get_audit_logs(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    return [
        {
            "id": log.id,
            "user_role": log.user_role,
            "action": log.action,
            "target": log.target,
            "details": log.details,
            "created_at": log.created_at.isoformat()
        } for log in logs
    ]

@router.get("/alerts")
def get_urgent_alerts(db: Session = Depends(get_db)):
    pending_requests = db.query(Request).filter(Request.status == "pending").all()
    low_stock_items = db.query(Item).filter(Item.current_stock < 10).all()

    alerts_list = []
    
    for r in pending_requests:
        alerts_list.append({
            "type": "pending_request",
            "title": f"Phiếu #{r.id} đang chờ phê duyệt xuất kho",
            "subtitle": f"Cán bộ: {r.requester_name} ➔ Nơi nhận: {r.destination or 'N/A'}",
            "time": r.created_at.isoformat(),
            "target_tab": "tab-export"
        })

    for i in low_stock_items:
        alerts_list.append({
            "type": "low_stock",
            "title": f"Vật tư '{i.name}' ({i.item_code}) chạm ngưỡng cảnh báo tồn",
            "subtitle": f"Tồn kho còn: {i.current_stock} {i.unit}",
            "time": None,
            "target_tab": "tab-inventory"
        })

    total_count = len(pending_requests) + len(low_stock_items)

    return {
        "total_urgent_count": total_count,
        "pending_requests_count": len(pending_requests),
        "low_stock_count": len(low_stock_items),
        "alerts": alerts_list
    }
