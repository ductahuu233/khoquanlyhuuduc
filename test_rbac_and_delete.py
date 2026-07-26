import sys
import os

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import Item, Request, RequestDetail

client = TestClient(app)

def test_rbac_and_delete():
    print("=== STARTING RBAC & FORCE DELETE FEATURE TEST ===")

    # 1. Reset Database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 2. Test User Role Restrictions (HTTP 403)
    print("1. Testing User Role Restrictions (Header X-User-Role: user)...")
    res_user_add = client.post(
        "/api/items",
        json={"item_code": "VT-SEC", "name": "Vật Tư Thử Quyền", "unit": "Cái", "current_stock": 10},
        headers={"X-User-Role": "user"}
    )
    assert res_user_add.status_code == 403, f"Expected 403, got {res_user_add.status_code}"
    print("   [PASS] User role POST /api/items correctly rejected with HTTP 403 Forbidden.")

    res_user_export = client.post(
        "/api/export",
        json={"request_id": 1},
        headers={"X-User-Role": "user"}
    )
    assert res_user_export.status_code == 403, f"Expected 403, got {res_user_export.status_code}"
    print("   [PASS] User role POST /api/export correctly rejected with HTTP 403 Forbidden.")

    # 3. Admin Role Success
    print("2. Testing Admin Role Operations (Header X-User-Role: admin)...")
    res_admin_add = client.post(
        "/api/items",
        json={"item_code": "VT-DEL01", "name": "Vật Tư Test Xóa", "unit": "Cái", "current_stock": 50},
        headers={"X-User-Role": "admin"}
    )
    assert res_admin_add.status_code == 201
    item_id = res_admin_add.json()["id"]
    print(f"   [PASS] Admin role created item VT-DEL01 with ID {item_id}.")

    # 4. Create Request referencing this item
    print("3. Creating Export Request referencing Item...")
    res_req = client.post(
        "/api/requests",
        json={
            "requester_name": "Nhân viên Nguyễn Văn A",
            "items": [{"item_id": item_id, "quantity": 5}]
        },
        headers={"X-User-Role": "user"} # User can create requests!
    )
    assert res_req.status_code == 201
    req_id = res_req.json()["id"]
    print(f"   [PASS] User role created Request #{req_id} successfully.")

    # 5. User try to delete item -> 403
    print("4. Testing User role delete item attempt...")
    res_user_del = client.delete(f"/api/items/{item_id}", headers={"X-User-Role": "user"})
    assert res_user_del.status_code == 403
    print("   [PASS] User role delete attempt correctly rejected with 403.")

    # 6. Admin Force Delete Item (With dependencies)
    print("5. Testing Admin Force Delete Item (With child dependencies)...")
    res_admin_del = client.delete(f"/api/items/{item_id}", headers={"X-User-Role": "admin"})
    assert res_admin_del.status_code == 204, f"Failed: {res_admin_del.text}"
    print("   [PASS] Admin force deleted item successfully! (Cascade child records cleaned up).")

    # Verify item is gone
    res_check = client.get(f"/api/items/{item_id}")
    assert res_check.status_code == 404
    print("   [PASS] Item no longer exists in database.")

    print("\n=== RBAC & FORCE DELETE TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    try:
        test_rbac_and_delete()
    except Exception as e:
        print(f"\n[FAIL] RBAC & Force Delete test failed: {e}")
        sys.exit(1)
