import sys
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_super_features():
    print("=== TESTING 4 SUPER-ADVANCED FEATURES ===")

    # 1. Test AI Analytics & Dashboard API
    res1 = client.get("/api/analytics/dashboard")
    print("1. Analytics Dashboard Status:", res1.status_code)
    assert res1.status_code == 200
    data1 = res1.json()
    assert "summary" in data1
    assert "predictive_alerts" in data1
    print("   Total items:", data1["summary"]["total_items"])
    print("   AI Alerts generated:", len(data1["predictive_alerts"]))

    # 2. Test Inventory Audit Report PDF Generation
    res2 = client.get("/api/export/audit-pdf")
    print("2. Inventory Audit PDF Status:", res2.status_code)
    assert res2.status_code == 200
    assert res2.headers["content-type"] == "application/pdf"

    # 3. Test Security Audit Logs API
    res3 = client.get("/api/audit/logs")
    print("3. Audit Logs Status:", res3.status_code)
    assert res3.status_code == 200
    print("   Total audit logs in DB:", len(res3.json()))

    # 4. Test Urgent Alerts Notification Bell API
    res4 = client.get("/api/audit/alerts")
    print("4. Urgent Alerts Status:", res4.status_code)
    assert res4.status_code == 200
    print("   Total urgent count:", res4.json()["total_urgent_count"])

    print("\n=== ALL 4 SUPER-ADVANCED FEATURES TESTED & PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_super_features()
