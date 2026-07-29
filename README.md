# 🏛️ HỆ THỐNG QUẢN LÝ KHO KỸ THUẬT & VÒNG ĐỜI TÀI SẢN (LEVEL MAX v4.0)
### 👮‍♂️ ĐOÀN NGHI LỄ CÔNG AN NHÂN DÂN — BỘ TƯ LỆNH CẢNH SÁT CƠ ĐỘNG

> **Hệ thống Quản lý Kho Kỹ Thuật, Vật Tư & Vòng Đời Tài Sản Nội Bộ** chuẩn hóa theo **Nghị định 30/2020/NĐ-CP** và quy định quản lý tài sản công của **Bộ Công An**. Tích hợp tìm kiếm phím tắt `Ctrl + K`, Bản đồ kho Grid 3D, Quét mã QR di động siêu tốc và bảo mật mã hóa SHA-256 Air-Gapped Local LAN.

---

## 🌟 CÁC TÍNH NĂNG NỔI BẬT (FEATURES LEVEL MAX v4.0)

- 🔒 **Bảo Mật Nội Bộ Air-Gapped Local LAN**: Đăng nhập mã hóa SHA-256 nội bộ, hỗ trợ 3 nhóm vai trò phân quyền chi tiết (`Admin`, `Thủ Kho`, `Cán Bộ`).
- ⌨️ **Thanh Điều Hành Siêu Tốc `Ctrl + K` (Command Palette)**: Nhấn `Ctrl + K` ở bất kỳ đâu để bật thanh tìm kiếm thông minh 1-click truy cập tức thì mọi vật tư và chức năng.
- 🗺️ **Bản Đồ Kho Grid 3D (Interactive Visual Grid)**: Trực quan hóa Kho Kỹ Thuật theo từng dãy Kệ kho (A1, A2, B1, C1), nhấp chọn kệ để lọc ngay danh sách vật tư thực tế.
- 📱 **Quét Mã QR Di Động Hàng Loạt (`/scan`)**: Sử dụng camera điện thoại quét liên tục mã QR kiểm kê & in tem mã decal A4 tự động.
- 📑 **Trích Xuất Văn Bản Chuẩn Nghị Định 30 & Bộ Công An**: Tự động tạo file Word `.docx` và Excel `.xlsx` cho phiếu Nhập kho (C30-HD), Xuất kho (C31-HD), Bàn giao (C32-HD), Kiểm kê (01/TSC).
- 🌙 **Hỗ Trợ Giao Diện Tối / Sáng (Dark / Light Theme)**: Tùy chỉnh chế độ hiển thị với thiết bị lưu `localStorage`.
- 🔄 **Loading Spinner Giữa Màn Hình & Real-Time API Refresh**: Tự động hiển thị Icon Loading Spinner chính giữa màn hình khi chuyển Tab và kết nối CSDL làm mới dữ liệu thời gian thực.

---

## 📖 HƯỚNG DẪN SỬ DỤNG CHI TIẾT (USER MANUAL)

### 🔑 1. Đăng Nhập Hệ Thống
1. Truy cập địa chỉ web: **`http://127.0.0.1:8000/login`**
2. Sử dụng 1 trong 3 tài khoản mặc định được phân quyền:
   - 👑 **Tài khoản Admin (Quản trị viên)**: Username: `admin` | Password: `admin123`
   - 📦 **Tài khoản Thủ Kho**: Username: `thukho` | Password: `thukho123`
   - 👤 **Tài khoản Cán Bộ / Nhân Viên**: Username: `canbo` | Password: `canbo123`

---

### 💻 2. Hướng Dẫn Thao Tác Các Tab Chức Năng (Tab 0 ➔ Tab 7)

- **📊 Tab 0. Dashboard AI**: Xem tổng quan KPIs kho, biểu đồ phân tích và AI dự báo bảo dưỡng định kỳ.
- **📦 Tab 1. Danh Mục Kho**: Tìm kiếm, thêm mới vật tư, chỉnh sửa định mức tồn kho tối thiểu.
- **📋 Tab 2. Yêu Cầu Xuất Kho**: Cán bộ gửi yêu cầu xin cấp phát vật tư/trang bị, Admin/Thủ kho duyệt 1-click.
- **📄 Tab 3. Duyệt Xuất & Trích Xuất Báo Cáo**: Tạo phiếu xuất kho chính thức và trích xuất file Word/PDF/Excel.
- **🚚 Tab 4. Nhập Kho Lô & Tem QR**: Nhập danh mục vật tư hàng loạt, tự động sinh mã QR và in tem decal A4.
- **🚨 Tab 5. Phế Phẩm & Thanh Lý (NĐ30)**: Báo hỏng thiết bị, quản lý kho phế phẩm và sinh Biên bản thanh lý theo Nghị định 30.
- **📈 Tab 6. Thẻ Kho & Kiểm Kê**: Xem lịch sử vết thẻ kho và so khớp chênh lệch kiểm kê thực tế.
- **🗺️ Tab 7. Bản Đồ Kho Grid 3D**: Nhấp chuột vào từng kệ kho (Kệ A1, A2, B1, C1) để xem ngay vật tư lưu trữ.

---

### ⚡ 3. Hướng Dẫn Thao Tác Nhanh Bằng Phím Tắt
- **Bấm `Ctrl + K`**: Bật thanh tìm kiếm siêu tốc ở bất kỳ màn hình nào ➔ Gõ tên vật tư hoặc tên chức năng ➔ Bấm `Enter` để mở ngay.
- **Bấm `ESC`**: Đóng thanh tìm kiếm hoặc các hộp thoại Modal.

---

### 📱 4. Quét Mã QR Bằng Điện Thoại Di Động
1. Mở trình duyệt trên điện thoại kết nối chung Wi-Fi/LAN nội bộ: **`http://<IP_MAY_CHU>:8000/scan`**
2. Cho phép camera hoạt động ➔ Đưa camera quét mã QR dán trên thiết bị ➔ Hệ thống tự động báo tiếng "Beep" và ghi nhận thông tin tài sản!

---

## ⚙️ HƯỚNG DẪN CÀI ĐẶT & CHẠY MÁY CHỦ (INSTALLATION)

### 1. Yêu Cầu Môi Trường:
- **Python**: 3.10 trở lên
- **Hệ điều hành**: Windows 10/11, Linux, macOS
- **Trình duyệt**: Chrome, Edge, Firefox, Safari

### 2. Lệnh Khởi Chạy Máy Chủ:
```bash
# 1. Kích hoạt môi trường ảo (nếu có)
.venv\Scripts\activate

# 2. Khởi chạy máy chủ Uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- Mở trình duyệt truy cập: **`http://127.0.0.1:8000`**

---

## 🏛️ ĐƠN VỊ SỬ DỤNG
**ĐOÀN NGHI LỄ CÔNG AN NHÂN DÂN — BỘ TƯ LỆNH CẢNH SÁT CƠ ĐỘNG**
*Phần mềm quản lý kho kỹ thuật & vòng đời tài sản nội bộ.*
