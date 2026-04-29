---
title: User Personas
description: Hồ sơ người dùng và khách hàng của ứng dụng
keywords: personas, ux, users
robots: index, follow
---

# 👥 Personas (Hồ sơ người dùng)

:::info Tóm tắt
Hai đối tượng chính tương tác với ứng dụng: System Admin (Cài đặt) và Merchant (Người dùng cuối).
:::

## 1. Technical Admin (Người triển khai)
- **Mục tiêu:** Tích hợp Haravan SSO vào Frappe Helpdesk mà không gặp lỗi `invalid_redirect_uri`.
- **Nỗi đau (Pain Points):** Cấu hình OAuth phức tạp, mismatch URL, thiếu logs rõ ràng.
- **Hành vi:** Đọc log qua Frappe Error Log, kiểm tra Site Config.

## 2. Haravan Merchant (Người dùng cuối)
- **Mục tiêu:** Đăng nhập vào cổng hỗ trợ (Helpdesk Portal) để tạo ticket nhanh chóng bằng tài khoản Haravan hiện có.
- **Nỗi đau:** Không muốn tạo thêm tài khoản mới, muốn ticket được tự động gắn với đúng cửa hàng (org) của mình.
- **Kỳ vọng:** Quá trình chỉ cần 1 click, tự động phân luồng đúng.
