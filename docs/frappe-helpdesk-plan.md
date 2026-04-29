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
2. **Profile Sync Engine:** Tự động lắng nghe và trích xuất dữ liệu tổ chức (OrgID, Shop Plan, Domain) từ Haravan Profile để tạo hoặc cập nhật thông tin `HD Customer` trong Frappe Helpdesk.

Hệ thống đã đạt mức **Production-ready** cho nhu cầu xác thực và phân luồng ticket. Một số tính năng dữ liệu nâng cao đã được hoàn thiện:
- Quản lý Ticket theo Role: Tự động phân quyền xem toàn bộ ticket cho `owner`/`admin` và thu hẹp scope cho nhân viên (`staff`).
- Đồng bộ Ngày kích hoạt (First Paid Date): Lấy từ API Subscription và fallback thông minh về ngày tạo Shop để hỗ trợ chia team theo thời gian vòng đời.

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
- **Giải pháp:** Bổ sung API gọi sang `Haravan OmniPower` để kéo danh sách đơn hàng (Orders) gần nhất của tổ chức đó hiển thị vào Frappe Helpdesk (có thể tạo một Custom HTML field trên Ticket).

### Pha 2: Real-time Webhooks & SLA Automation
- **Vấn đề:** `Shop Plan` (Gói dịch vụ Scale/Growth) chỉ được cập nhật khi người dùng đăng nhập lại (Login event). Nếu họ nâng cấp gói nhưng không đăng xuất/đăng nhập, Helpdesk sẽ không biết.
- **Giải pháp:** Viết một endpoint `login_with_haravan.webhooks.receive_org_update` để nhận Webhook từ Haravan. Khi Merchant nâng cấp gói, tự động điều chỉnh SLA tương ứng trong Frappe Helpdesk.

### Pha 3: Haravan Admin App (Embedded Mini-App)
- **Vấn đề:** Merchant phải rời khỏi trang quản trị Haravan để truy cập `haravandesk.s.frappe.cloud` để tạo ticket.
- **Giải pháp:** Sử dụng Haravan App SDK để nhúng (embed) một giao diện tạo Ticket của Frappe thẳng vào Dashboard của Haravan, giúp trải nghiệm hỗ trợ liền mạch 100%.

## 4. Góp ý & Mở rộng Logic (Extending Logic)
Nếu cần thêm một trường dữ liệu từ Haravan (ví dụ: `phone_number`):
1. Sửa file `engines/haravan_api.py` để yêu cầu thêm scope cần thiết.
2. Sửa `engines/sync_helpdesk.py` (hàm `upsert_hd_customer` hoặc `create_contact`) để map trường dữ liệu mới vào DB của Frappe.
3. Chạy `bench migrate` để áp dụng.
