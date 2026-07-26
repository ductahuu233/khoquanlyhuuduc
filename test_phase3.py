import os
import sys
from app.services.pdf_maker import generate_pdf
from app.services.excel_maker import generate_excel
from app.services.word_maker import generate_word

def test_file_generators():
    print("=== STARTING PHASE 3 FILE GENERATORS TEST ===")

    test_data = {
        "request_id": 999,
        "requester_name": "Nguyễn Thị Mai (Trưởng phòng IT)",
        "export_date": "22/07/2026 23:55",
        "items": [
            {
                "item_code": "VT-001",
                "name": "Giấy A4 Double A 80gsm",
                "unit": "Ram",
                "quantity": 15
            },
            {
                "item_code": "VT-002",
                "name": "Bút bi Thiên Long xanh",
                "unit": "Hộp",
                "quantity": 10
            },
            {
                "item_code": "VT-003",
                "name": "Chuột không dây Logitech M330",
                "unit": "Cái",
                "quantity": 3
            }
        ]
    }

    # 1. Test PDF Generator
    print("1. Testing PDF Generator (pdf_maker.py)...")
    pdf_path = generate_pdf(test_data)
    assert os.path.exists(pdf_path), f"Error: PDF file {pdf_path} not found"
    assert os.path.getsize(pdf_path) > 0, "Error: PDF file size is 0 bytes"
    print(f"   [PASS] Generated PDF at: {pdf_path} (Size: {os.path.getsize(pdf_path)} bytes)")

    # 2. Test Excel Generator
    print("2. Testing Excel Generator (excel_maker.py)...")
    excel_path = generate_excel(test_data)
    assert os.path.exists(excel_path), f"Error: Excel file {excel_path} not found"
    assert os.path.getsize(excel_path) > 0, "Error: Excel file size is 0 bytes"
    print(f"   [PASS] Generated/Appended Excel at: {excel_path} (Size: {os.path.getsize(excel_path)} bytes)")

    # Test Excel I/O safety (Append second time)
    excel_path_2 = generate_excel(test_data)
    assert os.path.exists(excel_path_2)
    print("   [PASS] Successfully appended second dataset to Excel without conflicts.")

    # 3. Test Word Generator
    print("3. Testing Word Generator (word_maker.py)...")
    word_path = generate_word(test_data)
    assert os.path.exists(word_path), f"Error: Word file {word_path} not found"
    assert os.path.getsize(word_path) > 0, "Error: Word file size is 0 bytes"
    print(f"   [PASS] Generated Word document at: {word_path} (Size: {os.path.getsize(word_path)} bytes)")

    print("\n=== PHASE 3 TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    try:
        test_file_generators()
    except Exception as e:
        print(f"\n[FAIL] Phase 3 test failed: {e}")
        sys.exit(1)
