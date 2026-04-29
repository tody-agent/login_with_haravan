---
title: API - Identity Sync
description: API đồng bộ danh tính tổ chức
keywords: api, identity, sync, org
robots: index, follow
---

# 🪪 API: Identity Sync

:::info Tóm tắt
API hỗ trợ lấy danh sách tổ chức (org) của người dùng hiện tại, dùng cho Portal Frontend.
:::

## `GET /api/method/login_with_haravan.oauth.get_user_haravan_orgs`

Trả về danh sách các `HD Customer` được liên kết với người dùng đang đăng nhập thông qua `Haravan Account Link`.

### Response Payload

```json
[
  {
    "orgid": "12345",
    "orgname": "Minh Hải Store",
    "customer": "12345 - Minh Hải Store"
  }
]
```

### Sử dụng
Dùng trong Frappe Client Script trên màn hình Web Form tạo Ticket để hiển thị Dropdown cho người dùng thuộc nhiều Org.
