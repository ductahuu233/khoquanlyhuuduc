import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000"

def make_request(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    body_bytes = json.dumps(data).encode('utf-8') if data else None
    try:
        with urllib.request.urlopen(req, data=body_bytes) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8')) if e.fp else {}

def test_security():
    print("[START] Bat dau kiem tra tinh nang Bao mat Mang Noi bo (Security Edition)...")

    # 1. Test Login Page
    req = urllib.request.Request(f"{BASE_URL}/login")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, "Loi truy cap trang login"
        print("[OK] Test 1: Trang Dang Nhap /login hoat dong binh thuong (Status 200)")

    # 2. Test Seed Users API
    s2, d2 = make_request(f"{BASE_URL}/api/auth/seed-users", method="POST")
    assert s2 == 200 and d2.get("success"), "Loi nap danh sach tai khoan mau"
    print("[OK] Test 2: Nap thanh cong 3 tai khoan bao mat mau (admin, thukho, canbo)")

    # 3. Test Successful Login (Thu kho)
    s3, d3 = make_request(f"{BASE_URL}/api/auth/login", method="POST", data={"username": "thukho", "password": "thukho123"})
    assert s3 == 200 and d3.get("success"), "Loi dang nhap thu kho"
    print(f"[OK] Test 3: Dang nhap thanh cong tai khoan Thu kho ({d3['user']['username']})")

    # 4. Test Successful Login (Admin)
    s4, d4 = make_request(f"{BASE_URL}/api/auth/login", method="POST", data={"username": "admin", "password": "admin123"})
    assert s4 == 200 and d4.get("user")["role"] == "admin", "Loi dang nhap admin"
    print(f"[OK] Test 4: Dang nhap thanh cong tai khoan Admin ({d4['user']['username']})")

    # 5. Test Failed Login (Wrong password)
    s5, d5 = make_request(f"{BASE_URL}/api/auth/login", method="POST", data={"username": "admin", "password": "wrongpassword!"})
    assert s5 == 401, "He thong khong chan duoc mat khau sai"
    print("[OK] Test 5: He thong chan chinh xac dang nhap sai mat khau (HTTP 401 Unauthorized)")

    print("\n[SUCCESS] ALL 5 SECURITY ARCHITECTURE TESTS PASSED 100% PERFECTLY!")

if __name__ == "__main__":
    test_security()
