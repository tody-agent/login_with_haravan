---
title: API — Hồ sơ khách hàng
description: API lấy hồ sơ khách hàng chi tiết từ Bitrix theo nhu cầu agent
keywords: api, hồ sơ khách hàng, customer profile, bitrix, helpdesk
robots: index, follow
---

# 👤 API: Hồ sơ khách hàng

:::info Tóm tắt
Các API phục vụ panel Customer Profile trên giao diện agent. Dữ liệu chi tiết được lấy từ Bitrix theo nhu cầu — không nằm trong callback đăng nhập.
:::

## `GET /api/method/haravan_bitrix_customer_profile`

Endpoint production của Server Script `Profile - Bitrix Customer API`. Endpoint kiểm tra quyền đọc `HD Ticket`, lấy `HD Customer` và `Contact` liên quan, tạo danh sách ứng viên Haravan Company ID từ ticket/customer, rồi gọi Bitrix server-side bằng `crm.company.list` filter `UF_CRM_COMPANY_ID` nếu cấu hình đang bật. Bitrix internal `ID` chỉ dùng để build link details.

### Tham số

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|:--------:|-------|
| `ticket` | string | ✅ | Mã `HD Ticket` |
| `refresh` | 0/1 | ❌ | Ép lấy lại dữ liệu từ Bitrix |

### Phản hồi

```json
{
  "success": true,
  "data": {
    "customer": {},
    "contact": {},
    "haravan": [],
    "bitrix": {
      "enabled": true,
      "configured": true,
      "status": "matched",
      "cached": false,
      "lookup_candidates": ["200000317825", "1900000017"],
      "lookup_value": "1900000017",
      "company": {},
      "contact": {},
      "responsible": {
        "id": "338",
        "active": true,
        "email": "agent@example.com",
        "name": "Nguyen An",
        "user_type": "employee",
        "status": "active"
      }
    }
  },
  "message": "Customer profile loaded."
}
```

| Trường | Mô tả |
|--------|-------|
| `data.customer` | Thông tin `HD Customer` |
| `data.contact` | Thông tin `Contact` |
| `data.bitrix.enabled` | Tích hợp Bitrix có đang bật không |
| `data.bitrix.configured` | Webhook Bitrix đã được cấu hình server-side chưa |
| `data.bitrix.status` | Trạng thái: `disabled`, `missing_config`, `missing_orgid`, `matched`, `not_found`, `error`, `cached` |
| `data.bitrix.cached` | Response đang dùng cache trong TTL |
| `data.bitrix.lookup_candidates` | Các Haravan Company ID đã thử theo thứ tự ưu tiên |
| `data.bitrix.lookup_value` | Candidate cuối cùng dùng cho match hoặc candidate cuối cùng đã thử |
| `data.bitrix.company` | Dữ liệu công ty Bitrix đã normalize, gồm `bitrix_id`, `company_id`, `company_name`, HSI, Shopplan, `url` |
| `data.bitrix.contact` | Dữ liệu contact từ Bitrix |
| `data.bitrix.responsible` | User phụ trách resolve từ `ASSIGNED_BY_ID` qua `user.get`; nếu `active = true`, tên được ghi vào `HD Ticket.custom_responsible` |

:::warning Bảo mật
Bitrix token/webhook URL **không bao giờ** được trả về browser. Production đọc `bitrix_webhook_url` cho customer/company và `bitrix_responsible_webhook_url` cho responsible từ `Helpdesk Integrations Settings` bằng `get_password()`; mọi gọi Bitrix đều thực hiện server-side.
:::

## Legacy app endpoint

`GET /api/method/login_with_haravan.customer_profile.get_ticket_customer_profile` vẫn tồn tại trong custom app cho panel phụ, nhưng HD Form Script production hiện gọi `haravan_bitrix_customer_profile`.

## `POST /api/method/login_with_haravan.customer_profile.refresh_customer_profile`

Làm mới hồ sơ theo `HD Customer` và optional `Contact`. Gọi lại Bitrix để cập nhật dữ liệu mới nhất.

### Tham số

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|:--------:|-------|
| `hd_customer` | string | ✅ | Tên `HD Customer` |
| `contact` | string | ❌ | Tên `Contact` (nếu muốn refresh cụ thể) |
