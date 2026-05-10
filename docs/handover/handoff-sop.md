# Tài liệu bàn giao vận hành

> Tài liệu này là SOP (Standard Operating Procedure) chính để bàn giao Haravan Helpdesk cho team Haravan.

## 1. Thông tin hệ thống

| Mục | Giá trị |
|---|---|
| **Production URL** | [https://haravan.help](https://haravan.help) |
| **Frappe Cloud site** | `haravandesk.s.frappe.cloud` |
| **App custom** | `login_with_haravan` |
| **GitHub repo** | `https://github.com/tody-agent/login_with_haravan` |
| **Frappe version** | v15 |
| **Helpdesk version** | Latest (Frappe Helpdesk) |

## 2. Tài khoản & quyền truy cập

### Frappe Cloud Dashboard
- URL: [frappecloud.com/dashboard](https://frappecloud.com/dashboard)
- Cần: tài khoản Frappe Cloud owner hoặc admin
- Quyền: quản lý site, apps, config, billing

### Haravan Partner Dashboard
- URL: [partners.haravan.com](https://partners.haravan.com)
- Cần: tài khoản partner có quyền quản lý App
- Để quản lý: OAuth Client ID/Secret, callback URL

### Bitrix24
- URL: _(\[domain\].bitrix24.vn)_
- Cần: tài khoản admin có quyền tạo/quản lý incoming webhook
- Webhook URL lưu trong Site Config key `bitrix_webhook_url`

## 3. Checklist bàn giao

### Hạ tầng & truy cập
- [ ] Transfer Frappe Cloud site ownership
- [ ] Transfer GitHub repo ownership
- [ ] Chuyển giao Haravan Partner App credentials
- [ ] Xác nhận Bitrix webhook hoạt động
- [ ] Xác nhận GitLab access token (nếu dùng)

### Cấu hình
- [ ] Review Site Config keys — xem [Site Config](/getting-started/site-config)
- [ ] Xác nhận OAuth flow hoạt động — test đăng nhập
- [ ] Review Assignment Rules — xem [RBAC](/access-control/rbac)
- [ ] Review Server Scripts — xem [Script Catalog](/operations/script-catalog)

### Tài liệu
- [ ] Team đã đọc [Tổng quan dự án](/overview/project)
- [ ] Team đã hiểu [Luồng Enrichment Routing](/integrations/bitrix-routing)
- [ ] Team đã biết [safe_exec gotchas](/architecture/safe-exec)
- [ ] Team đã test trên site staging (nếu có)

## 4. Vận hành hàng ngày

### Ticket flow chuẩn

1. Khách đăng nhập → tạo ticket → hệ thống enrichment tự động
2. Routing script set `agent_group` → Assignment Rule phân công agent
3. Agent xử lý → reply → resolve → close
4. Khách feedback / reopen nếu cần

### Kiểm tra sức khỏe hệ thống

| Kiểm tra | Tần suất | Cách làm |
|---|---|---|
| Error Log | Hàng ngày | Setup > Error Log, lọc `Server Script` |
| Assignment hoạt động | Hàng ngày | Tạo ticket test, check ToDo |
| OAuth flow | Hàng tuần | Đăng nhập incognito |
| Bitrix sync | Hàng tuần | Tạo ticket có store_url, check enrichment |

### Xử lý sự cố thường gặp

| Sự cố | Nguyên nhân | Fix |
|---|---|---|
| Ticket không enrich | `meta.json` fail hoặc Bitrix timeout | Check Error Log → manual re-save ticket |
| Agent không thấy ticket | User Permission sai | Check Setup > User Permission |
| OAuth lỗi | Callback URL mismatch | Check Haravan Partner Dashboard |
| Assignment sai team | `agent_group` rỗng/sai | Check Server Script Routing, Assignment Rule |

## 5. Thay đổi & bảo trì

### Thêm agent mới
→ Xem [RBAC & Phân quyền](/access-control/rbac)

### Thêm/sửa Server Script
→ Xem [Script Catalog](/operations/script-catalog) + [safe_exec](/architecture/safe-exec)

### Thay đổi routing/assignment
→ Xem [Enrichment Routing](/integrations/bitrix-routing)

### Cập nhật Site Config
→ Xem [Site Config](/getting-started/site-config)

## 6. Rollback plan

Nếu có sự cố sau thay đổi:

1. **Server Script**: restore từ backup JSON (export trước khi sửa)
2. **Assignment Rule**: disable rule mới, enable rule cũ
3. **Custom Field**: restore từ fixture backup
4. **App code**: revert commit trên GitHub, redeploy
5. **Site Config**: sửa lại value cũ qua Frappe Cloud Dashboard

::: warning Luôn backup trước khi thay đổi
- Export Server Script bằng `frappe.get_doc("Server Script", name).as_json()`
- Export Assignment Rule tương tự
- Lưu backup local trước khi deploy
:::

## Tham chiếu

- [UAT Checklist](/handover/uat-checklist) — Checklist kiểm thử
- [Checklist bàn giao](/handover/uat-ban-giao) — Bàn giao chi tiết
- [Scripts Review](/handover/scripts-review) — Review checklist scripts
