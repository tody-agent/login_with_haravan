---
title: API - Customer Profile
description: API hồ sơ khách hàng lấy dữ liệu Bitrix theo nhu cầu
keywords: api, customer profile, bitrix, helpdesk
robots: index, follow
---

# API: Customer Profile

## `GET /api/method/login_with_haravan.customer_profile.get_ticket_customer_profile`

Trả hồ sơ khách hàng cho ticket agent đang xem. Endpoint kiểm tra quyền đọc `HD Ticket`, lấy `HD Customer` và `Contact` liên quan, sau đó gọi Bitrix server-side nếu cấu hình đang bật.

### Parameters

- `ticket` (string): Mã `HD Ticket`.
- `refresh` (0/1): Ép lấy lại dữ liệu từ Bitrix.

### Response

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
      "company": {},
      "contact": {}
    }
  },
  "message": "Customer profile loaded."
}
```

Bitrix token/webhook URL không bao giờ được trả về browser.

## `POST /api/method/login_with_haravan.customer_profile.refresh_customer_profile`

Làm mới hồ sơ theo `HD Customer` và optional `Contact`.
