import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.services.word_maker import generate_word

def test_word_formatting():
    print("=== TESTING DECREE 30/2020 WORD GENERATOR ===")

    test_data = {
        "request_id": 2,
        "requester_name": "Đại úy Phạm Văn B (Phòng Kỹ Thuật)",
        "destination": "Đội Cảnh Sát Giao Thông Số 1 - Công An Tỉnh",
        "reason": "Trang bị phục vụ công tác tuần tra kiểm soát giao thông khẩn cấp",
        "export_date": "26/07/2026",
        "items": [
            {"item_code": "VT-CA01", "name": "Bộ Đàm Motorola GP328 Chuyên Dụng", "unit": "Bộ", "quantity": 5},
            {"item_code": "VT-CA02", "name": "Đèn Pin Siêu Sáng Đuốc Tuần Tra", "unit": "Cái", "quantity": 10}
        ]
    }

    word_path = generate_word(test_data)
    print("Generated Word document path:", word_path)
    assert os.path.exists(word_path)
    assert os.path.getsize(word_path) > 0

    print("=== WORD FORMATTING TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_word_formatting()
