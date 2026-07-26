import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Vietnamese Font if available on Windows
FONT_NAME = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

try:
    font_path = r"C:\Windows\Fonts\arial.ttf"
    font_bold_path = r"C:\Windows\Fonts\arialbd.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("ArialVN", font_path))
        FONT_NAME = "ArialVN"
    if os.path.exists(font_bold_path):
        pdfmetrics.registerFont(TTFont("ArialVN-Bold", font_bold_path))
        FONT_BOLD = "ArialVN-Bold"
except Exception as e:
    print(f"Font registration warning: {e}")

OUTPUT_DIR = os.path.join(os.getcwd(), "exports")

def generate_pdf(export_data: dict) -> str:
    """
    Sinh file PDF Phiếu xuất kho từ export_data.
    Trả về đường dẫn tuyệt đối đến file PDF đã lưu.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    request_id = export_data.get("request_id", "000")
    file_path = os.path.join(OUTPUT_DIR, f"phieu_xuat_kho_{request_id}.pdf")

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="TitleStyle",
        fontName=FONT_BOLD,
        fontSize=18,
        leading=22,
        alignment=1,  # Center
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=15
    )

    normal_style = ParagraphStyle(
        name="NormalStyle",
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155")
    )

    header_style = ParagraphStyle(
        name="HeaderStyle",
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        textColor=colors.white,
        alignment=1
    )

    cell_style = ParagraphStyle(
        name="CellStyle",
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    )

    # 1. Title
    story.append(Paragraph("PHIẾU XUẤT KHO VẬT TƯ", title_style))
    story.append(Spacer(1, 10))

    # 2. Metadata Info
    requester = export_data.get("requester_name", "N/A")
    destination = export_data.get("destination", "N/A")
    reason = export_data.get("reason", "N/A")
    export_date = export_data.get("export_date", "N/A")
    
    meta_info = [
        [Paragraph(f"<b>Mã phiếu xuất:</b> #{request_id}", normal_style),
         Paragraph(f"<b>Ngày xuất:</b> {export_date}", normal_style)],
        [Paragraph(f"<b>Người yêu cầu:</b> {requester}", normal_style),
         Paragraph(f"<b>Nơi nhận (Xuất đi):</b> {destination}", normal_style)],
        [Paragraph(f"<b>Lý do xuất kho:</b> {reason}", normal_style),
         Paragraph("<b>Trạng thái:</b> Đã xuất kho", normal_style)]
    ]
    meta_table = Table(meta_info, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # 3. Items Table
    headers = [
        Paragraph("STT", header_style),
        Paragraph("Mã Vật Tư", header_style),
        Paragraph("Tên Vật Tư", header_style),
        Paragraph("ĐVT", header_style),
        Paragraph("Số Lượng", header_style)
    ]
    
    table_data = [headers]
    items = export_data.get("items", [])
    total_qty = 0

    for idx, item in enumerate(items, start=1):
        qty = item.get("quantity", 0)
        total_qty += qty
        row = [
            Paragraph(str(idx), cell_style),
            Paragraph(str(item.get("item_code", "")), cell_style),
            Paragraph(str(item.get("name", "")), cell_style),
            Paragraph(str(item.get("unit", "")), cell_style),
            Paragraph(str(qty), cell_style)
        ]
        table_data.append(row)

    # Footer total row
    total_row = [
        Paragraph("", cell_style),
        Paragraph("<b>TỔNG CỘNG</b>", ParagraphStyle("BoldCell", parent=cell_style, fontName=FONT_BOLD)),
        Paragraph("", cell_style),
        Paragraph("", cell_style),
        Paragraph(f"<b>{total_qty}</b>", ParagraphStyle("BoldQty", parent=cell_style, fontName=FONT_BOLD))
    ]
    table_data.append(total_row)

    items_table = Table(table_data, colWidths=[40, 90, 240, 70, 80])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2563EB")),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#F1F5F9")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 30))

    # 4. Signature Block
    sig_data = [
        [
            Paragraph("<b>Người Lập Phiếu</b><br/>(Ký, ghi rõ họ tên)", ParagraphStyle("Center", parent=normal_style, alignment=1)),
            Paragraph("<b>Người Nhận Hàng</b><br/>(Ký, ghi rõ họ tên)", ParagraphStyle("Center", parent=normal_style, alignment=1)),
            Paragraph("<b>Thủ Kho</b><br/>(Ký, ghi rõ họ tên)", ParagraphStyle("Center", parent=normal_style, alignment=1))
        ]
    ]
    sig_table = Table(sig_data, colWidths=[170, 170, 180])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(sig_table)

    # Build Document
    try:
        doc.build(story)
    except Exception as e:
        raise RuntimeError(f"Lỗi khi tạo file PDF: {e}")

    return file_path
