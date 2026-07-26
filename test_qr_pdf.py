import sys
import os

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.services.qr_pdf_maker import generate_qr_decal_pdf

client = TestClient(app)

def test_qr_decal_pdf():
    print("=== STARTING QR DECAL LABELS PDF TEST ===")

    # 1. Reset Database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 2. Add Test Items
    print("1. Adding 5 sample items for decal grid test...")
    sample_items = [
        {"item_code": "VT-001", "name": "Giấy A4 Double A 80gsm", "unit": "Ram", "current_stock": 100},
        {"item_code": "VT-002", "name": "Bút bi Thiên Long xanh", "unit": "Hộp", "current_stock": 50},
        {"item_code": "VT-003", "name": "Máy in HP LaserJet M404dn", "unit": "Bộ", "current_stock": 5},
        {"item_code": "VT-004", "name": "Chuột không dây Logitech M330", "unit": "Cái", "current_stock": 12},
        {"item_code": "VT-005", "name": "Bàn phím cơ Wireless Keychron K2", "unit": "Cái", "current_stock": 8}
    ]

    for item_data in sample_items:
        res = client.post("/api/items", json=item_data)
        assert res.status_code == 201

    print("   [PASS] 5 items created successfully.")

    # 3. Test Service Function Directly
    print("2. Testing app.services.qr_pdf_maker.generate_qr_decal_pdf()...")
    pdf_path = generate_qr_decal_pdf(sample_items)
    assert os.path.exists(pdf_path), f"Error: PDF file {pdf_path} not found"
    assert os.path.getsize(pdf_path) > 0, "Error: PDF file size is 0 bytes"
    print(f"   [PASS] Generated QR Decal PDF at: {pdf_path} (Size: {os.path.getsize(pdf_path)} bytes)")

    # 4. Test API Endpoint GET /api/items/export-qr-pdf
    print("3. Testing GET /api/items/export-qr-pdf Endpoint...")
    res_api = client.get("/api/items/export-qr-pdf")
    assert res_api.status_code == 200
    assert res_api.headers["content-type"] == "application/pdf"
    assert len(res_api.content) > 0
    print("   [PASS] Endpoint returned 200 OK with valid PDF bytes.")

    print("\n=== QR DECAL LABELS PDF TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    try:
        test_qr_decal_pdf()
    except Exception as e:
        print(f"\n[FAIL] QR Decal PDF test failed: {e}")
        sys.exit(1)
