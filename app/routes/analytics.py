from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Item, Request, Transaction

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/dashboard")
def get_dashboard_analytics(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    requests = db.query(Request).all()

    total_items = len(items)
    total_stock = sum(i.current_stock for i in items)
    low_stock_items = [i for i in items if i.current_stock < 10]
    pending_requests = [r for r in requests if r.status == "pending"]
    exported_requests = [r for r in requests if r.status == "exported"]

    # Items Breakdown for Chart.js
    items_breakdown = [
        {
            "code": i.item_code,
            "name": i.name,
            "stock": i.current_stock,
            "unit": i.unit
        } for i in items
    ]

    # Calculate 30-day export velocity & AI Predictive Alerts
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    recent_transactions = db.query(Transaction).filter(
        Transaction.timestamp >= thirty_days_ago,
        Transaction.type == "export"
    ).all()

    # Sum exports per item
    item_export_sums = {}
    for tx in recent_transactions:
        item_export_sums[tx.item_id] = item_export_sums.get(tx.item_id, 0) + tx.quantity

    predictive_alerts = []
    for i in items:
        exported_qty = item_export_sums.get(i.id, 0)
        daily_avg = exported_qty / 30.0

        if daily_avg > 0:
            days_left = int(i.current_stock / daily_avg)
            if days_left <= 14 or i.current_stock < 10:
                predictive_alerts.append({
                    "item_code": i.item_code,
                    "name": i.name,
                    "current_stock": i.current_stock,
                    "unit": i.unit,
                    "daily_avg": round(daily_avg, 1),
                    "days_remaining": days_left,
                    "severity": "danger" if days_left <= 7 else "warning",
                    "message": f"🔴 CẢNH BÁO AI: Vật tư '{i.name}' dự kiến sẽ hết hàng trong khoảng {days_left} ngày tới dựa trên tốc độ xuất kho trung bình {round(daily_avg, 1)} {i.unit}/ngày. Đề xuất Lãnh đạo lập kế hoạch mua sắm bổ sung khẩn cấp!"
                })
        elif i.current_stock < 10:
            predictive_alerts.append({
                "item_code": i.item_code,
                "name": i.name,
                "current_stock": i.current_stock,
                "unit": i.unit,
                "daily_avg": 0,
                "days_remaining": 0,
                "severity": "warning",
                "message": f"🟡 CẢNH BÁO TỒN KHO: Vật tư '{i.name}' đang chạm ngưỡng sắp hết (Tồn kho hiện tại: {i.current_stock} {i.unit}). Vui lòng nhập thêm hàng!"
            })

    return {
        "summary": {
            "total_items": total_items,
            "total_stock": total_stock,
            "low_stock_count": len(low_stock_items),
            "pending_requests_count": len(pending_requests),
            "exported_requests_count": len(exported_requests)
        },
        "items_breakdown": items_breakdown,
        "predictive_alerts": predictive_alerts
    }
