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

## `GET /api/method/login_with_haravan.customer_profile.get_ticket_customer_profile`

Trả hồ sơ khách hàng cho ticket mà agent đang xem. Endpoint kiểm tra quyền đọc `HD Ticket`, lấy `HD Customer` và `Contact` liên quan, sau đó gọi Bitrix server-side nếu cấu hình đang bật.

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
      "company": {},
      "contact": {}
    }
  },
  "message": "Customer profile loaded."
}
```

| Trường | Mô tả |
|--------|-------|
| `data.customer` | Thông tin `HD Customer` |
| `data.contact` | Thông tin `Contact` |
| `data.haravan` | Danh sách `Haravan Account Link` liên quan |
| `data.bitrix.enabled` | Tích hợp Bitrix có đang bật không |
| `data.bitrix.status` | Trạng thái match: `matched`, `unmatched`, `error` |
| `data.bitrix.company` | Dữ liệu công ty từ Bitrix |
| `data.bitrix.contact` | Dữ liệu contact từ Bitrix |

:::warning Bảo mật
Bitrix token/webhook URL **không bao giờ** được trả về browser. Mọi gọi Bitrix đều thực hiện server-side.
:::

## `POST /api/method/login_with_haravan.customer_profile.refresh_customer_profile`

Làm mới hồ sơ theo `HD Customer` và optional `Contact`. Gọi lại Bitrix để cập nhật dữ liệu mới nhất.

### Tham số

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|:--------:|-------|
| `hd_customer` | string | ✅ | Tên `HD Customer` |
| `contact` | string | ❌ | Tên `Contact` (nếu muốn refresh cụ thể) |
