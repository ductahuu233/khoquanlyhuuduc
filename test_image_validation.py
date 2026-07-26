import io
import sys
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_image_validation():
    print("=== TESTING IMAGE FORMAT VALIDATION ===")

    # 1. Test uploading non-image file (.txt)
    fake_txt = io.BytesIO(b"This is a text file, not an image")
    res1 = client.post(
        "/api/items/upload-image",
        files={"file": ("document.txt", fake_txt, "text/plain")}
    )
    print("1. Uploading .txt result:", res1.status_code, res1.json())
    assert res1.status_code == 400
    assert "hình ảnh" in res1.json()["detail"].lower() or "định dạng" in res1.json()["detail"].lower()

    # 2. Test uploading valid PNG image
    valid_png = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4")
    res2 = client.post(
        "/api/items/upload-image",
        files={"file": ("photo.png", valid_png, "image/png")}
    )
    print("2. Uploading .png result:", res2.status_code, res2.json())
    assert res2.status_code == 200
    assert res2.json()["url"].startswith("/uploads/")

    # 3. Test creating item with invalid image URL format
    res3 = client.post(
        "/api/items",
        headers={"X-User-Role": "admin"},
        json={
            "item_code": "VT-TEST-IMG",
            "name": "Vật Tư Test Ảnh Invalid",
            "unit": "Cái",
            "current_stock": 10,
            "image_url": "invalid_url_string_without_http"
        }
    )
    print("3. Invalid URL item creation result:", res3.status_code, res3.json())
    assert res3.status_code == 400

    print("\n=== IMAGE VALIDATION TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_image_validation()
