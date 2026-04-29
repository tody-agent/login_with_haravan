---
title: Quy trình Triển khai (Deployment Workflow)
description: Hướng dẫn chi tiết quy trình viết code, đẩy lên GitHub và deploy lên Frappe Cloud.
keywords: deployment, workflow, github, frappe cloud, migrate
robots: index, follow
---

# 🚀 Quy trình Triển khai (Deployment Workflow)

:::info Mục tiêu
Tài liệu này hướng dẫn chi tiết quy trình End-to-End từ lúc Developer viết code/sửa app ở máy cá nhân (Local), đẩy code lên **GitHub**, cho đến việc cập nhật và deploy ứng dụng đó lên **Frappe Cloud**.
:::

## 1. Giai đoạn 1: Lập trình và Cập nhật App (Local)

Mọi quá trình phát triển (viết tính năng mới, fix bug, thêm Custom Fields) đều phải được thực hiện và kiểm thử trên môi trường local trước.

### 1.1. Viết Code
- **Logic & API:** Thay đổi hoặc viết mới tại thư mục `login_with_haravan/engines/` hoặc `oauth.py`.
- **Database Schema:** Nếu cần thêm trường dữ liệu (Custom Fields) vào `HD Customer`, hãy định nghĩa chúng trong `login_with_haravan/setup/install.py` thông qua hook `after_migrate`. Việc này đảm bảo khi deploy lên production, lệnh migrate sẽ tự động tạo bảng mà không cần thao tác tay.

### 1.2. Kiểm thử (Testing)
Trước khi push code, bạn bắt buộc phải chạy bộ test cục bộ để tránh làm hỏng các luồng OAuth hiện tại:
```bash
# Chạy Unit Tests
PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v
```
*(Nếu source code có file `./test_gate.sh`, hãy chạy nó).*

---

## 2. Giai đoạn 2: Quản lý Phiên bản (Đẩy lên GitHub)

Frappe Cloud hoạt động dựa trên cơ chế kéo code (pull) trực tiếp từ kho lưu trữ GitHub. Do đó, việc cập nhật GitHub là bắt buộc.

### 2.1. Cập nhật mã nguồn
Sau khi code chạy ổn định trên local:
```bash
git add .
git commit -m "feat: [Mô tả tính năng bạn vừa làm]"
git push origin main
```

*(Lưu ý: Đối với dự án này, nếu có quy định làm việc qua nhánh tính năng (feature branches), hãy tạo PR và merge vào `main`. Khuyến nghị sử dụng kịch bản `./ship.sh` nếu có).*

---

## 3. Giai đoạn 3: Triển khai trên Frappe Cloud

Frappe Cloud chia làm 2 cấp độ: **Bench** (Nơi chứa mã nguồn của các App) và **Site** (Nơi lưu database của từng khách hàng).

### 3.1. Thêm App mới vào Frappe Cloud (Dành cho cài đặt lần đầu)
Nếu app `login_with_haravan` chưa từng có mặt trên Frappe Cloud:
1. Đăng nhập vào [Frappe Cloud Dashboard](https://frappecloud.com/dashboard).
2. Chuyển đến tab **Apps** trên thanh điều hướng bên trái -> Chọn **New App**.
3. Chọn nhà cung cấp là **GitHub** -> Tìm repo `tody-agent/login_with_haravan` và chọn nhánh `main`.
4. Nhấn **Validate** để Frappe Cloud kiểm tra tính hợp lệ của App (file `hooks.py`, `setup.py`).
5. Thêm App này vào một **Bench** cụ thể đang chạy phiên bản Frappe Framework tương ứng (ví dụ v15).

### 3.2. Cập nhật (Update) App đã có
Khi bạn đã push code mới lên GitHub, bạn cần báo cho Bench biết để tải code về:
1. Mở Frappe Cloud Dashboard.
2. Truy cập vào **Benches** -> Chọn Bench chứa app của bạn.
3. Chuyển sang tab **Apps**.
4. Nhấn vào nút **Update** (hoặc Fetch Updates) để Bench lấy (pull) commit mới nhất từ nhánh `main` của GitHub về.

### 3.3. Deploy Migration cho Bản App mới (Site Update)
Sau khi Bench đã có mã nguồn mới, cơ sở dữ liệu trên Site vẫn là phiên bản cũ. Bạn phải chạy tiến trình **Migrate**:
1. Từ Frappe Cloud, chuyển đến tab **Sites**.
2. Chọn site đích (ví dụ: `haravandesk.s.frappe.cloud`).
3. Ở góc phải trên cùng, nhấn nút **Update** (Đôi khi nút này hiển thị tên là Deploy hoặc Migrate).
4. **Tiến trình này sẽ:**
   - Đưa site vào chế độ bảo trì (Maintenance Mode).
   - Cập nhật mã nguồn mới nhất từ Bench.
   - Chạy lệnh `bench migrate`: Lệnh này sẽ kích hoạt hook `after_migrate` trong file `install.py` của bạn để tạo/xóa các bảng DB mới.
   - Dọn dẹp Cache và khởi động lại dịch vụ.

:::tip Kiểm tra Lịch sử Deploy
Nếu sau khi Update mà tính năng mới không chạy, hãy vào tab **Jobs** của Site đó trên Frappe Cloud để xem log chi tiết của tiến trình `bench migrate` xem có lỗi cú pháp Python hay lỗi SQL nào bị từ chối không.
:::
