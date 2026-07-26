import sys
import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import Item, Request, Transaction

client = TestClient(app)

def test_phase4_export_flow():
    print("=== STARTING PHASE 4 EXPORT INTEGRATION FLOW TEST ===")

    # 1. Reset Database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 2. Add Test Items
    print("1. Creating Items for test...")
    res_i1 = client.post("/api/items", json={
        "item_code": "VT-001",
        "name": "Giấy A4 Double A 80gsm",
        "unit": "Ram",
        "current_stock": 20
    })
    item1_id = res_i1.json()["id"]

    res_i2 = client.post("/api/items", json={
        "item_code": "VT-002",
        "name": "Bút bi Thiên Long xanh",
        "unit": "Hộp",
        "current_stock": 5
    })
    item2_id = res_i2.json()["id"]
    print("   [PASS] Created VT-001 (Stock: 20) and VT-002 (Stock: 5).")

    # 3. Create Export Request
    print("2. Creating Export Request...")
    res_req = client.post("/api/requests", json={
        "requester_name": "Kỹ sư Lê Văn C",
        "items": [
            {"item_id": item1_id, "quantity": 10},
            {"item_id": item2_id, "quantity": 3}
        ]
    })
    req_id = res_req.json()["id"]
    print(f"   [PASS] Request #{req_id} created.")

    # 4. Execute Export API POST /api/export
    print("3. Executing POST /api/export (Core Logic)...")
    res_export = client.post("/api/export", json={"request_id": req_id})
    assert res_export.status_code == 200, f"Export failed: {res_export.text}"
    exp_data = res_export.json()

    assert exp_data["success"] is True
    assert exp_data["status"] == "exported"
    assert "pdf" in exp_data["files"]
    assert "excel" in exp_data["files"]
    assert "word" in exp_data["files"]
    print(f"   [PASS] Export API returned success with file links:")
    print(f"          PDF  : {exp_data['files']['pdf']}")
    print(f"          Excel: {exp_data['files']['excel']}")
    print(f"          Word : {exp_data['files']['word']}")

    # 5. Verify Database State
    print("4. Verifying DB State (Stock deduction & Transactions)...")
    db = SessionLocal()
    i1 = db.query(Item).filter(Item.id == item1_id).first()
    i2 = db.query(Item).filter(Item.id == item2_id).first()
    assert i1.current_stock == 10, f"Expected stock 10, got {i1.current_stock}"
    assert i2.current_stock == 2, f"Expected stock 2, got {i2.current_stock}"
    print(f"   [PASS] Stock updated: VT-001 = {i1.current_stock}, VT-002 = {i2.current_stock}")

    trans_list = db.query(Transaction).filter(Transaction.request_id == req_id).all()
    assert len(trans_list) == 2
    print(f"   [PASS] {len(trans_list)} transaction log records created in DB.")
    db.close()

    # 6. Test Download API
    print("5. Testing GET /api/download/{filename}...")
    pdf_filename = os.path.basename(exp_data['files']['pdf'])
    res_dl = client.get(f"/api/download/{pdf_filename}")
    assert res_dl.status_code == 200
    assert len(res_dl.content) > 0
    print("   [PASS] Download endpoint correctly returned PDF file bytes.")

    # 7. Test Insufficient Stock Handling
    print("6. Testing Insufficient Stock Rejection...")
    res_req2 = client.post("/api/requests", json={
        "requester_name": "Thủ kho D",
        "items": [
            {"item_id": item2_id, "quantity": 10}  # Stock is only 2!
        ]
    })
    req2_id = res_req2.json()["id"]

    res_fail = client.post("/api/export", json={"request_id": req2_id})
    assert res_fail.status_code == 400
    assert "Không đủ tồn kho" in res_fail.json()["detail"]
    print("   [PASS] Insufficient stock correctly rejected with HTTP 400.")

    # 8. Test Re-export Prevention
    print("7. Testing Re-export Prevention...")
    res_re = client.post("/api/export", json={"request_id": req_id})
    assert res_re.status_code == 400
    assert "đã được thực thi xuất kho trước đó" in res_re.json()["detail"]
    print("   [PASS] Duplicate export call correctly rejected with HTTP 400.")

    print("\n=== PHASE 4 TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    try:
        test_phase4_export_flow()
    except Exception as e:
        print(f"\n[FAIL] Phase 4 test failed: {e}")
        sys.exit(1)
