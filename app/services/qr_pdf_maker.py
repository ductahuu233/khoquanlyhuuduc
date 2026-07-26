import os
import io
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
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

def generate_qr_decal_pdf(items_data: list) -> str:
    """
    Tạo file PDF tem nhãn mã QR chuẩn khổ A4 (lưới 3 cột) để in lên giấy Decal.
    Trả về đường dẫn tuyệt đối file đã lưu.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    file_path = os.path.join(OUTPUT_DIR, "tem_nhan_ma_qr_A4.pdf")

    # A4 Page setup with 25pt margins (~9mm)
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=25,
        rightMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="DecalTitle",
        fontName=FONT_BOLD,
        fontSize=14,
        leading=18,
        alignment=1,  # Center
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=12
    )

    code_style = ParagraphStyle(
        name="DecalCode",
        fontName=FONT_BOLD,
        fontSize=10,
        leading=12,
        alignment=1,  # Center
        textColor=colors.HexColor("#0F172A")
    )

    name_style = ParagraphStyle(
        name="DecalName",
        fontName=FONT_NAME,
        fontSize=8,
        leading=10,
        alignment=1,  # Center
        textColor=colors.HexColor("#334155")
    )

    story.append(Paragraph("DANH SÁCH TEM NHÃN MÃ QR VẬT TƯ KHO (GIẤY DECAL A4)", title_style))
    story.append(Spacer(1, 10))

    # Generate cell element for each item
    cells = []
    for item in items_data:
        code = str(item.get("item_code", ""))
        name = str(item.get("name", ""))
        unit = str(item.get("unit", ""))

        # 1. Generate QR Code image in memory
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=1
        )
        qr.add_data(code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # 2. ReportLab Image (22x22mm ~ 62x62 points)
        rl_img = Image(img_buffer, width=62, height=62)
        rl_img.hAlign = 'CENTER'

        # 3. Cell elements
        cell_content = [
            rl_img,
            Spacer(1, 2),
            Paragraph(code, code_style),
            Paragraph(f"{name} ({unit})", name_style)
        ]
        cells.append(cell_content)

    if not cells:
        # Fallback empty cell
        cells.append([Paragraph("Chưa có vật tư nào trong kho", name_style)])

    # Arrange cells into 3-column rows
    table_matrix = []
    row = []
    for cell in cells:
        row.append(cell)
        if len(row) == 3:
            table_matrix.append(row)
            row = []
    if row:
        # Fill remaining columns in last row
        while len(row) < 3:
            row.append("")
        table_matrix.append(row)

    # Column width 175pt x 3 = 525pt (A4 printable area = 545pt)
    col_widths = [175, 175, 175]
    decal_table = Table(table_matrix, colWidths=col_widths)
    
    decal_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))

    story.append(decal_table)

    try:
        doc.build(story)
        return file_path
    except Exception as e:
        raise RuntimeError(f"Lỗi khi tạo file PDF tem nhãn A4: {e}")
