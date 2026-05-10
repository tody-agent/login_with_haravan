# Audit Custom Field HD Ticket

> Cập nhật: 2026-05-10 | Nguồn: Custom Field, Server Script, Assignment Rule production

## Phân nhóm Custom Field theo nghiệp vụ

### A. Identity / Store

| Field | Mô tả | Status |
|---|---|---|
| `custom_store_url` | URL cửa hàng (canonical input) | ✅ ACTIVE |
| `custom_orgid` | Organization ID (canonical) | ✅ ACTIVE |
| `custom_myharavan_domain` | Domain myharavan | ✅ ACTIVE |
| `custom_haravan_org_name` | Tên tổ chức | ✅ ACTIVE |
| `custom_haravan_shop_link` | _(legacy → custom_store_url)_ | ⚠️ LEGACY |
| `custom_haravan_myharavan_link` | _(legacy → custom_store_url)_ | ⚠️ LEGACY |
| `custom_my_haravan_domain` | _(legacy → custom_myharavan_domain)_ | ⚠️ LEGACY |
| `custom_haravan_profile_orgid` | _(legacy → custom_orgid)_ | ⚠️ LEGACY |

### B. Segment / Plan / Lifecycle

| Field | Mô tả | Status |
|---|---|---|
| `custom_customer_segment` | Phân khúc khách hàng (SME/Medium/Enterprise) | ✅ ACTIVE |
| `custom_current_shopplan` | Shopplan hiện tại (snapshot) | ✅ ACTIVE |
| `custom_customer_lifetime_months` | Thời gian sử dụng (tháng) | ✅ ACTIVE |
| `custom_haravan_hsi_segment` | _(legacy → custom_customer_segment)_ | ⚠️ LEGACY |

### C. Service / Intake

| Field | Mô tả | Status |
|---|---|---|
| `custom_service_line` | Dòng dịch vụ | ✅ ACTIVE |
| `custom_service_name` | Tên dịch vụ | ✅ ACTIVE |
| `custom_service_group` | Group dịch vụ (Select: Ecom/Ads/Design...) | ✅ ACTIVE |
| `custom_partner_service` | Partner service (snapshot) | ✅ ACTIVE |
| `custom_product_line` | Sản phẩm chính | ✅ ACTIVE |
| `custom_product_feature` | Tính năng sản phẩm | ✅ ACTIVE |
| `custom_product_suggestion` | Gợi ý sản phẩm (input) | ✅ ACTIVE |

### D. Workflow / Integration

| Field | Mô tả | Status |
|---|---|---|
| `custom_gitlab_issue_url` | GitLab issue URL | ✅ ACTIVE |
| `custom_bitrix_deal_id` | Bitrix Deal ID | ✅ ACTIVE |
| `custom_contact_phone` | Số điện thoại liên hệ | ✅ ACTIVE |
| `custom_haravan_routing_reason` | Lý do routing | ✅ ACTIVE |

## Quy tắc quản lý field

### ACTIVE — Không xóa
Field đang được sử dụng bởi Server Script, Assignment Rule, hoặc Report.

### LEGACY — Giữ tạm, khóa ghi mới
Field cũ đã có canonical thay thế. Migrate dữ liệu cũ → canonical, sau đó hidden.

### CANDIDATE_REMOVE — Chờ xóa
Sau khi qua gate dữ liệu (không còn script/rule/report dùng + dữ liệu rỗng/đã migrate).

## Tiêu chí an toàn để xóa field

Phải đạt **tất cả** điều kiện:
1. ❌ Không còn read/write trong Server Script
2. ❌ Không còn trong Assignment Rule / Report / Notification
3. ✅ Giá trị rỗng hoặc đã migrate 100% về canonical
4. ✅ Đã hidden tối thiểu 7 ngày không phát sinh issue

## Tham chiếu

- [Script Catalog](/operations/script-catalog) — Danh sách script production
- [Data Model](/architecture/data-model) — Entity relationships
