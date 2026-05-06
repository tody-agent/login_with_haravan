---
title: Sổ đăng ký Script Helpdesk
description: Quy ước đặt tên và bản đồ chức năng các script đang quản lý trên Haravan Helpdesk
keywords: frappe, helpdesk, script, registry, haravan, quản lý
robots: noindex, follow
---

# 📋 Sổ đăng ký Script Helpdesk

:::info Mục tiêu
Tài liệu này là bản đồ đặt tên và phân nhóm các script đang quản lý trực tiếp trên Haravan Helpdesk (`https://haravan.help`). Nhìn vào tên script có thể biết ngay script thuộc module nào, flow nào, và làm việc gì.
:::

## Quy ước đặt tên

Sử dụng mẫu tên ngắn gọn:

```text
<Module> - <Flow/Context> <Action>
```

Ví dụ:

```text
Auth - Login Customer Enrich
AI - Ticket Analyze API
Ticket - Intake Field Rules
```

### Quy tắc

- **Module:** Dùng một trong các nhóm chính: `Auth`, `Profile`, `AI`, `GitLab`, `Ticket`, `Media`, `Email`, `Onboarding`.
- **Action:** Dùng động từ ngắn: `Enrich`, `Analyze`, `Map`, `Validate`, `Filter`, `Public`, `Button`, `API`, `Event`.
- Server Script dạng API được phép đổi tên record, nhưng `api_method` phải giữ nguyên nếu UI/logic cũ còn gọi endpoint đó.
- Script đang bị nghi ngờ hoặc chưa cần dùng thì **disabled**, không xoá ngay nếu chưa có backup/quyết định rõ ràng.
- Logic mapping/validation quan trọng nên ưu tiên đưa về server-side/source-controlled thay vì rải trong Client Script hoặc HD Form Script.

## Phân quyền Module

| Module | Phạm vi | Trạng thái |
|--------|---------|------------|
| `Auth` | Đăng nhập Haravan, liên kết account, làm giàu `HD Customer` khi login/register | Giữ — đang bật |
| `Profile` | Customer Profile cho agent, Bitrix backup/passive lookup | Giữ — cần tiếp tục phát triển |
| `AI` | Các API và action AI: phân tích, tóm tắt, gợi ý trả lời, gửi reply | Giữ — cần gom UI thành một menu AI |
| `GitLab` | Tạo/xem issue GitLab từ ticket | Giữ |
| `Ticket` | Field dependency, validate, mapping dữ liệu ticket | Giữ phần cơ bản; refactor dần về server-side |
| `Media` | Attachment và inline media để khách xem được file/ảnh | Giữ |
| `Email` | Email automation, subject/SLA, phân công song ngữ | Giữ |
| `Onboarding` | Tạo ticket onboarding/agent-created customer ticket | Giữ nếu còn cần flow tạo ticket từ agent/API |

## Danh sách Script hiện tại

### HD Form Script

Tất cả HD Form Script hiện đang **enabled**. Đây là các script UI trong Helpdesk portal/desk form.

| Script | Flow | Mục đích |
|--------|------|----------|
| `AI - Ticket Assist Menu` | AI / Ticket | Menu/action AI tổng hợp cho agent |
| `AI - Ticket Analyze Action` | AI / Ticket | Nút/action phân tích ticket |
| `GitLab - Ticket Issue Button` | GitLab / Ticket | Popup đầy đủ: tạo issue, tìm/link issue, xem liên kết hiện tại, sync, gỡ mapping |
| `Profile - Ticket Customer Button` | Profile / Ticket | Menu Customer Profile / Refresh Bitrix Profile, gọi `haravan_bitrix_customer_profile` |
| `Ticket - Intake Field Rules` | Ticket / Intake | Required/visible/validate cơ bản khi tạo ticket |
| `Ticket - Onboarding Phase Filter` | Ticket / Field dependency | Lọc phase onboarding theo loại/service |
| `Ticket - Service Line Filter` | Ticket / Field dependency | Lọc service line |
| `Ticket - Service Name Filter` | Ticket / Field dependency | Lọc service name |
| `Ticket - Service Vendor Filter` | Ticket / Field dependency | Lọc service vendor |

### Client Script

| Script | Doctype/View | Trạng thái | Mục đích |
|--------|-------------|:----------:|----------|
| `Onboarding - Agent Ticket Dialog` | `HD Ticket` / Form | ✅ | Dialog để agent tạo ticket cho khách |

### Server Script

| Script | Loại | Event/API | Trạng thái | Mục đích |
|--------|------|-----------|:----------:|----------|
| `Auth - Login Customer Enrich` | DocType Event | `Haravan Account Link / After Save` | ✅ | Làm giàu `HD Customer` chủ động sau login/register |
| `Auth - Inside Customer Enrich` | DocType Event | `HD Ticket / Before Save` | ✅ | Làm giàu ticket/customer từ Inside/nguồn nội bộ |
| `Profile - Bitrix Customer API` | API | `haravan_bitrix_customer_profile` | ✅ | Lấy Customer Profile từ Bitrix theo nhu cầu agent, đọc webhook từ `Helpdesk Integrations Settings` và normalize HSI/Shopplan |
| `Metajson - Bitrix Company Enrichment API` | API | `haravan_bitrix_metajson_company_enrichment` | ✅ | Làm giàu `HD Customer` và link `HD Ticket` từ metajson/orgid bằng Bitrix company data |
| `Profile - Ticket Routing` | DocType Event | `HD Ticket / Before Save` | ✅ | Routing ticket theo profile/segment khách hàng |
| `Onboarding - Agent Ticket API` | API | `haravan_agent_create_customer_ticket` | ✅ | Backend cho dialog agent tạo ticket cho khách |
| `Onboarding - Create Ticket API` | API | `haravan_helpdesk.api.create_onboarding_ticket` | ✅ | Tạo onboarding ticket từ API |
| `GitLab - Ticket Issue API` | API | `haravan_helpdesk.api.gitlab_popup_v2` | ✅ | Backend API cho popup GitLab |
| `AI - Summary API` | API | `generate-ai-summary` | ✅ | Tạo tóm tắt ticket |
| `AI - Reply Suggest API` | API | `generate-ai-reply` | ✅ | Gợi ý nội dung reply |
| `AI - Send Reply API` | API | `send-ai-reply` | ✅ | Gửi reply từ kết quả AI |
| `AI - Ticket Analyze API` | API | `haravan_ai_analyze_ticket` | ✅ | Phân tích/phân loại ticket bằng AI |
| `AI - Ticket Copilot Event` | DocType Event | `HD Ticket / After Insert` | ✅ | Tự động tạo gợi ý routing/next step sau khi tạo ticket |
| `Ticket - Store URL Enrich` | DocType Event | `HD Ticket / Before Validate` | ✅ | Chuẩn hóa store URL, đọc `meta.json`, map OrgID/MyHaravan |
| `Ticket - Product Suggestion Map` | DocType Event | `HD Ticket / Before Validate` | ✅ | Map product suggestion sang product line/feature |
| `Ticket - Contact Phone Validate` | DocType Event | `HD Ticket / Before Validate` | ✅ | Validate số điện thoại liên hệ |
| `Media - Ticket Attachment Public` | DocType Event | `File / After Save` | ✅ | Đảm bảo attachment ticket public khi cần |
| `Media - Ticket Inline Public` | DocType Event | `Communication / After Save` | ✅ | Đảm bảo inline media trong trao đổi ticket public khi cần |
| `Email - Assignment Bilingual` | DocType Event | `Notification Log / Before Insert` | ✅ | Email phân công song ngữ |
| `Email - Ack Subject SLA` | DocType Event | `Email Queue / Before Insert` | ✅ | Chuẩn hóa subject/nội dung email acknowledgement/SLA |

## Lịch sử đổi tên

### HD Form Script

| Tên cũ | Tên mới |
|--------|---------|
| `AI Reply Summary Actions` | `AI - Ticket Assist Menu` |
| `HD Ticket - AI Analyze Actions` | `AI - Ticket Analyze Action` |
| `HD Ticket - GitLab Popup V3` | `GitLab - Ticket Issue Button` |
| `Custom Button - Customer Profile` | `Profile - Ticket Customer Button` |
| `HD Ticket Intake Dependencies` | `Ticket - Intake Field Rules` |
| `Field Dependency-custom_internal_type-custom_service_line` | `Ticket - Service Line Filter` |
| `Field Dependency-custom_internal_type-custom_service_name` | `Ticket - Service Name Filter` |
| `Field Dependency-custom_internal_type-custom_service_onboarding_phrase` | `Ticket - Onboarding Phase Filter` |
| `Field Dependency-custom_internal_type-custom_service_vendor` | `Ticket - Service Vendor Filter` |

### Client Script

| Tên cũ | Tên mới |
|--------|---------|
| `HD Ticket - Agent Create Customer Ticket Dialog` | `Onboarding - Agent Ticket Dialog` |

### Server Script

| Tên cũ | Tên mới |
|--------|---------|
| `Haravan Login Customer Enrichment` | `Auth - Login Customer Enrich` |
| `Haravan Inside Enrichment` | `Auth - Inside Customer Enrich` |
| `Haravan Bitrix Customer Profile API` | `Profile - Bitrix Customer API` |
| `HD Ticket - Haravan Customer Profile Routing` | `Profile - Ticket Routing` |
| `Haravan API Create Onboarding Ticket` | `Onboarding - Create Ticket API` |
| `HD GitLab Popup API v2` | `GitLab - Ticket Issue API` |
| `generate_ai_summary` | `AI - Summary API` |
| `generate-ai-reply` | `AI - Reply Suggest API` |
| `send-ai-reply` | `AI - Send Reply API` |
| `haravan_ai_analyze_ticket` | `AI - Ticket Analyze API` |
| `HD Ticket AI Copilot` | `AI - Ticket Copilot Event` |
| `HD Ticket - Haravan Store URL Enrichment` | `Ticket - Store URL Enrich` |
| `HD Ticket Product Suggestion Mapping` | `Ticket - Product Suggestion Map` |
| `HD Ticket - Contact Phone Validation` | `Ticket - Contact Phone Validate` |
| `Haravan Public HD Ticket Attachments` | `Media - Ticket Attachment Public` |
| `Haravan Public HD Ticket Inline Media` | `Media - Ticket Inline Public` |
| `Haravan Assignment Email Bilingual` | `Email - Assignment Bilingual` |
| `Haravan Ack Email Subject SLA` | `Email - Ack Subject SLA` |

## Quy trình bảo trì

1. Khi thêm script mới, **chọn module trước** khi đặt tên.
2. Nếu script là API, ghi rõ `api_method` trong tài liệu này và **không đổi endpoint** nếu UI đang gọi.
3. Nếu script là event, ghi rõ `Reference DocType` và event.
4. Sau khi sửa script, **cập nhật danh sách** trong file này.
5. Trước khi xoá script cũ, cần backup record và ghi lý do xoá trong cleanup execution log.
