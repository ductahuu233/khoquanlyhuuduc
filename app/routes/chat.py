import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app import models

router = APIRouter(prefix="/api/chat", tags=["AI Chatbot"])

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    suggested_actions: Optional[List[str]] = []

def contains_any(text: str, keywords: List[str]) -> bool:
    for kw in keywords:
        if " " in kw:
            if kw in text:
                return True
        else:
            if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
                return True
    return False

@router.post("", response_model=ChatResponse)
def ai_chat(payload: ChatRequest, db: Session = Depends(get_db)):
    msg = payload.message.strip().lower()
    
    # 1. Fetch live database state for accurate context
    all_items = db.query(models.Item).all()
    all_requests = db.query(models.Request).all()
    exported_requests = [r for r in all_requests if r.status == 'exported']
    pending_requests = [r for r in all_requests if r.status == 'pending']
    low_stock_items = [i for i in all_items if i.current_stock < 10]
    out_of_stock_items = [i for i in all_items if i.current_stock <= 0]

    # Intent 1: Real-Time Stock Lookup / Inventory Status (Priority check if asking about items/stock)
    if contains_any(msg, ["tồn kho", "kiểm kho", "bao nhiêu", "còn hàng", "hết hàng", "bộ đàm", "đèn pin", "giấy in", "vật tư", "danh sách kho"]):
        if not all_items:
            reply = "⚠️ **Hiện tại kho chưa có dữ liệu vật tư nào!**\nCán bộ có thể nhấn nút **'Nạp Dữ Liệu Mẫu'** ở góc trên màn hình để khởi tạo nhanh dữ liệu kho."
            return ChatResponse(reply=reply, suggested_actions=["Nạp dữ liệu mẫu"])
        
        # Specific item search in question
        matching = [i for i in all_items if i.name.lower() in msg or i.item_code.lower() in msg]
        
        if matching:
            items_text = "\n".join([
                f"- **{i.item_code} - {i.name}**: Tồn kho **{i.current_stock} {i.unit}** " +
                ("🔴 *(Hết hàng)*" if i.current_stock <= 0 else ("🟡 *(Sắp hết)*" if i.current_stock < 10 else "🟢 *(An toàn)*"))
                for i in matching
            ])
            reply = f"🔍 **KẾT QUẢ TRA CỨU VẬT TƯ THEO YÊU CẦU:**\n\n{items_text}"
        else:
            items_summary = "\n".join([
                f"- **{i.item_code} - {i.name}**: **{i.current_stock} {i.unit}** " +
                ("🔴" if i.current_stock <= 0 else ("🟡" if i.current_stock < 10 else "🟢"))
                for i in all_items
            ])
            
            warning_text = ""
            if low_stock_items:
                warning_text = f"\n\n⚠️ **CẢNH BÁO:** Có **{len(low_stock_items)}** vật tư ở ngưỡng dưới 10 đơn vị cần bổ sung!"

            reply = (
                f"📊 **BÁO CÁO TỒN KHO THỜI GIAN THỰC ({len(all_items)} loại vật tư):**\n\n"
                f"{items_summary}{warning_text}\n\n"
                f"📌 Cán bộ có thể bấm trực tiếp vào từng dòng vật tư trong Tab 1 để xem mã QR & ảnh chi tiết."
            )
        return ChatResponse(reply=reply, suggested_actions=["Tạo phiếu xuất kho", "In tem QR Decal A4"])

    # Intent 2: Export Guidance & File Generation (PDF, Excel, Word)
    if contains_any(msg, ["xuất kho", "tạo file", "in báo cáo", "pdf", "excel", "word", "tờ trình", "nhật ký"]):
        reply = (
            "📄 **HƯỚNG DẪN QUY TRÌNH XUẤT KHO & KHỞI TẠO BỘ 3 FILE BÁO CÁO:**\n\n"
            "1. **Bước 1 (Lập Phiếu):** Vào **Tab 2 (Phiếu Yêu Cầu)** -> Điền *Cán bộ đề xuất, Nơi nhận (Xuất đi đâu), Lý do xuất* và chọn số lượng vật tư cần xuất.\n"
            "2. **Bước 2 (Duyệt Xuất):** Chuyển sang **Tab 3 (Duyệt Xuất Kho)** -> Chọn vai trò **👑 Admin** ở góc phải -> Chọn phiếu cần xuất -> Bấm **'PHÊ DUYỆT XUẤT KHO & IN BÁO CÁO'**.\n"
            "3. **Tự Động Sinh 3 File:** Hệ thống tự động khấu trừ kho và tạo ngay:\n"
            "   - 🔴 **PDF**: Tờ Phiếu xuất kho chính thức.\n"
            "   - 🟢 **Excel**: Sổ nhật ký xuất kho chi tiết.\n"
            "   - 🔵 **Word**: Tờ trình xuất vận dụng trình Lãnh đạo.\n\n"
            "📌 Bộ file được tự động lưu vào **Cột Lịch Sử Bên Phải Tab 3** để tải lại bất cứ lúc nào!"
        )
        return ChatResponse(reply=reply, suggested_actions=["Xem lịch sử file báo cáo", "Xem tồn kho khẩn cấp"])

    # Intent 3: Historical File Editing & Re-printing
    if contains_any(msg, ["sửa file", "in lại", "lịch sử", "sửa báo cáo", "nhầm", "sai"]):
        reply = (
            "📁 **HƯỚNG DẪN TẢI LẠI & SỬA FILE BÁO CÁO ĐÃ XUẤT KHO:**\n\n"
            "1. Vào **Tab 3 (Duyệt Xuất Kho & Lịch Sử File Báo Cáo)**.\n"
            "2. Quan sát **Cột Bên Phải Màn Hình**: Bảng *'Lịch Sử Bộ File Báo Cáo Đã Xuất'*\n"
            "3. **Tải / In Lại File:** Bấm trực tiếp vào các nút 🔴 PDF, 🟢 Excel, 🔵 Word để xem hoặc in lại.\n"
            "4. **Sửa & Tạo Lại File:** Nếu thông tin cán bộ/nơi nhận bị sai, Admin bấm nút **'✏️ Sửa'** ở cột bên phải -> Nhập thông tin chuẩn -> Bấm lưu.\n"
            "   -> Hệ thống sẽ **tự động sinh lại bộ 3 file mới** chuẩn xác mà **không trừ đúp kho**!"
        )
        return ChatResponse(reply=reply, suggested_actions=["Xem lịch sử file báo cáo", "Quyền Admin là gì"])

    # Intent 4: QR Code & Mobile Camera Scanner
    if contains_any(msg, ["qr", "quét", "camera", "chụp ảnh", "điện thoại", "ios", "android", "decal"]):
        reply = (
            "📱 **HƯỚNG DẪN QUÉT MÃ QR & CHỤP ẢNH BẰNG ĐIỆN THOẠI:**\n\n"
            "1. **Quét Mã QR Di Động:** Bấm nút **'📱 Quét Mã QR Di Động'** ở góc trên màn hình (hoặc truy cập `/scan`). Hệ thống tự kích hoạt Camera điện thoại để quét mã vạch/QR xuất kho siêu tốc!\n"
            "2. **Chụp Ảnh Vật Tư:** Khi Thêm hoặc Sửa vật tư, bấm nút **'📸 Chụp Ảnh Ngay'**. Điện thoại (iOS Safari / Android Chrome) sẽ tự hỏi xin quyền camera và tải trực tiếp ảnh chụp vào kho.\n"
            "3. **In Tem QR Decal A4:** Trong Tab 1, bấm nút **'🖨️ In Tem QR Decal A4'** để xuất file PDF chứa toàn bộ tem mã QR dán lên thiết bị kho."
        )
        return ChatResponse(reply=reply, suggested_actions=["Cách quét mã QR di động", "In tem QR Decal A4"])

    # Intent 5: RBAC & Permissions
    if contains_any(msg, ["quyền", "admin", "user", "cán bộ", "phân quyền", "bảo mật"]):
        reply = (
            "👑 **HỆ THỐNG PHÂN QUYỀN RBAC (ADMIN vs CÁN BỘ):**\n\n"
            "- 👑 **Vai Trò Admin (Quản Trị Viên):** Có toàn quyền *Thêm/Sửa/Xóa vật tư, Duyệt xuất kho sinh bộ 3 file, Sửa lịch sử file báo cáo, Upload ảnh và In tem QR*.\n"
            "- 👤 **Vai Trò Cán Bộ / Nhân Viên:** Được quyền *Xem danh mục tồn kho, Lập phiếu yêu cầu xuất kho và Quét mã QR di động*.\n\n"
            "📌 Cán bộ có thể thử nghiệm đổi vai trò ở menu **'Vai Trò'** góc trên màn hình!"
        )
        return ChatResponse(reply=reply, suggested_actions=["Xem tồn kho khẩn cấp", "Hướng dẫn xuất kho"])

    # Intent 6: Greetings / System Overview
    if contains_any(msg, ["chào", "hello", "hi", "bạn là ai", "trợ lý", "giúp", "dùng sao"]):
        reply = (
            "🫡 **Xin chào Cán bộ! Tôi là Trợ Lý AI Quản Lý Kho Nội Bộ - Bộ Công An.**\n\n"
            "Tôi có thể hỗ trợ Cán bộ các công việc sau:\n"
            "1. 📦 **Tra cứu tồn kho thực tế** & cảnh báo vật tư sắp hết hàng.\n"
            "2. 📄 **Hướng dẫn lập phiếu xuất & sinh bộ 3 file** (PDF, Excel, Word).\n"
            "3. 📁 **Quản lý lịch sử file báo cáo** & hướng dẫn Sửa / In lại file.\n"
            "4. 📷 **Hướng dẫn chụp ảnh di động & quét mã QR** vật tư.\n"
            "5. 👑 **Giải đáp phân quyền Admin / Cán bộ**.\n\n"
            "Cán bộ cần hỗ trợ thông tin gì ạ?"
        )
        return ChatResponse(
            reply=reply, 
            suggested_actions=["Xem tồn kho khẩn cấp", "Hướng dẫn xuất kho", "Cách quét mã QR di động"]
        )

    # Fallback / Custom queries
    reply = (
        f"🤖 **Trợ lý AI đã ghi nhận thắc mắc của Cán bộ:** *'{payload.message}'*\n\n"
        f"Hiện tại hệ thống đang quản lý **{len(all_items)}** loại vật tư và **{len(exported_requests)}** phiếu xuất kho thành công.\n"
        f"Cán bộ có thể chọn các gợi ý bên dưới hoặc hỏi chi tiết hơn về *tồn kho, quy trình xuất kho, quét mã QR di động, hoặc sửa file báo cáo* ạ!"
    )
    return ChatResponse(
        reply=reply,
        suggested_actions=["Xem tồn kho khẩn cấp", "Hướng dẫn xuất kho", "Cách quét mã QR di động"]
    )
