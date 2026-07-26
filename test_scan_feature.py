import sys
import os

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)

def test_scan_feature():
    print("=== STARTING QR / BARCODE SCANNING FEATURE TEST ===")

    # 1. Reset Database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 2. Insert item for scanning
    print("1. Creating item VT-QR01 for scan test...")
    res = client.post("/api/items", json={
        "item_code": "VT-QR01",
        "name": "Ổ Cứng SSD Samsung 1TB",
        "unit": "Cái",
        "current_stock": 25
    })
    assert res.status_code == 201
    print("   [PASS] Created item VT-QR01.")

    # 3. Test Scan API GET /api/items/scan/VT-QR01
    print("2. Testing GET /api/items/scan/VT-QR01 (Success Case)...")
    res_scan = client.get("/api/items/scan/VT-QR01")
    assert res_scan.status_code == 200, f"Failed: {res_scan.text}"
    scan_data = res_scan.json()
    assert scan_data["item_code"] == "VT-QR01"
    assert scan_data["name"] == "Ổ Cứng SSD Samsung 1TB"
    assert scan_data["current_stock"] == 25
    print(f"   [PASS] Scan API correctly returned: {scan_data['name']} (Stock: {scan_data['current_stock']})")

    # 4. Test Case Insensitive Scan GET /api/items/scan/vt-qr01
    print("3. Testing GET /api/items/scan/vt-qr01 (Case Insensitive)...")
    res_lower = client.get("/api/items/scan/vt-qr01")
    assert res_lower.status_code == 200
    assert res_lower.json()["item_code"] == "VT-QR01"
    print("   [PASS] Case insensitive lookup matched successfully.")

    # 5. Test Non-existent Item Scan
    print("4. Testing GET /api/items/scan/INVALID-CODE (404 Case)...")
    res_404 = client.get("/api/items/scan/INVALID-CODE")
    assert res_404.status_code == 404
    assert "Không tìm thấy vật tư" in res_404.json()["detail"]
    print("   [PASS] Non-existent code correctly returned 404 Not Found.")

    # 6. Test /scan web page endpoint
    print("5. Testing GET /scan (Mobile Scanner Web View)...")
    res_view = client.get("/scan")
    assert res_view.status_code == 200
    assert "Quét Mã Xuất Kho" in res_view.text
    print("   [PASS] /scan served mobile camera HTML view successfully.")

    print("\n=== SCAN FEATURE TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    try:
        test_scan_feature()
    except Exception as e:
        print(f"\n[FAIL] Scan feature test failed: {e}")
        sys.exit(1)
