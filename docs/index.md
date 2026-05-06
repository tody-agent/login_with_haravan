---
title: Trang chủ
description: Bản đồ bàn giao Haravan Helpdesk cho Frappe Helpdesk dành cho Haravan Developers và đội vận hành.
keywords: haravan, frappe, helpdesk, oauth, đăng nhập, tài liệu
robots: index, follow
---

# Haravan Helpdesk — Bản đồ bàn giao

Ứng dụng **Haravan Helpdesk** là custom app Frappe đang chạy cho Haravan Helpdesk tại `https://haravan.help`. App phụ trách đăng nhập OAuth bằng Haravan Account, tạo/match `User`, liên kết Haravan org với `HD Customer`, và hỗ trợ agent đọc hồ sơ khách hàng từ Bitrix khi xử lý ticket.

:::tip Trạng thái hiện tại
Luồng OAuth là **login-only**. Callback đăng nhập chỉ lưu dữ liệu định danh tối thiểu (`userid`, `email`, `orgid`). Dữ liệu vận hành chi tiết như HSI, Shopplan, responsible, segment và Customer Profit/Profile được lấy server-side từ Bitrix theo nhu cầu agent, không gọi Haravan commerce API trong callback.
:::

## Đọc theo vai trò

| Vai trò | Nên đọc trước | Mục tiêu |
|---|---|---|
| Developer tiếp quản app | [Hiện trạng & lộ trình](/about/handoff-roadmap) → [Kiến trúc hệ thống](/architecture/overview) → [Triển khai production](/guide/deployment) | Nắm ranh giới code, cách deploy và hướng mở rộng an toàn |
| Admin vận hành Haravan Helpdesk | [Bắt đầu & cấu hình OAuth](/guide/getting-started) → [Khắc phục sự cố](/guide/troubleshooting) → [Sổ đăng ký Script](/operations/script-registry) | Quản lý config, script production và xử lý lỗi thường gặp |
| Team CS/Support Haravan | [User, email & multi-org](/guide/haravan-user-account-cases) → [Cấp quyền Portal/Desk](/guide/haravan-employee-helpdesk-access) → [HD Ticket Product Suggestion](/guide/hd-ticket-product-suggestion) | Hiểu user được tạo thế nào, cấp quyền đúng và cập nhật luật nghiệp vụ |
| Agent dùng Customer Profile | [Data model haravan.help](/haravan-helpdesk-data-model) → [Customer Profile API](/api/customer-profile) → [Metajson, Bitrix & Customer Profit](/operations/metajson-bitrix-customer-profit-flow) | Hiểu dữ liệu ticket/customer, Bitrix enrichment và popup agent |

## Luồng đọc khuyến nghị

### 1. Bàn giao nhanh

1. [Hiện trạng & lộ trình](/about/handoff-roadmap)
2. [Bắt đầu & cấu hình OAuth](/guide/getting-started)
3. [Triển khai production](/guide/deployment)
4. [Khắc phục sự cố](/guide/troubleshooting)

### 2. Login và phân quyền

1. [User, email & multi-org](/guide/haravan-user-account-cases)
2. [Cấp quyền Portal/Desk](/guide/haravan-employee-helpdesk-access)
3. [Luồng OAuth & đăng nhập](/architecture/oauth-flow)
4. [OAuth Callback API](/api/oauth-callback)
5. [Danh tính & tổ chức API](/api/identity-sync)

### 3. Dữ liệu Helpdesk, Bitrix và agent workflow

1. [Data model haravan.help](/haravan-helpdesk-data-model)
2. [Customer Profile API](/api/customer-profile)
3. [Metajson, Bitrix & Customer Profit](/operations/metajson-bitrix-customer-profit-flow)
4. [HD Ticket Product Suggestion](/guide/hd-ticket-product-suggestion)
5. [Sổ đăng ký Script](/operations/script-registry)
6. [Ghi đè giao diện tiếng Việt](/operations/vietnamese-ui-override)

### 4. Kiến trúc và tham chiếu

1. [Tổng quan kiến trúc](/architecture/overview)
2. [Luồng dữ liệu & đồng bộ](/architecture/data-flow)
3. [Cơ sở dữ liệu](/architecture/database)
4. [Bitrix integration reference](/bitrix_integration)
5. [Bitrix field mapping](/bitrix_mapping)
6. [Bitrix MCP setup](/bitrix_mcp_setup)

## Giá trị cấu hình quan trọng

| Hạng mục | Giá trị hiện tại |
|---|---|
| Public domain | `https://haravan.help` |
| Frappe Cloud site | `haravandesk.s.frappe.cloud` |
| OAuth callback path | `/api/method/login_with_haravan.oauth.login_via_haravan` |
| Public callback URL | `https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan` |
| Site Config key chính | `haravan_account_login` |
| Provider DocType name | `haravan_account` |
| Provider display name | `Login With Haravan` |

## Quy tắc bảo trì

- Không sửa Frappe core hoặc Helpdesk core; mọi tùy biến nằm trong app `login_with_haravan`, Custom Fields, Server Script hoặc HD Form Script.
- Giữ `Social Login Key.redirect_url` dạng path tương đối để Frappe tự dùng domain request hiện tại. Chỉ đặt `haravan_account_login.redirect_uri` khi thật sự cần ép domain.
- Không đưa Bitrix webhook, Haravan client secret, GitLab token hoặc API key ra browser hay tài liệu public.
- Trước khi ship code, chạy test local theo [Triển khai production](/guide/deployment) hoặc `./test_gate.sh` nếu có.
