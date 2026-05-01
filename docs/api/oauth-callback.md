---
title: API — OAuth Callback
description: Tài liệu tham chiếu cho endpoint xử lý callback OAuth từ Haravan
keywords: api, oauth, callback, endpoint
robots: index, follow
---

# 🔌 API: OAuth Callback

:::info Tóm tắt
Endpoint cốt lõi xử lý callback từ Haravan. Nằm trong Whitelist API của Frappe, không yêu cầu đăng nhập (`allow_guest=True`).
:::

## `GET /api/method/login_with_haravan.oauth.login_via_haravan`

### Tham số (Query)

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|:--------:|-------|
| `code` | string | ✅ | Authorization code trả về từ Haravan |
| `state` | string | ✅ | Chuỗi mã hóa chứa CSRF token và `redirect_to` |

### Luồng xử lý

1. **Xác thực** `code` và `state`.
2. **Ghi đè** `redirect_to` nếu có cookie `haravan_login_redirect_to`.
3. **Lấy token:** Gọi `fetch_haravan_info_and_token` để lấy Access Token.
4. **Chuẩn hóa:** Định dạng profile qua `normalize_haravan_profile`.
5. **Đăng nhập:** Đăng nhập user vào Frappe.
6. **Lưu trữ:** Gọi `enrich_helpdesk_data` để tạo/cập nhật HD Customer và Contact từ claim đăng nhập tối thiểu.

:::warning Lưu ý kiến trúc
Luồng OAuth **không** gọi Haravan commerce/shop API. Hồ sơ khách hàng chi tiết được lấy từ Bitrix khi agent mở Customer Profile.
:::

### Xử lý lỗi

Nếu có lỗi, hệ thống ghi vào **Error Log** của Frappe với tiêu đề `Haravan social login failed`. Log bao gồm trường `stage` cho biết giai đoạn xảy ra lỗi.

Xem chi tiết tại [Khắc phục sự cố](/guide/troubleshooting#_5-loi-417-uncaught-exception-sau-khi-goi-callback).
