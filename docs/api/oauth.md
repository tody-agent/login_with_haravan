---
title: API - OAuth Callback
description: Tài liệu tham khảo API endpoint chính cho OAuth
keywords: api, oauth, callback
robots: index, follow
---

# 🔌 API: OAuth Callback

:::info Tóm tắt
Tài liệu tham khảo cho endpoint xử lý callback từ Haravan.
:::

## `GET /api/method/login_with_haravan.oauth.login_via_haravan`

Đây là endpoint cốt lõi, nằm trong Whitelist API của Frappe. Nó không yêu cầu đăng nhập (`allow_guest=True`).

### Parameters (Query)
- `code` (string): Authorization code trả về từ Haravan.
- `state` (string): Chuỗi mã hóa chứa CSRF token và thông tin chuyển hướng (`redirect_to`).

### Xử lý (Logic Flow)
1. Xác thực `code` và `state`.
2. Gắn kết đè (override) `redirect_to` nếu có cookie `haravan_login_redirect_to`.
3. Gọi `fetch_haravan_info_and_token` để lấy Access Token.
4. Định dạng profile qua `normalize_haravan_profile`.
5. Đăng nhập user vào Frappe.
6. Xử lý lưu trữ bất đồng bộ (Persistence): Gọi `enrich_helpdesk_data` để tạo HD Customer và Contact từ claim đăng nhập tối thiểu.

Luồng OAuth không gọi Haravan commerce/shop API nữa. Hồ sơ khách hàng giàu dữ liệu được lấy từ Bitrix khi agent mở Customer Profile.

### Error Handling
Nếu có lỗi, sẽ ghi vào **Error Log** của Frappe với tiêu đề `Haravan social login failed`.
