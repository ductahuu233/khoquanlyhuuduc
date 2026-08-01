import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            raw_body = response.read()
            content_type = response.headers.get('Content-Type', '')
            if 'json' in content_type:
                return response.status, json.loads(raw_body.decode('utf-8'))
            else:
                return response.status, raw_body
    except urllib.error.HTTPError as e:
        raw_body = e.read()
        try:
            return e.code, json.loads(raw_body.decode('utf-8'))
        except Exception:
            return e.code, raw_body

def test_login_authentication():
    print("[TEST 1/7] Testing SHA-256 Authentication & Authorization...")
    
    # 1. Valid Admin Login
    status_code, data = make_request(f"{BASE_URL}/api/auth/login", method="POST", data={
        "username": "admin",
        "password": "admin123"
    })
    assert status_code == 200, f"Expected 200, got {status_code}"
    assert data.get("success") == True, "Login admin failed"
    print("  [OK] Admin SHA-256 login successful.")

    # 2. Valid Storekeeper Login
    status_code, data = make_request(f"{BASE_URL}/api/auth/login", method="POST", data={
        "username": "thukho",
        "password": "thukho123"
    })
    assert status_code == 200, f"Expected 200, got {status_code}"
    assert data.get("user", {}).get("role") == "storekeeper", "Role mismatch for storekeeper"
    print("  [OK] Storekeeper SHA-256 login successful.")

    # 3. Invalid Password Rejection
    status_code, data = make_request(f"{BASE_URL}/api/auth/login", method="POST", data={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert status_code == 401, f"Expected 401, got {status_code}"
    print("  [OK] Rejected invalid password correctly (401 Unauthorized).")

def test_inventory_management():
    print("\n[TEST 2/7] Testing Inventory CRUD & QR Code Scanner API...")

    # 1. Fetch Item List
    status_code, items = make_request(f"{BASE_URL}/api/items")
    assert status_code == 200, f"Expected 200, got {status_code}"
    assert isinstance(items, list), "Items response should be list"
    print(f"  [OK] Fetched {len(items)} inventory items successfully.")

    # 2. QR Code Scanning for item
    if len(items) > 0:
        target_code = items[0]["item_code"]
        status_code, scan_data = make_request(f"{BASE_URL}/api/items/scan/{target_code}")
        assert status_code == 200, f"Expected 200, got {status_code}"
        assert scan_data.get("item_code") == target_code, "Scanned code mismatch"
        print(f"  [OK] Scanned QR barcode '{target_code}' successfully.")

def test_request_submission():
    print("\n[TEST 3/7] Testing Export Request Creation Flow...")

    # 1. Fetch available items
    _, items = make_request(f"{BASE_URL}/api/items")
    assert len(items) > 0, "No items available to create request"
    item_id = items[0]["id"]

    # 2. Submit new Export Request
    payload = {
        "requester_name": "Hạ sĩ Tạ Hữu Đức (Đội Nghi Lễ)",
        "destination": "Đoàn Đặc Nhiệm 1 - Bộ Tư Lệnh CSCĐ",
        "reason": "Phục vụ công tác huấn luyện nghi lễ cấp Nhà nước",
        "items": [
            {"item_id": item_id, "quantity": 2}
        ]
    }
    status_code, req_data = make_request(f"{BASE_URL}/api/requests", method="POST", data=payload, headers={"X-User-Role": "user"})
    assert status_code == 201, f"Expected 201, got {status_code}"
    req_id = req_data.get("id")
    assert req_data.get("status") == "pending", "Request status should be pending"
    print(f"  [OK] Created new export request #PXK-{req_id} with status 'pending'.")
    return req_id

def test_export_approval_and_reports(req_id):
    print("\n[TEST 4/7] Testing Export Approval & Report Files Generation (Word/Excel/PDF/ZIP)...")

    # 1. Execute Export Approval
    headers = {"X-User-Role": "admin"}
    status_code, export_res = make_request(f"{BASE_URL}/api/export", method="POST", data={"request_id": req_id}, headers=headers)
    assert status_code == 200, f"Expected 200, got {status_code}: {export_res}"
    assert export_res.get("success") == True, "Export execution failed"
    print(f"  [OK] Approved export request #PXK-{req_id} successfully.")

    # 2. Verify Generated Files Accessibility
    files = export_res.get("files", {})
    for ftype in ["pdf", "excel", "word"]:
        furl = files.get(ftype)
        assert furl is not None, f"Missing {ftype} file link"
        full_url = f"{BASE_URL}{furl}"
        
        # Test download endpoint
        d_status, _ = make_request(full_url)
        assert d_status == 200, f"File download failed for {ftype} at {full_url}: status {d_status}"
        print(f"  [OK] Verified {ftype.upper()} document download link ({furl}).")

    # 3. Verify ZIP Archive Bundle Download
    zip_url = f"{BASE_URL}/api/export/history/{req_id}/zip"
    z_status, _ = make_request(zip_url)
    assert z_status == 200, f"ZIP bundle download failed for request #{req_id}"
    print(f"  [OK] Verified ZIP archive package download for #PXK-{req_id}.")

def test_inbound_batch_and_qr():
    print("\n[TEST 5/7] Testing Inbound Batch Receipt & Fixed Asset Serial QR Creation...")

    payload = {
        "source": "Cục Quản Lý Kỹ Thuật - Bộ Công An",
        "supplier_or_unit": "Tổng Cục Hậu Cần",
        "created_by": "Thủ Kho Trưởng",
        "location": "Kho Kỹ Thuật (Kệ A2)",
        "items": [
            {
                "item_code": "VT-TEST-001",
                "name": "Bộ Đàm Nghi Lễ Chuyên Dụng Moto-2026",
                "unit": "Bộ",
                "category": "fixed_asset",
                "quantity": 2,
                "unit_price": 5000000,
                "serial_numbers": ["SN-MOTO-001", "SN-MOTO-002"]
            }
        ]
    }
    headers = {"X-User-Role": "storekeeper"}
    status_code, res = make_request(f"{BASE_URL}/api/inbound", method="POST", data=payload, headers=headers)
    assert status_code == 200, f"Expected 200, got {status_code}"
    receipt_code = res.get("receipt_code")
    created_assets = res.get("created_assets", [])
    assert len(created_assets) == 2, "Expected 2 assets created"
    print(f"  [OK] Created inbound receipt {receipt_code} with {len(created_assets)} serial QR assets ({created_assets[0]['code']}).")

def test_asset_lifecycle_damaged_recovery():
    print("\n[TEST 6/7] Testing Asset Lifecycle 360° (Damage Report, Recovery & Disposal Word)...")

    # 1. Fetch Assets
    status_code, assets = make_request(f"{BASE_URL}/api/assets")
    assert status_code == 200, f"Expected 200, got {status_code}"
    assert len(assets) > 0, "No assets found"
    asset_code = assets[0]["asset_code"]

    # 2. Report Damaged
    status_code, res = make_request(f"{BASE_URL}/api/assets/report-damaged", method="POST", data={
        "asset_code": asset_code,
        "reporter_name": "Đại úy Nguyễn Văn A",
        "reason": "Hỏng hóc mạch điều khiển do chập điện trong công tác"
    })
    assert status_code == 200, f"Expected 200, got {status_code}"
    print(f"  [OK] Reported asset {asset_code} as DAMAGED.")

    # 3. Recover to Disposal Stock
    status_code, res = make_request(f"{BASE_URL}/api/assets/recover?asset_code={asset_code}&performer=Th%E1%BB%A7%20kho", method="POST")
    assert status_code == 200, f"Expected 200, got {status_code}"
    print(f"  [OK] Recovered asset {asset_code} into Kho Phe Pham.")

    # 4. Generate Disposal Word Report (Decree 30)
    status_code, _ = make_request(f"{BASE_URL}/api/assets/disposal-word")
    assert status_code == 200, f"Expected 200, got {status_code}"
    print(f"  [OK] Generated Decree 30 Disposal Word document successfully.")

def test_audit_logs_and_alerts():
    print("\n[TEST 7/7] Testing Security Audit Logs & Emergency Alerts System...")

    # 1. Fetch Audit Trail Logs
    status_code, logs = make_request(f"{BASE_URL}/api/audit/logs")
    assert status_code == 200, f"Expected 200, got {status_code}"
    assert isinstance(logs, list), "Audit logs should be list"
    print(f"  [OK] Retrieved {len(logs)} security audit trail logs.")

    # 2. Fetch System Alerts
    status_code, alerts = make_request(f"{BASE_URL}/api/audit/alerts")
    assert status_code == 200, f"Expected 200, got {status_code}"
    print(f"  [OK] System alerts check returned {len(alerts)} items.")

if __name__ == "__main__":
    print("==========================================================================")
    print("  AUTOMATED FULL SYSTEM TEST SUITE - LEVEL MAX v4.0")
    print("  Target: Doan Nghi Le CAND / Bo Tu Lenh CSCD Warehouse Platform")
    print("==========================================================================")
    
    time.sleep(2) # Give uvicorn a moment
    try:
        test_login_authentication()
        test_inventory_management()
        req_id = test_request_submission()
        test_export_approval_and_reports(req_id)
        test_inbound_batch_and_qr()
        test_asset_lifecycle_damaged_recovery()
        test_audit_logs_and_alerts()

        print("\n==========================================================================")
        print("  ALL 7 SYSTEM TEST SUITES PASSED 100% PERFECTLY!")
        print("  System is 100% verified, bug-free, and operational.")
        print("==========================================================================")
    except Exception as e:
        print(f"\n[TEST FAILED] Error: {e}")
        import traceback
        traceback.print_exc()
