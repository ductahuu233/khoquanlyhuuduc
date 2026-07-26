import os
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT

OUTPUT_DIR = os.path.join(os.getcwd(), "exports")

def generate_word(export_data: dict) -> str:
    """
    Sinh Tờ trình xuất kho vật tư dưới dạng file Microsoft Word (.docx).
    Trả về đường dẫn tuyệt đối file đã lưu.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    request_id = export_data.get("request_id", "000")
    file_path = os.path.join(OUTPUT_DIR, f"to_trinh_xuat_kho_{request_id}.docx")

    doc = Document()

    # Page setup
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # 1. Header Quốc Hiệu Tự Do
    p_header1 = doc.add_paragraph()
    p_header1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run1 = p_header1.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc")
    run1.bold = True
    run1.font.name = "Times New Roman"
    run1.font.size = Pt(12)
    run1.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

    doc.add_paragraph() # Spacer

    # 2. Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("TỜ TRÌNH XUẤT KHO VẬT TƯ")
    run_title.bold = True
    run_title.font.name = "Times New Roman"
    run_title.font.size = Pt(16)
    run_title.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run(f"Số phiếu: PXK-{request_id}")
    run_sub.italic = True
    run_sub.font.name = "Times New Roman"
    run_sub.font.size = Pt(11)

    # 3. Main Body
    export_date = export_data.get("export_date", datetime.now().strftime("%d/%m/%Y"))
    requester = export_data.get("requester_name", "Ban Quản lý")
    destination = export_data.get("destination", "N/A")
    reason = export_data.get("reason", "N/A")
    items = export_data.get("items", [])
    total_qty = sum(item.get("quantity", 0) for item in items)

    p_content = doc.add_paragraph()
    p_content.paragraph_format.line_spacing = 1.25
    p_content.paragraph_format.space_after = Pt(8)
    
    r_kg = p_content.add_run("Kính gửi: ")
    r_kg.bold = True
    r_kg.font.name = "Times New Roman"
    r_kg.font.size = Pt(13)

    p_content.add_run("Trưởng Ban / Lãnh Đạo Đơn Vị\n\n").font.name = "Times New Roman"
    
    r_l1 = p_content.add_run("• Cán bộ đề xuất: ")
    r_l1.bold = True
    r_l1.font.name = "Times New Roman"
    p_content.add_run(f"{requester}\n").font.name = "Times New Roman"

    r_l2 = p_content.add_run("• Nơi nhận (Xuất đi đâu): ")
    r_l2.bold = True
    r_l2.font.name = "Times New Roman"
    p_content.add_run(f"{destination}\n").font.name = "Times New Roman"

    r_l3 = p_content.add_run("• Lý do / Mục đích xuất kho: ")
    r_l3.bold = True
    r_l3.font.name = "Times New Roman"
    p_content.add_run(f"{reason}\n\n").font.name = "Times New Roman"

    p_content.add_run(
        f"Kính trình Ban Lãnh Đạo phê duyệt xuất kho các vật tư phục vụ công tác vào ngày "
    ).font.name = "Times New Roman"
    
    r_date = p_content.add_run(f"{export_date}")
    r_date.bold = True
    r_date.font.name = "Times New Roman"
    
    p_content.add_run(f". Tổng số lượng vật tư đề xuất xuất kho là: ").font.name = "Times New Roman"
    
    r_sum = p_content.add_run(f"{total_qty} đơn vị")
    r_sum.bold = True
    r_sum.font.name = "Times New Roman"
    p_content.add_run(" chi tiết như sau:").font.name = "Times New Roman"

    # 4. Items Table
    table = doc.add_table(rows=1, cols=5)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table.rows[0].cells
    headers = ["STT", "Mã Vật Tư", "Tên Vật Tư", "Đơn Vị Tính", "Số Lượng"]
    
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.name = "Times New Roman"
            run.font.bold = True
            run.font.size = Pt(11)

    for idx, item in enumerate(items, start=1):
        row_cells = table.add_row().cells
        row_cells[0].text = str(idx)
        row_cells[1].text = str(item.get("item_code", ""))
        row_cells[2].text = str(item.get("name", ""))
        row_cells[3].text = str(item.get("unit", ""))
        row_cells[4].text = str(item.get("quantity", 0))

        for cell in row_cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(11)

    # Spacing
    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(12)

    p_end = doc.add_paragraph()
    r_end = p_end.add_run("Kính trình Trưởng đoàn/Ban Giám đốc xem xét phê duyệt.")
    r_end.italic = True
    r_end.font.name = "Times New Roman"
    r_end.font.size = Pt(12)

    # 5. Signature Area
    p_sig = doc.add_paragraph()
    p_sig.paragraph_format.space_before = Pt(20)
    p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_sig_date = p_sig.add_run(f"Ngày ..... tháng ..... năm 2026\n")
    r_sig_date.italic = True
    r_sig_date.font.name = "Times New Roman"

    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    s_cells = sig_table.rows[0].cells

    p_left = s_cells[0].paragraphs[0]
    p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_l = p_left.add_run("NGƯỜI TRÌNH\n(Ký và ghi rõ họ tên)")
    r_l.bold = True
    r_l.font.name = "Times New Roman"

    p_right = s_cells[1].paragraphs[0]
    p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_r = p_right.add_run("TRƯỞNG ĐOÀN / PHÊ DUYỆT\n(Ký và ghi rõ họ tên)")
    r_r.bold = True
    r_r.font.name = "Times New Roman"

    # Save document with try-except
    try:
        doc.save(file_path)
        return file_path
    except Exception as e:
        raise RuntimeError(f"Lỗi khi tạo file Word: {e}")
