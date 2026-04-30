---
title: Helpdesk Script Registry
description: Quy uoc dat ten va ban do chuc nang cac script tren Haravan Helpdesk
keywords: frappe, helpdesk, script, registry, haravan
robots: noindex, follow
---

# Helpdesk Script Registry

Tai lieu nay la ban do dat ten va phan nhom cac script dang quan ly truc tiep tren Haravan Helpdesk:

```text
https://haravan.help
```

Muc tieu la nhin vao ten script co the biet ngay script thuoc module nao, flow nao, va lam viec gi. Ten record duoc dung nhu inventory/operations label; logic dai han nen duoc dua dan ve source-controlled code trong app `login_with_haravan`.

## Quy uoc dat ten

Dung mau ten ngan gon:

```text
<Module> - <Flow/Context> <Action>
```

Vi du:

```text
Auth - Login Customer Enrich
AI - Ticket Analyze API
Ticket - Intake Field Rules
```

Quy tac:

- Module dung mot trong cac nhom chinh: `Auth`, `Profile`, `AI`, `GitLab`, `Ticket`, `Media`, `Email`, `Onboarding`.
- Ten action dung dong tu ngan: `Enrich`, `Analyze`, `Map`, `Validate`, `Filter`, `Public`, `Button`, `API`, `Event`.
- Server Script dang API duoc phep doi ten record, nhung `api_method` phai giu nguyen neu UI/logic cu con goi endpoint do.
- Script dang bi nghi ngo hoac chua can dung thi disabled, khong xoa ngay neu chua co backup/decision ro rang.
- Logic mapping/validation quan trong nen uu tien dua ve server-side/source-controlled logic thay vi rai trong Client Script hoac HD Form Script.

## Module Ownership

| Module | Pham vi | Trang thai hien tai |
| --- | --- | --- |
| `Auth` | Login Haravan, lien ket account, lam giau `HD Customer` khi login/register | Giu; `Auth - Login Customer Enrich` dang bat |
| `Profile` | Customer Profile cho agent, Bitrix backup/passive lookup | Giu; can tiep tuc development |
| `AI` | Gom cac API va action AI: phan tich, tom tat, goi y tra loi, gui reply | Giu; can gom UI thanh mot menu AI |
| `GitLab` | Tao/xem issue GitLab tu ticket | Giu |
| `Ticket` | Field dependency, validate, mapping du lieu ticket | Giu phan co ban; refactor dan ve server-side |
| `Media` | Attachment va inline media de khach xem duoc file/anh | Giu |
| `Email` | Email automation, subject/SLA, bilingual assignment | Giu |
| `Onboarding` | Tao ticket onboarding/agent-created customer ticket | Giu neu con can flow tao ticket tu agent/API |

## Current Inventory

### HD Form Script

Tat ca `HD Form Script` hien dang enabled. Day la cac script UI trong Helpdesk portal/desk form.

| Script | Flow | Muc dich |
| --- | --- | --- |
| `AI - Ticket Assist Menu` | AI / Ticket | Menu/action AI tong hop cho agent |
| `AI - Ticket Analyze Action` | AI / Ticket | Nut/action phan tich ticket |
| `GitLab - Ticket Issue Button` | GitLab / Ticket | Popup day du: tao issue, tim/link issue, xem lien ket hien tai, sync, go mapping |
| `Profile - Ticket Customer Button` | Profile / Ticket | Custom button xem ho so khach hang |
| `Ticket - Intake Field Rules` | Ticket / Intake | Required/visible/validate co ban khi tao ticket |
| `Ticket - Onboarding Phase Filter` | Ticket / Field dependency | Loc phase onboarding theo loai/service |
| `Ticket - Service Line Filter` | Ticket / Field dependency | Loc service line |
| `Ticket - Service Name Filter` | Ticket / Field dependency | Loc service name |
| `Ticket - Service Vendor Filter` | Ticket / Field dependency | Loc service vendor |

### Client Script

| Script | Doctype/View | State | Muc dich |
| --- | --- | --- | --- |
| `Onboarding - Agent Ticket Dialog` | `HD Ticket` / Form | Enabled | Dialog de agent tao ticket cho khach |

### Server Script

| Script | Type | Event/API | State | Muc dich |
| --- | --- | --- | --- | --- |
| `Auth - Login Customer Enrich` | DocType Event | `Haravan Account Link / After Save` | Enabled | Lam giau `HD Customer` chu dong sau login/register Haravan |
| `Auth - Inside Customer Enrich` | DocType Event | `HD Ticket / Before Save` | Enabled | Lam giau ticket/customer tu Inside/nguon noi bo |
| `Profile - Bitrix Customer API` | API | `haravan_bitrix_customer_profile` | Enabled | Lay Customer Profile tu Bitrix theo nhu cau agent |
| `Profile - Ticket Routing` | DocType Event | `HD Ticket / Before Save` | Enabled | Routing ticket theo profile/segment khach hang |
| `Onboarding - Agent Ticket API` | API | `haravan_agent_create_customer_ticket` | Enabled | Backend cho dialog agent tao ticket cho khach |
| `Onboarding - Create Ticket API` | API | `haravan_helpdesk.api.create_onboarding_ticket` | Enabled | Tao onboarding ticket tu API |
| `GitLab - Ticket Issue API` | API | `haravan_helpdesk.api.gitlab_popup_v2` | Enabled | Backend API cho popup GitLab |
| `AI - Summary API` | API | `generate-ai-summary` | Enabled | Tao tom tat ticket |
| `AI - Reply Suggest API` | API | `generate-ai-reply` | Enabled | Goi y noi dung reply |
| `AI - Send Reply API` | API | `send-ai-reply` | Enabled | Gui reply tu ket qua AI |
| `AI - Ticket Analyze API` | API | `haravan_ai_analyze_ticket` | Enabled | Phan tich/phan loai ticket bang AI |
| `AI - Ticket Copilot Event` | DocType Event | `HD Ticket / After Insert` | Enabled | Tu dong tao goi y routing/next step sau khi tao ticket |
| `Ticket - Store URL Enrich` | DocType Event | `HD Ticket / Before Validate` | Enabled | Chuan hoa store URL, doc `meta.json`, map OrgID/MyHaravan |
| `Ticket - Product Suggestion Map` | DocType Event | `HD Ticket / Before Validate` | Enabled | Map product suggestion sang product line/feature |
| `Ticket - Contact Phone Validate` | DocType Event | `HD Ticket / Before Validate` | Enabled | Validate so dien thoai lien he |
| `Media - Ticket Attachment Public` | DocType Event | `File / After Save` | Enabled | Dam bao attachment ticket public khi can |
| `Media - Ticket Inline Public` | DocType Event | `Communication / After Save` | Enabled | Dam bao inline media trong trao doi ticket public khi can |
| `Email - Assignment Bilingual` | DocType Event | `Notification Log / Before Insert` | Enabled | Email phan cong song ngu |
| `Email - Ack Subject SLA` | DocType Event | `Email Queue / Before Insert` | Enabled | Chuan hoa subject/noi dung email acknowledgement/SLA |

## Rename Mapping Applied

### HD Form Script

| Ten cu | Ten moi |
| --- | --- |
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

| Ten cu | Ten moi |
| --- | --- |
| `HD Ticket - Agent Create Customer Ticket Dialog` | `Onboarding - Agent Ticket Dialog` |

### Server Script

| Ten cu | Ten moi |
| --- | --- |
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

## Maintenance Workflow

1. Khi them script moi, chon module truoc khi dat ten.
2. Neu script la API, ghi ro `api_method` trong document nay va khong doi endpoint neu UI dang goi.
3. Neu script la event, ghi ro `Reference DocType` va event.
4. Sau khi sua script, cap nhat inventory trong file nay.
5. Truoc khi xoa script cu, can backup record va ghi ly do xoa trong cleanup execution log.
