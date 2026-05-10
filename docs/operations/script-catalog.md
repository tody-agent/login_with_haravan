# Sổ đăng ký Script (Canonical)

> Cập nhật: 2026-05-10 | Source of truth: Production scripts trên `haravan.help` (Frappe Cloud)

## Quy ước đặt tên

### Format production

```
<Type> - <Group> - <Purpose>
```

**Ví dụ:**
- `Server Script - Enrichment - Auto Customer Sync From OrgID`
- `HD Form Script - Profile - Ticket Customer Button`
- `Client Script - Intake - Agent Ticket Dialog`

### Format debug

```
Debug - {group} - {name}
```

**Ví dụ:**
- `Debug - API - Frappe Endpoint Smoke`
- `Debug - Enrichment - Ticket Domain Filter Replay`

## Từ điển trạng thái

| Trạng thái | Ý nghĩa |
|---|---|
| `Active` | Đang sử dụng trong production |
| `Debug` | Chỉ dùng cho test/diagnostic |
| `Not use` | Không còn sử dụng, giữ lại để tham chiếu |
| `Legacy` | Hành vi cũ, giữ cho migration/audit |

## Phân loại theo nhóm (Taxonomy)

| Group | Mô tả |
|---|---|
| `Intake` | API/dialog tạo ticket |
| `Validation` | Kiểm tra và normalize trước khi save |
| `Enrichment` | Tra cứu org/domain, meta.json, Bitrix sync |
| `Routing` | Normalize route fields và `agent_group` |
| `Assignment` | Phân công ownership cho agent |
| `Profile` | Customer profile và actions |
| `Integration` | GitLab, Make, hệ thống bên ngoài |
| `Debug` | Test và troubleshooting |

## Danh sách Script đầy đủ

### Server Script / API

| Tên hiện tại | Tên Canonical | Group | Status |
|---|---|---|---|
| `Onboarding - Create Ticket API` | Server Script - Intake - Create Onboarding Ticket API | Intake | ✅ Active |
| `Onboarding - Agent Ticket API` | Server Script - Intake - Create Agent Ticket API | Intake | ✅ Active |
| `Ticket - Contact Phone Validate` | Server Script - Validation - Contact Phone Normalize | Validation | ✅ Active |
| `Ticket - Normalize Intake Selects` | Server Script - Validation - Intake Select Normalize | Validation | ✅ Active |
| `Ticket - Product Suggestion Map` | Server Script - Validation - Product Suggestion Map | Validation | ✅ Active |
| `Ticket - Auto Customer Sync From OrgID` | Server Script - Enrichment - Auto Customer Sync From OrgID | Enrichment | ✅ Active |
| `Ticket - Find OrgID From URL API` | Server Script - Enrichment - Find OrgID From URL API | Enrichment | ✅ Active |
| `Metajson - Bitrix Company Enrichment API` | Server Script - Enrichment - Bitrix Company Enrichment API | Enrichment | ✅ Active |
| `Profile - Bitrix Sync Ticket Customer` | Server Script - Profile - Bitrix Sync Ticket Customer | Profile | ✅ Active |
| `Profile - Bitrix Customer API` | Server Script - Profile - Bitrix Customer Profile API | Profile | ✅ Active |
| `Ticket - Snapshot Enrichment Fields` | Server Script - Routing - Snapshot Enrichment Fields | Routing | ✅ Active |
| `Ticket - Normalize Enrichment Routing After Save` | Server Script - Routing - Normalize Enrichment Routing | Routing | ✅ Active |
| `GitLab - Ticket Issue API` | Server Script - Integration - GitLab Ticket Issue API | Integration | ✅ Active |

### Server Script — Disabled

| Tên | Canonical | Group | Status | Lý do |
|---|---|---|---|---|
| `Ticket - Auto Customer Sync Kickoff After Insert` | Enrichment - Auto Customer Sync Kickoff | Enrichment | ⛔ Not use | Superseded by after-save path |
| `Ticket - Require Customer Or Store URL` | Validation - Require Customer Or Store URL | Validation | ⛔ Not use | Blocking validator disabled |
| `Ticket - Store URL Enrich` | Enrichment - Store URL Enrich | Enrichment | ⛔ Not use | Legacy pre-validate flow |
| `Profile - Ticket Routing` | Routing - Ticket Routing | Routing | ⛔ Not use | Legacy routing |
| `Profile - Ticket Round Robin Assignment` | Assignment - Ticket Round Robin Assignment | Assignment | ⛔ Not use | Legacy assignment |

### Client Script

| Tên | Group | Status | Chức năng |
|---|---|---|---|
| `Onboarding - Agent Ticket Dialog` | Intake | ✅ Active | Dialog tạo ticket cho agent |

### HD Form Script

| Tên | Group | Status | Chức năng |
|---|---|---|---|
| `Profile - Ticket Customer Button` | Profile | ✅ Active | Nút customer profile trên ticket |
| `GitLab - Ticket Issue Button` | Integration | ✅ Active | Nút tạo GitLab issue từ ticket |

## Quy trình thay đổi Script

Trước khi thêm hoặc sửa script:

1. ✅ Tên đúng format canonical theo loại script
2. ✅ Group thuộc taxonomy ở trên
3. ✅ Status được set rõ ràng
4. ✅ Mô tả ngắn 1 dòng
5. ✅ Nếu debug: tên bắt đầu bằng `Debug -`
6. ✅ Nếu tắt: chuyển sang `Not use` (không xóa khỏi catalog)
7. ✅ Cập nhật docs liên quan

## Tham chiếu

- [Data Model](/architecture/data-model) — Entities và field contracts
- [Bitrix Enrichment Routing](/integrations/bitrix-routing) — Luồng enrichment chi tiết
- [Custom Fields Audit](/operations/custom-fields) — Kiểm tra field
