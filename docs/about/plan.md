---
title: Bàn giao & Kế hoạch Phát triển (Handoff & Roadmap)
description: Tài liệu bàn giao dành cho Developer và định hướng phát triển tích hợp Frappe x Haravan trong tương lai.
keywords: handoff, dev, roadmap, maintain, haravan
robots: index, follow
---

# 🤝 Bàn giao & Kế hoạch Phát triển

:::info Mục tiêu
Tài liệu này được thiết kế dành riêng cho **Haravan Developers** (hoặc đội ngũ lập trình viên tiếp quản) để hiểu rõ hiện trạng ứng dụng `login_with_haravan`, cách bảo trì, và lộ trình phát triển để cải tiến sự kết nối giữa Frappe và Haravan.
:::

## 1. Hiện trạng Hệ thống (Current State)
Ứng dụng `login_with_haravan` hiện tại đảm nhận 2 vai trò cốt lõi:
1. **SSO Identity Provider:** Đóng vai trò là cầu nối OAuth 2.0 cho Frappe Helpdesk, cho phép các merchant đăng nhập một chạm từ hệ sinh thái Haravan.
2. **Helpdesk Identity Link:** Lưu định danh tối thiểu từ Haravan Account (`userid`, `email`, `orgid`) để tạo phiên đăng nhập, liên kết `Haravan Account Link`, `HD Customer`, và `Contact`.

Hệ thống hiện là luồng **login-only**. Dữ liệu hồ sơ giàu hơn cho agent Helpdesk được enrich theo nhu cầu từ Bitrix Customer Profile, không còn lấy từ Haravan commerce/shop API trong callback đăng nhập.

## 2. Hướng dẫn Bảo trì (Maintenance Guide)

Để tiếp tục maintain và fix bug, developer cần nắm rõ các quy tắc sau:

### 2.1. Cấu trúc Source Code (Tuân thủ 7-Layer Frappe)
- Tuyệt đối **không sửa core** của Frappe hay Frappe Helpdesk. Mọi logic tuỳ biến phải nằm trong ứng dụng `login_with_haravan`.
- Thêm Custom Field vào các DocType có sẵn (như `HD Customer`) bằng cách định nghĩa trong `login_with_haravan/setup/install.py` (hook `after_migrate`).

### 2.2. Luồng Phát triển & Kiểm thử (Dev Workflow)
Mọi thay đổi code cần phải được kiểm thử nghiêm ngặt trước khi deploy:
```bash
# Chạy Unit Tests cục bộ để đảm bảo không phá vỡ logic OAuth và Sync
PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v
```
Khuyến nghị sử dụng kịch bản `./test_gate.sh` hoặc `./ship.sh` nếu có để tự động hoá quá trình kiểm tra.

## 3. Lộ trình Cải tiến (Future Improvements)

Để nâng tầm sự kết nối giữa Frappe và Haravan, dưới đây là các tính năng kỹ thuật mà Developer tiếp theo nên cân nhắc triển khai:

### Pha 1: Tích hợp Dữ liệu Bán hàng (Omnichannel Sync)
- **Vấn đề:** Hiện tại Helpdesk chỉ biết khách hàng là ai, chưa biết họ đang kinh doanh ra sao, có bị lỗi đơn hàng nào không.
- **Giải pháp:** Chỉ bổ sung Haravan commerce API khi có yêu cầu sản phẩm rõ ràng. Nếu triển khai, thêm scope riêng, test bảo mật riêng, và không trộn vào callback login-only hiện tại.

### Pha 2: Real-time Webhooks & SLA Automation
- **Vấn đề:** SLA và phân tuyến ticket cần dữ liệu vận hành đáng tin cậy, nhưng callback OAuth không nên trở thành nơi đồng bộ dữ liệu nặng.
- **Giải pháp:** Thiết kế webhook hoặc scheduled sync riêng nếu cần, tách khỏi OAuth callback và ghi log bằng `frappe.log_error()`.

### Pha 3: Haravan Admin App (Embedded Mini-App)
- **Vấn đề:** Merchant phải rời khỏi trang quản trị Haravan để truy cập `haravan.help` để tạo ticket.
- **Giải pháp:** Sử dụng Haravan App SDK để nhúng (embed) một giao diện tạo Ticket của Frappe thẳng vào Dashboard của Haravan, giúp trải nghiệm hỗ trợ liền mạch 100%.

## 4. Góp ý & Mở rộng Logic (Extending Logic)
Nếu cần thêm một trường dữ liệu từ Haravan (ví dụ: `phone_number`):
1. Xác minh trường đó nằm trong login/userinfo scope hiện có hay cần scope mới.
2. Sửa `engines/sync_helpdesk.py` (hàm `upsert_hd_customer` hoặc `create_contact`) để map trường dữ liệu mới vào DB của Frappe.
3. Cập nhật test trước, rồi chạy `./test_gate.sh`.
