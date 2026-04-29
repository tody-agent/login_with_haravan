---
title: User Flows
description: Biểu đồ luồng trải nghiệm người dùng
keywords: user flow, ux, login
robots: index, follow
---

# 🌊 User Flows (Luồng trải nghiệm)

:::info Tóm tắt
Mô tả trải nghiệm người dùng từ góc nhìn UI/UX.
:::

## Luồng Đăng nhập (SSO)

```mermaid
graph TD
    A[Mở trang /login] --> B[Nhấn nút 'Login with Haravan']
    B --> C{Đã đăng nhập Haravan chưa?}
    C -->|Chưa| D[Nhập Email/Pass Haravan]
    C -->|Rồi| E[Chọn Tổ chức / Cửa hàng (nếu có nhiều)]
    D --> E
    E --> F[Chuyển hướng về Helpdesk]
    F --> G{Thuộc bao nhiêu Org?}
    G -->|1 Org| H[Chuyển đến màn hình Dashboard / Tickets]
    G -->|> 1 Org| I[Hiển thị Dropdown chọn Org khi tạo Ticket]
```
