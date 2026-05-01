---
title: API — Danh tính & Tổ chức
description: API lấy danh sách tổ chức của người dùng hiện tại, dùng cho Portal Frontend
keywords: api, danh tính, identity, tổ chức, org
robots: index, follow
---

# 🪪 API: Danh tính & Tổ chức

:::info Tóm tắt
API hỗ trợ lấy danh sách tổ chức (org) của người dùng hiện tại — phục vụ Portal Frontend hiển thị Dropdown chọn tổ chức khi tạo ticket.
:::

## `GET /api/method/login_with_haravan.oauth.get_user_haravan_orgs`

Trả về danh sách các `HD Customer` được liên kết với người dùng đang đăng nhập, thông qua `Haravan Account Link`.

### Yêu cầu

- Người dùng phải đã đăng nhập (session hợp lệ).
- Không cần tham số.

### Phản hồi

```json
[
  {
    "orgid": "12345",
    "orgname": "Minh Hải Store",
    "customer": "12345 - Minh Hải Store"
  }
]
```

| Trường | Mô tả |
|--------|-------|
| `orgid` | ID tổ chức trên Haravan |
| `orgname` | Tên tổ chức |
| `customer` | Tên `HD Customer` tương ứng trên Helpdesk |

### Trường hợp sử dụng

Dùng trong Frappe Client Script trên màn hình Web Form tạo Ticket:

- Nếu người dùng thuộc **1 tổ chức** → tự động điền tổ chức.
- Nếu người dùng thuộc **nhiều tổ chức** → hiển thị Dropdown để chọn.

Xem thêm luồng UX tại [Luồng OAuth & Đăng nhập](/architecture/oauth-flow#_2-luong-trai-nghiem-nguoi-dung-ux).
