---
title: Trang chủ
description: Tài liệu tích hợp đăng nhập Haravan cho Frappe Helpdesk
keywords: haravan, frappe, helpdesk, oauth, login
robots: index, follow
---

# 🚀 Login With Haravan (Frappe Integration)

:::info Đối tượng & Mục tiêu
Tài liệu này là **Developer Handoff Manual** dành cho đội ngũ Kỹ sư phần mềm (đặc biệt là Haravan Developers). Mục tiêu là giúp các nhà phát triển nắm vững kiến trúc, cách vận hành và định hướng mở rộng (improvement) ứng dụng Frappe tích hợp với Haravan.
:::

## 🌟 Vai trò của ứng dụng
- **Đăng nhập OAuth 2.0:** Xác thực an toàn qua hệ thống `accounts.haravan.com`.
- **Đồng bộ Profile:** Lấy thông tin tổ chức và tạo `HD Customer` trong Frappe Helpdesk.
- **Sẵn sàng để mở rộng:** Cấu trúc 7-Layer chuẩn của Frappe, dễ dàng thêm tính năng mới (như lấy thông tin Orders, Webhooks) mà không phá vỡ core của Frappe.

## 📚 Hướng dẫn dành cho Developer
- **[Kế hoạch & Bàn giao (Roadmap)](/frappe-helpdesk-plan):** Đọc file này đầu tiên để biết cách tiếp quản source code và các ý tưởng phát triển tiếp theo.
- **[Kiến trúc Hệ thống](/architecture):** Hiểu cách code được cấu trúc trong thư mục `login_with_haravan`.
- **[SOP & Cài đặt](/sop/installation):** Cách cài ứng dụng vào môi trường local (bench) để lập trình.
- **[Luồng dữ liệu](/data-flow):** Cách JWT token được giải mã và dữ liệu chuyển vào database.

[Bắt đầu với Kế hoạch Bàn giao & Phát triển](/frappe-helpdesk-plan)
