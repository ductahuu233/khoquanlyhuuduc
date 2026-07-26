import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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

def generate_inventory_audit_pdf(items_data: list) -> str:
    """
    Tạo file PDF Biên bản kiểm kê tồn kho A4 chính thức cho Bộ Công An.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(OUTPUT_DIR, f"bien_ban_kiem_ke_kho_{timestamp_str}.pdf")

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

    # Header section: Official Police Banner
    header_style_left = ParagraphStyle(
        name="HeaderLeft",
        fontName=FONT_BOLD,
        fontSize=10,
        leading=12,
        alignment=0,
        textColor=colors.HexColor("#DC2626")
    )
    header_style_right = ParagraphStyle(
        name="HeaderRight",
        fontName=FONT_BOLD,
        fontSize=10,
        leading=12,
        alignment=2,
        textColor=colors.HexColor("#1E3A34")
    )

    header_table = Table(
        [[
            Paragraph("BỘ CÔNG AN<br/><font size=8 color='#059669'>TỔNG CỤC KỸ THUẬT VẬT TƯ</font>", header_style_left),
            Paragraph("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM<br/><font size=8 color='#D97706'>Độc lập - Tự do - Hạnh phúc</font>", header_style_right)
        ]],
        colWidths=[250, 280]
    )
    story.append(header_table)
    story.append(Spacer(1, 15))

    # Document Title
    title_style = ParagraphStyle(
        name="AuditTitle",
        fontName=FONT_BOLD,
        fontSize=16,
        leading=20,
        alignment=1,
        textColor=colors.HexColor("#064E3B"),
        spaceAfter=6
    )
    story.append(Paragraph("BIÊN BẢN KIỂM KÊ KHO VẬT TƯ NỘI BỘ", title_style))

    sub_title = ParagraphStyle(
        name="AuditSubTitle",
        fontName=FONT_NAME,
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=15
    )
    now_str = datetime.now().strftime("%H:%M ngày %d/%m/%Y")
    story.append(Paragraph(f"<i>Thời điểm lập biên bản: {now_str} - Địa điểm: Kho Kỹ thuật trung tâm</i>", sub_title))

    # Audit Items Table
    cell_head = ParagraphStyle(name="CellHead", fontName=FONT_BOLD, fontSize=10, leading=12, alignment=1, textColor=colors.white)
    cell_body = ParagraphStyle(name="CellBody", fontName=FONT_NAME, fontSize=9, leading=11, alignment=0)
    cell_body_center = ParagraphStyle(name="CellCenter", fontName=FONT_NAME, fontSize=9, leading=11, alignment=1)
    cell_body_bold = ParagraphStyle(name="CellBold", fontName=FONT_BOLD, fontSize=9, leading=11, alignment=1, textColor=colors.HexColor("#059669"))

    table_data = [[
        Paragraph("STT", cell_head),
        Paragraph("Mã VT", cell_head),
        Paragraph("Tên Vật Tư / Thiết Bị Kho", cell_head),
        Paragraph("Đơn Vị", cell_head),
        Paragraph("Tồn Thực Tế", cell_head),
        Paragraph("Trạng Thái Kho", cell_head)
    ]]

    for idx, item in enumerate(items_data, 1):
        stock = item.get("current_stock", 0)
        unit = item.get("unit", "")
        if stock <= 0:
            status_str = "<font color='#DC2626'><b>🔴 Hết hàng</b></font>"
        elif stock < 10:
            status_str = "<font color='#D97706'><b>🟡 Sắp hết hàng</b></font>"
        else:
            status_str = "<font color='#059669'><b>🟢 An toàn</b></font>"

        table_data.append([
            Paragraph(str(idx), cell_body_center),
            Paragraph(item.get("item_code", ""), cell_body_center),
            Paragraph(item.get("name", ""), cell_body),
            Paragraph(unit, cell_body_center),
            Paragraph(f"<b>{stock}</b>", cell_body_bold),
            Paragraph(status_str, cell_body_center)
        ])

    audit_table = Table(table_data, colWidths=[35, 75, 230, 55, 65, 70])
    audit_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#047857")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F0FDF4")]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(audit_table)
    story.append(Spacer(1, 25))

    # Signature Blocks
    sig_style = ParagraphStyle(name="SigHead", fontName=FONT_BOLD, fontSize=10, leading=12, alignment=1, textColor=colors.HexColor("#1E293B"))
    sig_sub = ParagraphStyle(name="SigSub", fontName=FONT_NAME, fontSize=8, leading=10, alignment=1, textColor=colors.HexColor("#64748B"))

    sig_table = Table([
        [
            Paragraph("<b>CÁN BỘ KIỂM KÊ</b>", sig_style),
            Paragraph("<b>THỦ KHO QUẢN LÝ</b>", sig_style),
            Paragraph("<b>LÃNH ĐẠO PHÊ DUYỆT</b>", sig_style)
        ],
        [
            Paragraph("<i>(Ký và ghi rõ họ tên)</i>", sig_sub),
            Paragraph("<i>(Ký và ghi rõ họ tên)</i>", sig_sub),
            Paragraph("<i>(Ký tên và đóng dấu)</i>", sig_sub)
        ]
    ], colWidths=[175, 175, 180])
    
    story.append(sig_table)

    doc.build(story)
    return file_path
