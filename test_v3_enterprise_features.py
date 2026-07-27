import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_v3_inbound_and_asset_lifecycle():
    print("=== STARTING V3 ENTERPRISE FEATURE TESTS ===")
    
    # 1. Test Inbound Batch Creation (Fixed Assets with Serials)
    inbound_payload = {
        "source": "Cuc Cap",
        "supplier_or_unit": "Cuc Ky Thuat Vat Tu",
        "created_by": "Thuong uy Nguyen Van A",
        "location": "Kho Ky Thuat",
        "items": [
            {
                "item_code": "VT-BD-TEST",
                "name": "Bo Dam Nghi Le Test",
                "unit": "Bo",
                "category": "fixed_asset",
                "quantity": 2,
                "unit_price": 1500000.0,
                "serial_numbers": ["SN-TEST-001", "SN-TEST-002"]
            }
        ]
    }
    response = client.post("/api/inbound", json=inbound_payload, headers={"X-User-Role": "admin"})
    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    assert data["success"] == True
    assert "PNK-" in data["receipt_code"]
    assert len(data["created_assets"]) == 2
    print("[OK] 1. Test Inbound Batch & Serial Creation PASSED!")

    receipt_id = data["receipt_id"]
    first_asset_code = data["created_assets"][0]["code"]

    # 2. Test Export QR PDF for Inbound Batch
    pdf_res = client.get(f"/api/inbound/export-qr-pdf/{receipt_id}")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    print("[OK] 2. Test Export Inbound QR PDF PASSED!")

    # 3. Test Assets List
    assets_res = client.get("/api/assets")
    assert assets_res.status_code == 200
    assets_list = assets_res.json()
    assert len(assets_list) >= 2
    print("[OK] 3. Test Assets Listing PASSED!")

    # 4. Test Scan QR Code
    scan_res = client.get(f"/api/assets/scan/{first_asset_code}")
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["code"] == first_asset_code
    assert scan_data["type"] == "fixed_asset"
    print("[OK] 4. Test QR Code Scanning PASSED!")

    # 5. Test Report Damaged Asset
    report_res = client.post("/api/assets/report-damaged", json={
        "asset_code": first_asset_code,
        "reporter_name": "Can bo A",
        "reason": "Hong loa trong khi dien tap"
    })
    assert report_res.status_code == 200
    assert report_res.json()["success"] == True
    print("[OK] 5. Test Asset Report Damaged PASSED!")

    # Verify status changed to damaged
    scan_after_damage = client.get(f"/api/assets/scan/{first_asset_code}")
    assert scan_after_damage.json()["status"] == "damaged"

    # 6. Test Recover Damaged Asset to Phe Pham
    recover_res = client.post(f"/api/assets/recover?asset_code={first_asset_code}")
    assert recover_res.status_code == 200
    assert recover_res.json()["success"] == True
    print("[OK] 6. Test Recover Asset to Kho Phe Pham PASSED!")

    # 7. Test Export Disposal Word Document
    word_res = client.get("/api/assets/disposal-word")
    assert word_res.status_code == 200
    print("[OK] 7. Test Export Disposal Word Document PASSED!")

    # 8. Test Stock Card (The Kho)
    item_res = client.get(f"/api/reports/stock-card/1")
    assert item_res.status_code == 200
    print("[OK] 8. Test Stock Card Dau Vet PASSED!")

    # 9. Test Excel NXT Export
    excel_res = client.get("/api/reports/nhat-ky-nxt-excel")
    assert excel_res.status_code == 200
    print("[OK] 9. Test Excel NXT Export PASSED!")

    # 10. Test Stock Reconciliation Audit
    reconcile_res = client.post("/api/reports/reconciliation", json={
        "title": "Kiem ke thu nghiem",
        "inspector_name": "Truong doan A",
        "scanned_asset_codes": [first_asset_code]
    })
    assert reconcile_res.status_code == 200
    assert reconcile_res.json()["success"] == True
    print("[OK] 10. Test Stock Reconciliation Audit PASSED!")

    print("\nALL 10 V3 ENTERPRISE FEATURE TESTS PASSED 100% PERFECTLY!")

if __name__ == "__main__":
    test_v3_inbound_and_asset_lifecycle()
