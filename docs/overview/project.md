# Tổng quan dự án

## Haravan Helpdesk là gì?

**Haravan Helpdesk** là hệ thống hỗ trợ khách hàng được xây dựng trên nền tảng [Frappe Helpdesk](https://frappedesk.com), mở rộng bởi custom app `login_with_haravan` để tích hợp đăng nhập qua Haravan và làm giàu dữ liệu khách hàng.

**URL production:** [https://haravan.help](https://haravan.help)

## Mục tiêu dự án

1. **Đăng nhập Haravan SSO** — Merchant Haravan đăng nhập portal bằng tài khoản Haravan (OAuth 2.0)
2. **Tự động nhận diện khách hàng** — Từ URL cửa hàng hoặc orgid, hệ thống tự lookup và link khách hàng
3. **Làm giàu dữ liệu** — Đồng bộ thông tin từ Bitrix CRM (segment, shopplan, partner, lifetime)
4. **Định tuyến thông minh** — Ticket được route đến đúng team dựa trên segment, partner, shopplan
5. **Bàn giao cho Haravan** — Tài liệu, cấu hình, SOP đầy đủ để team Haravan tự vận hành

## Kiến trúc tổng quan

```
┌──────────────────────────────────────────────────┐
│              haravan.help (Production)            │
│                                                  │
│  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Frappe       │  │ login_with_haravan        │  │
│  │ Helpdesk     │  │ (Custom App)              │  │
│  │              │  │  • OAuth SSO              │  │
│  │  • Tickets   │  │  • Customer Enrichment    │  │
│  │  • Portal    │  │  • Routing Engine         │  │
│  │  • KB        │  │  • Bitrix Integration     │  │
│  └──────┬───────┘  └──────────┬───────────────┘  │
│         │                     │                   │
│         └─────────┬───────────┘                   │
│                   │                               │
│         ┌─────────▼─────────┐                     │
│         │  Frappe Framework  │                     │
│         │  (v15)             │                     │
│         └───────────────────┘                     │
│                                                   │
│  Hosting: Frappe Cloud                            │
│  Site: haravandesk.s.frappe.cloud                 │
└──────────────────────────────────────────────────┘
```

## Các hệ thống tích hợp

| Hệ thống | Vai trò | Phương thức |
|---|---|---|
| **Haravan OAuth** | Đăng nhập SSO cho merchant | OAuth 2.0 Authorization Code |
| **Bitrix24 CRM** | Làm giàu dữ liệu khách hàng | REST API webhook |
| **GitLab** | Tạo issue từ ticket | Server Script API |
| **Make.com** | Workflow automation (onboarding) | Webhook + API |
| **meta.json** | Resolve orgid từ domain cửa hàng | HTTP GET |

## Personas

### 🧑‍💻 Technical Admin (Developer)
- Tiếp nhận và bảo trì codebase `login_with_haravan`
- Quản lý Server Script, Assignment Rule trên Frappe Cloud
- Debug và fix lỗi enrichment/routing

### 🏪 Merchant (End-user)
- Đăng nhập portal bằng tài khoản Haravan
- Tạo, theo dõi, đánh giá ticket hỗ trợ
- Truy cập Knowledge Base (KB)

### 👨‍💼 CS Manager / Admin
- Cấu hình phân quyền, template, team routing
- Quản lý agent, RBAC, SLA
- Review report và metrics

### 🎧 Agent (Support Staff)
- Xử lý ticket, sử dụng customer profile
- Chuyển ticket, tạo GitLab issue
- Sử dụng AI features

## Tài liệu liên quan

- [Bắt đầu cài đặt](/getting-started/installation) — Hướng dẫn cài đặt
- [Kiến trúc hệ thống](/architecture/overview) — Chi tiết kiến trúc
- [Bàn giao vận hành](/handover/handoff-sop) — SOP bàn giao
