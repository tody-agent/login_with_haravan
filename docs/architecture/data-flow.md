---
title: Luồng dữ liệu & Đồng bộ
description: Luồng luân chuyển dữ liệu từ OAuth claims đến Frappe Helpdesk database.
keywords: luồng dữ liệu, data flow, đồng bộ, sync
robots: index, follow
---

# 🔄 Luồng dữ liệu & Đồng bộ

:::info Tóm tắt
Tài liệu mô tả cách dữ liệu luân chuyển từ khi callback OAuth nhận response, qua quá trình chuẩn hóa, đến khi được lưu vào Frappe Helpdesk.
:::

## 1. Tổng quan luồng dữ liệu

```mermaid
sequenceDiagram
    participant Haravan as Haravan Accounts
    participant Engine as Engines Layer
    participant DB as Frappe Database

    Haravan-->>Engine: JSON Data (orgid, email, userid, orgname, ...)
    Engine->>Engine: normalize_haravan_profile()
    Engine->>DB: Upsert HD Customer
    Engine->>DB: Upsert Contact
    Engine->>DB: Upsert Haravan Account Link

    Note over Engine,DB: Dữ liệu hồ sơ chi tiết được lấy<br/>từ Bitrix khi agent mở Customer Profile
```

## 2. Logic đồng bộ khách hàng

Logic chính nằm ở `login_with_haravan/engines/sync_helpdesk.py`:

### 2.1. Tìm kiếm HD Customer

| Thứ tự | Phương thức | Mô tả |
|--------|-------------|-------|
| 1 | Tìm theo `custom_haravan_orgid` | Ưu tiên cao nhất — định danh duy nhất tổ chức |
| 2 | Tìm theo tên `[OrgID] - [OrgName]` | Dự phòng nếu custom field chưa được migrate |

### 2.2. Tạo/Cập nhật dữ liệu

Chỉ cập nhật dữ liệu định danh tối thiểu:

| Trường | Nguồn | Mô tả |
|--------|-------|-------|
| `customer_name` | OAuth claim | Tên hiển thị: `[OrgID] - [OrgName]` |
| `domain` | OAuth claim | Tên miền phụ (subdomain) |
| `custom_haravan_orgid` | OAuth claim | ID tổ chức — khóa định danh duy nhất |
| `custom_myharavan` | OAuth claim | Subdomain `.myharavan.com` |

### 2.3. Hồ sơ khách hàng chi tiết

Dữ liệu hồ sơ chi tiết (Bitrix) **không** được lấy trong callback đăng nhập. Thay vào đó, agent Helpdesk kích hoạt việc lấy dữ liệu khi mở hoặc refresh panel Customer Profile.

Xem API chi tiết: [Hồ sơ khách hàng](/api/customer-profile).

## 3. Phân quyền Contact theo vai trò

Hệ thống phân quyền dựa trên vai trò của người dùng trong tổ chức Haravan:

```mermaid
graph TD
    A[Người dùng đăng nhập] --> B{Vai trò trong tổ chức?}
    B -->|Owner / Admin| C[Tạo Contact + Liên kết với HD Customer]
    B -->|Staff| D[Tạo Contact — KHÔNG liên kết]
    C --> E[Xem toàn bộ ticket của tổ chức]
    D --> F[Chỉ xem ticket do chính họ tạo]
```

| Vai trò | Tạo Contact | Liên kết HD Customer | Phạm vi xem ticket |
|---------|:-----------:|:-------------------:|:------------------:|
| **Owner / Admin** | ✅ | ✅ | Toàn bộ ticket tổ chức |
| **Staff** | ✅ | ❌ | Chỉ ticket của bản thân |
