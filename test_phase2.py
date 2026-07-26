import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)

def test_phase2_apis():
    print("=== STARTING PHASE 2 CORE CRUD API TEST ===")

    # 1. Reset tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 2. Test Create Item
    print("1. Testing POST /api/items (Create Item)...")
    res1 = client.post("/api/items", json={
        "item_code": "VT-01",
        "name": "Giấy A4 Double A 80gsm",
        "unit": "Ram",
        "current_stock": 100
    })
    assert res1.status_code == 201, f"Failed: {res1.text}"
    item1_id = res1.json()["id"]
    print(f"   [PASS] Item 1 created with ID {item1_id}")

    res2 = client.post("/api/items", json={
        "item_code": "VT-02",
        "name": "Bút bi Thiên Long",
        "unit": "Hộp",
        "current_stock": 50
    })
    assert res2.status_code == 201
    item2_id = res2.json()["id"]
    print(f"   [PASS] Item 2 created with ID {item2_id}")

    # Test Duplicate Item Code
    dup_res = client.post("/api/items", json={
        "item_code": "VT-01",
        "name": "Giấy A4 Trùng",
        "unit": "Ram",
        "current_stock": 10
    })
    assert dup_res.status_code == 400
    print("   [PASS] Duplicate item code correctly rejected with 400 Bad Request.")

    # 3. Test Get Items
    print("2. Testing GET /api/items (List & Search)...")
    get_res = client.get("/api/items")
    assert get_res.status_code == 200
    assert len(get_res.json()) == 2
    print(f"   [PASS] Successfully retrieved {len(get_res.json())} items.")

    search_res = client.get("/api/items?search=Thiên Long")
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1
    assert search_res.json()[0]["item_code"] == "VT-02"
    print("   [PASS] Search API filtering works correctly.")

    # 4. Test Update Item
    print("3. Testing PUT /api/items/{id} (Update stock)...")
    update_res = client.put(f"/api/items/{item1_id}", json={"current_stock": 120})
    assert update_res.status_code == 200
    assert update_res.json()["current_stock"] == 120
    print("   [PASS] Updated stock to 120.")

    # 5. Test Create Request
    print("4. Testing POST /api/requests (Create Export Request)...")
    req_payload = {
        "requester_name": "Trần Thị B",
        "items": [
            {"item_id": item1_id, "quantity": 10},
            {"item_id": item2_id, "quantity": 5}
        ]
    }
    req_res = client.post("/api/requests", json=req_payload)
    assert req_res.status_code == 201, f"Failed: {req_res.text}"
    req_data = req_res.json()
    req_id = req_data["id"]
    assert req_data["status"] == "pending"
    assert len(req_data["details"]) == 2
    print(f"   [PASS] Request #{req_id} created with status 'pending' and 2 detail items.")

    # 6. Test Update Request Status
    print("5. Testing PUT /api/requests/{id}/status (Approve Request)...")
    status_res = client.put(f"/api/requests/{req_id}/status", json={"status": "approved"})
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "approved"
    print(f"   [PASS] Request #{req_id} status updated to 'approved'.")

    # 7. Test Delete Item
    print("6. Testing DELETE /api/items/{id}...")
    del_item_res = client.post("/api/items", json={
        "item_code": "VT-TEMP",
        "name": "Mục Tạm Bỏ",
        "unit": "Cái",
        "current_stock": 1
    })
    temp_id = del_item_res.json()["id"]
    del_res = client.delete(f"/api/items/{temp_id}")
    assert del_res.status_code == 204
    print("   [PASS] Item deleted successfully.")

    print("\n=== PHASE 2 TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    try:
        test_phase2_apis()
    except Exception as e:
        print(f"\n[FAIL] Phase 2 test failed: {e}")
        sys.exit(1)
