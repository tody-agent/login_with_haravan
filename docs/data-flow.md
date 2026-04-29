---
title: Luồng Dữ liệu (Data Flow)
description: Luồng dữ liệu đăng nhập và đồng bộ Haravan sang Frappe Helpdesk
keywords: data flow, oauth flow, sync
robots: index, follow
---

# 🔄 Luồng Dữ liệu (Data Flow)

:::info Tóm tắt
Tài liệu mô tả luồng luân chuyển dữ liệu từ khi người dùng bấm đăng nhập cho đến khi dữ liệu được đồng bộ vào Frappe Helpdesk.
:::

## 1. Luồng OAuth 2.0 & Đồng bộ

```mermaid
sequenceDiagram
    participant User as Người dùng
    participant Frappe as Frappe Helpdesk
    participant Haravan as Haravan Accounts
    participant DB as Frappe Database

    User->>Frappe: Click "Login with Haravan"
    Frappe->>Haravan: Redirect (client_id, state, redirect_uri)
    Haravan-->>User: Trang đăng nhập & Chọn Tổ chức
    User->>Haravan: Cấp quyền
    Haravan->>Frappe: Callback /oauth.login_via_haravan (code, state)
    Frappe->>Haravan: Đổi code lấy Access Token
    Haravan-->>Frappe: Access Token + ID Token
    Frappe->>Haravan: Fetch User & Org Info
    Haravan-->>Frappe: JSON Data (orgid, email, etc.)
    Frappe->>DB: Upsert HD Customer & Contact
    Frappe->>DB: Upsert Haravan Account Link
    Frappe-->>User: Đăng nhập thành công, tạo phiên (Session)
```

## 2. Đồng bộ Khách hàng (Sync Logic)
Logic chính nằm ở `login_with_haravan/engines/sync_helpdesk.py`:
1. **Tìm kiếm HD Customer:** Ưu tiên tìm theo `custom_haravan_orgid`. Nếu không có, tìm theo tên `[OrgID] - [OrgName]`.
2. **Tạo/Cập nhật:** Cập nhật các trường `domain`, `custom_shopplan_name`.
3. **First Paid Date (Fallback logic):** Trường `custom_first_paid_date` được ưu tiên lấy từ `subscription_created_at` (API Gói dịch vụ). Nếu trống, hệ thống sẽ sử dụng `shop.created_at` làm giá trị thay thế (chỉ điền 1 lần khi tạo mới).
4. **Phân quyền Contact (Role-based Linking):**
   - **Owner / Admin:** Được tự động tạo `Contact` và liên kết (link) với `HD Customer`. Nhờ đó, họ có thể **xem toàn bộ ticket** của tổ chức.
   - **Staff:** Tạo `Contact` nhưng **KHÔNG** liên kết với `HD Customer`. Nhân viên chỉ có thể **xem các ticket do chính họ tạo ra**.
