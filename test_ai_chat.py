import sys
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ai_chat_flow():
    print("=== TESTING AI CHATBOT ROUTE (/api/chat) ===")
    
    # 1. Test Greetings
    res1 = client.post("/api/chat", json={"message": "Xin chào bạn là ai"})
    assert res1.status_code == 200
    data1 = res1.json()
    print("1. Greeting Response:\n", data1["reply"][:150], "...")
    assert "Trợ Lý AI" in data1["reply"]

    # 2. Test Inventory Query
    res2 = client.post("/api/chat", json={"message": "Kho còn bao nhiêu bộ đàm và đèn pin?"})
    assert res2.status_code == 200
    data2 = res2.json()
    print("2. Inventory Lookup Response:\n", data2["reply"])
    assert "TỒN KHO" in data2["reply"] or "TRA CỨU" in data2["reply"]

    # 3. Test Export Workflow Guidance
    res3 = client.post("/api/chat", json={"message": "Hướng dẫn xuất kho và tải file pdf excel word"})
    assert res3.status_code == 200
    data3 = res3.json()
    print("3. Export Workflow Response:\n", data3["reply"])
    assert "BÁO CÁO" in data3["reply"] or "PDF" in data3["reply"]

    print("\n=== AI CHATBOT TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_ai_chat_flow()
