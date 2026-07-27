import sys
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime
from app.database import SessionLocal
from app.models import Request
from app.services.word_maker import generate_word

def force_regenerate_all():
    print("=== REGENERATING ALL EXISTING WORD DOCUMENTS ===")
    db = SessionLocal()
    requests = db.query(Request).all()

    for req in requests:
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

        path = generate_word(export_data)
        print(f"✅ Successfully regenerated Word file for Request #{req.id}: {path}")

    db.close()
    print("=== REGENERATION COMPLETE ===")

if __name__ == "__main__":
    force_regenerate_all()
