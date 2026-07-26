import os
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

OUTPUT_DIR = os.path.join(os.getcwd(), "exports")
DEFAULT_EXCEL_PATH = os.path.join(OUTPUT_DIR, "bao_cao_xuat_kho.xlsx")

def generate_excel(export_data: dict) -> str:
    """
    Append dữ liệu xuất kho mới vào file Báo cáo Excel.
    Sử dụng try-except xử lý I/O file an toàn chống crash server khi file bị mở bởi ứng dụng khác.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    file_path = DEFAULT_EXCEL_PATH

    # If file exists, load it; otherwise create a new workbook
    if os.path.exists(file_path):
        try:
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
        except Exception as e:
            # Fallback if corrupt or readable error
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Nhật Ký Xuất Kho"
            _create_headers(ws)
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Nhật Ký Xuất Kho"
        _create_headers(ws)

    # Determine next STT
    last_row = ws.max_row
    stt = 1
    if last_row > 1:
        val = ws.cell(row=last_row, column=1).value
        if isinstance(val, int):
            stt = val + 1

    request_id = export_data.get("request_id", "")
    export_date = export_data.get("export_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    requester = export_data.get("requester_name", "")
    destination = export_data.get("destination", "N/A")
    reason = export_data.get("reason", "N/A")
    items = export_data.get("items", [])

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    for item in items:
        row_data = [
            stt,
            f"PXK-{request_id}",
            export_date,
            requester,
            destination,
            reason,
            item.get("item_code", ""),
            item.get("name", ""),
            item.get("unit", ""),
            item.get("quantity", 0)
        ]
        ws.append(row_data)
        stt += 1

        # Format appended row
        current_row = ws.max_row
        for col_num in range(1, 11):
            cell = ws.cell(row=current_row, column=col_num)
            cell.border = thin_border
            if col_num in [1, 2, 3, 7, 9, 10]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # Save Excel file safely with try-except
    try:
        wb.save(file_path)
        return file_path
    except PermissionError:
        # File is opened in MS Excel or locked! Create a timestamped fallback file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback_path = os.path.join(OUTPUT_DIR, f"bao_cao_xuat_kho_{timestamp}.xlsx")
        wb.save(fallback_path)
        return fallback_path
    except Exception as e:
        raise RuntimeError(f"Lỗi không xác định khi lưu file Excel: {e}")

def _create_headers(ws):
    headers = [
        "STT", "Mã Phiếu", "Ngày Xuất", "Người Yêu Cầu", "Đơn Vị Nhận (Xuất Đi)", "Lý Do Xuất",
        "Mã Vật Tư", "Tên Vật Tư", "Đơn Vị Tính", "Số Lượng Xuất"
    ]
    ws.append(headers)
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    
    for col_num in range(1, 11):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Column widths
    col_widths = [8, 15, 20, 22, 25, 25, 15, 30, 15, 15]
    for i, col_width in enumerate(col_widths, start=1):
        col_letter = openpyxl.utils.get_column_letter(i)
        ws.column_dimensions[col_letter].width = col_width
