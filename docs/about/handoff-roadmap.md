---
title: Bàn giao & Lộ trình phát triển
description: Tài liệu bàn giao dành cho Developer tiếp quản và lộ trình cải tiến tích hợp Frappe × Haravan.
keywords: bàn giao, handoff, roadmap, bảo trì, haravan
robots: index, follow
---

# 🤝 Bàn giao & Lộ trình phát triển

:::info Mục tiêu
Tài liệu này dành cho **Haravan Developers** (hoặc đội ngũ lập trình viên tiếp quản) để nắm rõ hiện trạng, cách bảo trì, và lộ trình phát triển ứng dụng `Frappe x Haravan`.
:::

## 1. Hiện trạng hệ thống

Ứng dụng `Frappe x Haravan` hiện đảm nhận 2 vai trò cốt lõi:

1. **SSO Identity Provider** — Cầu nối OAuth 2.0 cho Frappe Helpdesk, cho phép merchant đăng nhập một chạm từ hệ sinh thái Haravan.
2. **Helpdesk Identity Link** — Lưu định danh tối thiểu từ Haravan Account (`userid`, `email`, `orgid`) để tạo phiên đăng nhập, liên kết `Haravan Account Link`, `HD Customer`, và `Contact`.

Hệ thống hiện là luồng **login-only**. Dữ liệu hồ sơ chi tiết cho agent Helpdesk được lấy theo nhu cầu từ Bitrix Customer Profile — không còn gọi Haravan commerce/shop API trong callback đăng nhập.

## 2. Hướng dẫn bảo trì

### 2.1. Nguyên tắc source code

- **Không sửa core** của Frappe hay Frappe Helpdesk. Mọi logic tuỳ biến phải nằm trong ứng dụng `login_with_haravan`.
- Thêm Custom Field vào DocType có sẵn (như `HD Customer`) bằng cách định nghĩa trong `login_with_haravan/setup/install.py` (hook `after_migrate`).
- Tuân thủ [cấu trúc 7-Layer Frappe](/architecture/overview).

### 2.2. Quy trình phát triển & kiểm thử

Mọi thay đổi code cần kiểm thử trước khi deploy:

```bash
# Chạy Unit Tests cục bộ
PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v
```

Khuyến nghị sử dụng `./test_gate.sh` hoặc `npm run ship` để tự động hoá kiểm tra và ship code. Xem chi tiết tại [Triển khai lên Production](/guide/deployment).

### 2.3. Mở rộng trường dữ liệu

Nếu cần thêm trường từ Haravan (ví dụ: `phone_number`):

1. Xác minh trường nằm trong login/userinfo scope hiện có hay cần scope mới.
2. Sửa `engines/sync_helpdesk.py` (hàm `upsert_hd_customer` hoặc `create_contact`) để map trường mới.
3. **Viết test trước**, rồi chạy `./test_gate.sh`.

## 3. Lộ trình cải tiến

### Pha 1: Tích hợp dữ liệu bán hàng (Omnichannel Sync)

- **Vấn đề:** Helpdesk chỉ biết khách hàng là ai, chưa biết họ kinh doanh ra sao hay có lỗi đơn hàng nào không.
- **Giải pháp:** Bổ sung Haravan commerce API khi có yêu cầu sản phẩm rõ ràng. Thêm scope riêng, test bảo mật riêng, và **không trộn** vào callback login-only hiện tại.

### Pha 2: Webhook thời gian thực & Tự động hóa SLA

- **Vấn đề:** SLA và phân tuyến ticket cần dữ liệu vận hành đáng tin cậy, nhưng callback OAuth không nên chứa logic đồng bộ nặng.
- **Giải pháp:** Thiết kế webhook hoặc scheduled sync riêng, tách khỏi OAuth callback. Ghi log bằng `frappe.log_error()`.

### Pha 3: Haravan Admin App (Ứng dụng nhúng)

- **Vấn đề:** Merchant phải rời trang quản trị Haravan để truy cập `haravan.help` tạo ticket.
- **Giải pháp:** Dùng Haravan App SDK nhúng giao diện tạo Ticket của Frappe thẳng vào Dashboard Haravan — trải nghiệm hỗ trợ liền mạch 100%.
