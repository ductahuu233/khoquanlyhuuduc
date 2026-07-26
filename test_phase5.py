import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_phase5_ui_and_e2e():
    print("=== STARTING PHASE 5 MVP UI & E2E INTEGRATION TEST ===")

    # 1. Test Root UI Route
    print("1. Testing GET / (UI index.html)...")
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "Hệ Thống Quản Lý Kho Nội Bộ" in res_root.text
    print("   [PASS] GET / correctly served static/index.html UI page.")

    # 2. Test Health Route
    print("2. Testing GET /health...")
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"
    print("   [PASS] System health check passed.")

    # 3. Test End-to-End Flow
    print("3. Testing End-to-End User Flow...")
    # Add Item
    res_item = client.post("/api/items", json={
        "item_code": "VT-E2E",
        "name": "Bàn Phím Cơ Wireless Logi",
        "unit": "Cái",
        "current_stock": 15
    })
    assert res_item.status_code == 201
    item_id = res_item.json()["id"]

    # Create Request
    res_req = client.post("/api/requests", json={
        "requester_name": "Phạm Văn E (Team Leader)",
        "items": [{"item_id": item_id, "quantity": 2}]
    })
    assert res_req.status_code == 201
    req_id = res_req.json()["id"]

    # Export
    res_export = client.post("/api/export", json={"request_id": req_id})
    assert res_export.status_code == 200
    exp_json = res_export.json()
    assert exp_json["success"] is True

    # Download All 3 Files
    pdf_url = exp_json["files"]["pdf"]
    excel_url = exp_json["files"]["excel"]
    word_url = exp_json["files"]["word"]

    assert client.get(pdf_url).status_code == 200
    assert client.get(excel_url).status_code == 200
    assert client.get(word_url).status_code == 200

    print("   [PASS] End-to-End flow from UI load -> Item create -> Request -> Export -> File downloads verified!")

    print("\n=== PHASE 5 TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    try:
        test_phase5_ui_and_e2e()
    except Exception as e:
        print(f"\n[FAIL] Phase 5 test failed: {e}")
        sys.exit(1)
