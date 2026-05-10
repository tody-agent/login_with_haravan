---
title: Haravan Helpdesk Data Model
description: Data model and script ownership reference aligned with the canonical script catalog.
robots: noindex, nofollow
---

# Haravan Helpdesk Data Model

Updated: 2026-05-09

## Purpose

This document describes key entities and fields for Helpdesk operations, and links script ownership to the canonical script catalog.

Canonical script source of truth:
`/docs/haravan/ticket-customer-enrichment`

## Core Entities

- `HD Ticket`: ticket lifecycle, enrichment snapshots, route fields, assignment target.
- `HD Customer`: organization-level customer profile and Bitrix sync anchor.
- `Contact`: person-level identity linked to tickets/customers.
- `Haravan Account Link`: identity link between user and Haravan organization.
- `HD Customer Data`: external enrichment snapshots (mainly Bitrix).

## Script Ownership by Group

| Group | Main Entity | Typical Responsibilities |
|---|---|---|
| Intake | `HD Ticket` | Create tickets from onboarding or agent-side dialogs. |
| Validation | `HD Ticket` | Normalize incoming values without blocking ticket creation. |
| Enrichment | `HD Ticket`, `HD Customer` | Resolve orgid/domain and sync customer profile data. |
| Routing | `HD Ticket` | Set/normalize routing fields and `agent_group`. |
| Assignment | `HD Ticket` | Apply assignment rule outcomes to team/agent flow. |
| Profile | `HD Ticket`, `HD Customer`, `Contact` | Manual/deep profile sync actions. |
| Integration | `HD Ticket` + external systems | GitLab and automation integrations. |
| Debug | Any | Non-production diagnostics and replay snapshots. |

## Status Policy

- `Active`: used in production runtime.
- `Debug`: diagnostics only.
- `Not use`: intentionally disabled, kept for traceability.
- `Legacy`: historical/migration references.

## Field Contracts (Routing + Enrichment)

Important `HD Ticket` fields for script interaction:

- `customer`
- `custom_orgid`
- `custom_store_url`
- `custom_myharavan_domain`
- `custom_customer_segment`
- `custom_current_shopplan`
- `custom_partner_service`
- `custom_customer_lifetime_months`
- `agent_group`

Legacy fallback-only fields:

- `custom_haravan_profile_orgid`
- `custom_my_haravan_domain`
- `custom_haravan_myharavan_link`
- `custom_haravan_shop_link`

## Naming Governance

- Production script names must follow `<Type> - <Group> - <Purpose>`.
- Debug script names must follow `Debug - {group} - {name}`.
- Any deactivated script must be marked as `Not use` in the canonical catalog.

## Related

- `/docs/haravan/ticket-customer-enrichment`
- `/docs/haravan/ticket-workflow-review-summary`
- `/docs/haravan/gitlab-assignee-routing-handover`
---
title: Haravan Helpdesk Data Model
description: Field guide for AI agents working with haravan.help Frappe Helpdesk data.
keywords: haravan.help, frappe helpdesk, hd ticket, hd customer, data model
robots: noindex, nofollow
---

# Haravan.help Helpdesk Data Model

This document helps AI agents understand how the production site `haravan.help`
stores Helpdesk data for tickets, customers, contacts, Haravan identities, and
Bitrix enrichment.

## Operational Snapshot (2026-05-08)

- `Ticket - Auto Customer Sync From OrgID` is enabled (`After Save`) and is the primary automatic enrichment path.
- `Ticket - Normalize Enrichment Routing After Save` is enabled (`After Save`) to keep enrichment/routing fields consistent after late updates.
- `Ticket - Auto Customer Sync Kickoff After Insert` is currently disabled.
- Legacy gate/early enrichment scripts are disabled: `Ticket - Require Customer Or Store URL`, `Ticket - Store URL Enrich`.
- Routing and round-robin scripts are currently disabled: `Profile - Ticket Routing`, `Profile - Ticket Round Robin Assignment`.
- End-to-end workflow and current script status are documented in `docs/haravan/ticket-customer-enrichment.md`.

The site is a Frappe Helpdesk instance extended by the custom app
`login_with_haravan`. Do not modify Frappe core or Helpdesk core. Use custom
fields, hooks, Server Scripts, Form Scripts, and the custom DocTypes from this
app.

## Data Flow Summary

1. Customer signs in with Haravan OAuth.
2. `login_with_haravan.oauth.login_via_haravan` normalizes the Haravan profile.
3. The app upserts:
   - `User`
   - `Contact`
   - `HD Customer`
   - `Haravan Account Link`
4. Customer creates a Helpdesk ticket in `/helpdesk/my-tickets/new`.
5. Ticket is stored as `HD Ticket`, linked to `HD Customer` through `customer`.
6. Agent-side customer profile can enrich `HD Customer`, `Contact`, and ticket
   fields from Bitrix on demand.

## Core Relationships

```mermaid
erDiagram
    User ||--o{ HaravanAccountLink : "logs in from"
    HaravanAccountLink }o--|| HDCustomer : "maps org to"
    HDCustomer ||--o{ HDTicket : "customer"
    Contact }o--o{ HDCustomer : "Dynamic Link"
    HDCustomer ||--o{ HDCustomerData : "external snapshots"
    Contact ||--o{ HDCustomerData : "optional contact match"
```

## `HD Ticket`

`HD Ticket` is the primary support ticket DocType from Frappe Helpdesk. The
native Helpdesk fields are owned by the upstream app; the custom fields below
are the fields this project expects or manages.

### Important Native Fields

| Fieldname | Type | Description |
|---|---:|---|
| `name` | Data | Ticket document ID, often displayed as the ticket number. |
| `subject` | Data | Customer-visible issue title. |
| `description` | Text / Editor | Main customer issue description. Treat as user-generated content. |
| `status` | Link / Select | Ticket status used by Helpdesk workflows and list filters. |
| `priority` | Link / Select | Ticket priority. |
| `ticket_type` | Link / Select | Helpdesk ticket type/category when configured. |
| `customer` | Link -> `HD Customer` | The merchant/store/account that owns the ticket. This is the key field for org-level context. |
| `contact` | Link -> `Contact` | Contact person linked to the ticket. |
| `raised_by` | Data | Email/user that raised the ticket. Used as fallback to find `Contact`. |
| `agent_group` | Link -> `HD Team` | Team assignment. Routing scripts can set this from customer segment. |
| `agent` | Link -> `User` | Assigned support agent when Helpdesk assignment is used. |
| `creation` | Datetime | Ticket creation timestamp. |
| `modified` | Datetime | Last modification timestamp. |

### Project Custom Fields On `HD Ticket`

| Fieldname | Type | Description |
|---|---:|---|
| `custom_cc_emails` | Small Text | Ticket-level CC list. Emails are comma-separated. Used by `HDTicketCCMixin` to merge CC recipients into acknowledgement and agent reply emails. |
| `custom_responsible` | Data | Email of the responsible person resolved from Bitrix `user.get` by `ASSIGNED_BY_ID`. Read-only in the app metadata. |
| `custom_product_suggestion` | Link / Data | Product suggestion used by Helpdesk/GitLab automation. Customer portal template keeps it optional; agent workflows may still require it. |
| `custom_internal_type` | Select / Data | Internal ticket classification. When value is `Onboarding Service`, service-related internal fields become relevant. |
| `custom_service_group` | Select | Internal service group for onboarding-service tickets. Hidden from customers in the ticket template. |
| `custom_service_name` | Select | Internal service name for onboarding-service tickets. Hidden from customers. |
| `custom_service_line` | Select | Internal service line for onboarding-service tickets. Hidden from customers. |
| `custom_service_onboarding_phrase` | Select | Internal onboarding phrase/stage for service tickets. Hidden from customers. |
| `custom_service_pricing` | Currency | Internal service price. Hidden from customers. |
| `custom_service_transaction_id` | Data | Internal payment/transaction reference for service tickets. Hidden from customers. |
| `custom_service_vendor` | Select | Internal service provider/vendor. Hidden from customers. |
| `custom_service_payment_status` | Select | Internal payment status. Hidden from customers. |
| `custom_orgid` | Data | Canonical Haravan org ID cached on ticket by production scripts. Used by Bitrix routing/profile scripts. |
| `custom_haravan_profile_orgid` | Data | Hidden legacy Org ID mirror. Read only as fallback for old tickets; new enrichment writes should use `custom_orgid`. |
| `custom_customer_segment` | Select / Data | Customer segment: `SME`, `Medium`, or `Enterprise`. Copied from `HD Customer.custom_customer_segment` when available, otherwise resolved from Bitrix enum/fallback enrichment rules. |
| `custom_haravan_profile_status` | Data | Bitrix profile lookup status, for example `Complete`, `Skipped`, `Missing OrgID`, or `API Error`. |
| `custom_haravan_profile_error` | Small Text / Text | Last profile lookup/routing error message. |
| `custom_haravan_profile_checked_at` | Datetime | Last timestamp when profile/routing script checked the ticket. |
| `custom_haravan_service_plan` | Data | Current Haravan service/shop plan from Bitrix. |
| `custom_current_shopplan` | Data | Snapshot of current shopplan at ticket creation time (from `HD Customer.custom_shopplan_name` / Bitrix feed). Nullable, read-only. |
| `custom_partner_service` | Data | Snapshot partner/service routing key from Bitrix/Make at ticket creation time. Nullable, read-only. |
| `custom_customer_lifetime_months` | Int | Snapshot months from `HD Customer.custom_first_paid_date` (create-time snapshot; may be refreshed by consistency script after late enrichment events). |
| `custom_shopplan` | Select / Data | Normalized shop plan bucket such as `SME`, `Medium Grow`, or `Medium Scale`. |
| `custom_haravan_hsi_segment` | Data | HSI segment from Bitrix company fields. |
| `custom_haravan_routing_reason` | Small Text / Text | Human-readable reason for automatic team routing. |

Notes:

- `customer` is intentionally visible in the customer ticket template so the
  portal can choose the correct Haravan organization.
- `custom_cc_emails` is hidden from customer portal templates and mainly for
  agent-created tickets/replies.
- Service/onboarding fields are internal. Do not expose them in customer-facing
  UI unless the product requirement explicitly changes.

## `HD Customer`

`HD Customer` is the Helpdesk-native customer/account entity. For Haravan, one
`HD Customer` normally represents one Haravan organization/store.

### Important Native Fields

| Fieldname | Type | Description |
|---|---:|---|
| `name` | Data | Document ID. In this app it usually follows `"{orgname} - {orgid}"`. |
| `customer_name` | Data | Display name. The app writes `"{orgname} - {orgid}"`. |
| `domain` | Data | Store domain. The app defaults to `"{orgid}.myharavan.com"` when only org ID is known. |
| `image` | Attach Image | Optional customer image/logo if present in Helpdesk. |
| `creation` | Datetime | Customer creation timestamp. |
| `modified` | Datetime | Last modification timestamp. |

### Project Custom Fields On `HD Customer`

| Fieldname | Type | Description |
|---|---:|---|
| `custom_haravan_orgid` | Int | Primary Haravan organization ID. This is the deterministic lookup key for avoiding duplicate `HD Customer` records. |
| `custom_myharavan` | Data | MyHaravan domain, usually `"{orgid}.myharavan.com"`. |
| `custom_bitrix_company_id` | Data | Matched Bitrix company ID. |
| `custom_bitrix_company_url` | Data | Direct URL to the matched Bitrix company. |
| `custom_bitrix_match_confidence` | Percent | Confidence score for the Bitrix match. The app commonly writes `90` or `95`. |
| `custom_bitrix_sync_status` | Data | Bitrix sync status, for example `matched` or `not_found`. |
| `custom_bitrix_last_synced_at` | Datetime | Last time company/contact data was synced from Bitrix. |
| `custom_bitrix_last_checked_at` | Datetime | Last time production metajson/org lookup checked Bitrix, even if no company was found. |
| `custom_bitrix_company_modified_at` | Datetime | Bitrix company modification timestamp when provided by the Bitrix API. |
| `custom_bitrix_not_found_at` | Datetime | Last time Bitrix lookup did not find a matching company. |
| `custom_customer_segment` | Select / Data | Customer segment used by routing: `SME`, `Medium`, or `Enterprise`. |

Notes:

- Lookup priority should be `custom_haravan_orgid` first, then exact name.
- Do not create a competing custom organization DocType for ticket ownership;
  `HD Customer` is the canonical Helpdesk entity.
- `custom_customer_segment` may exist from production Server Scripts even if it
  is not declared directly in this app's install hook. The current live segment
  rule prefers the existing customer value, then Bitrix `UF_CRM_1778130421650`
  mapping (`15090` -> `SME`, `15092` -> `Medium`, `15094` -> `Enterprise`),
  then falls back to `Medium` for HSI `HSI_500+` / `500+` or shopplan
  `Grow` / `Scale`; otherwise it resolves `SME`.

## `Contact`

`Contact` is the Frappe contact person entity. It is upserted from Haravan login
data when an email exists.

| Fieldname | Type | Description |
|---|---:|---|
| `name` | Data | Contact document ID. |
| `first_name` | Data | Name from Haravan profile, or email prefix fallback. |
| `middle_name` | Data | Optional Haravan middle name. |
| `email_id` | Data | Primary email. Used to match existing contacts. |
| `phone` | Data | Phone number if present or later enriched. |
| `mobile_no` | Data | Mobile number if present or later enriched. |
| `links` | Child Table | Dynamic Links. Owner/admin Haravan users are linked to `HD Customer`; staff are not linked for org-wide visibility. |
| `custom_bitrix_contact_id` | Data | Matched Bitrix contact ID. |
| `custom_bitrix_contact_url` | Data | Direct URL to the matched Bitrix contact. |
| `custom_bitrix_last_synced_at` | Datetime | Last Bitrix contact sync timestamp. |

Visibility rule:

- Haravan roles `owner` and `admin` get a `Contact.links` row to `HD Customer`,
  allowing org-level ticket visibility.
- Staff or other roles do not get the org-wide `HD Customer` contact link, so
  they should see only their own tickets in portal behavior.

## `Haravan Account Link`

Custom DocType from this app. It stores the durable mapping between a Frappe
user, a Haravan user, and a Haravan organization.

Autoname is method-based in the controller. Treat records as upserted identity
links, not as free-form CRM records.

| Fieldname | Type | Required | Description |
|---|---:|---:|---|
| `user` | Link -> `User` | Yes | Frappe user account. |
| `email` | Data | Yes | User email from Haravan/Frappe. |
| `last_login` | Datetime | No | Last successful Haravan OAuth login timestamp. |
| `haravan_userid` | Data | Yes | Haravan user ID. |
| `haravan_orgid` | Data | Yes | Haravan organization ID. |
| `haravan_orgname` | Data | No | Haravan organization/store name. |
| `haravan_orgcat` | Data | No | Haravan organization category from profile claims. |
| `haravan_roles` | Small Text | No | Haravan role list serialized as text. |
| `raw_profile` | Code / JSON | No | Raw normalized login profile for troubleshooting. Contains identity data; avoid exposing broadly. |
| `hd_customer` | Link -> `HD Customer` | No | Helpdesk customer created or matched for this org. |

## `HD Customer Data`

Custom DocType from this app. It stores external data snapshots, mainly from
Bitrix company/contact enrichment.

Autoname format:

```text
BTRX-{entity_type}-{external_id}
```

| Fieldname | Type | Required | Description |
|---|---:|---:|---|
| `hd_customer` | Link -> `HD Customer` | Yes | Customer/account that the external entity belongs to. |
| `contact` | Link -> `Contact` | No | Related contact, when the external snapshot is contact-specific. |
| `source` | Data | Yes | External source name. Default is `bitrix`. |
| `entity_type` | Select | Yes | External entity type. Allowed values: `company`, `contact`. |
| `external_id` | Data | Yes | ID in the external system. |
| `external_url` | Data | No | Direct URL to the external record. |
| `match_key` | Data | No | Matching strategy, for example `domain_or_haravan_orgid` or `email_or_phone`. |
| `confidence` | Percent | No | Match confidence. |
| `last_synced_at` | Datetime | No | Last sync timestamp. |
| `summary_json` | Code / JSON | No | JSON snapshot returned by the external API. May contain operational CRM data. |

## `Helpdesk Integrations Settings`

This is a Helpdesk settings DocType extended with Bitrix configuration fields.
These fields are configuration, not ticket/customer business data.

| Fieldname | Type | Description |
|---|---:|---|
| `bitrix_customer_api_section` | Section Break | UI grouping for customer/company API settings. |
| `bitrix_enabled` | Check | Enables or disables Bitrix customer/company profile lookup. |
| `bitrix_webhook_url` | Password | Inbound webhook URL used server-side for Bitrix `crm.company.*`. Never expose to browser or docs with real secret. |
| `bitrix_responsible_api_section` | Section Break | UI grouping for responsible-user API settings. |
| `bitrix_responsible_webhook_url` | Password | Inbound webhook URL used server-side for Bitrix `user.get`. Never expose the real value. |
| `bitrix_portal_url` | Data | Bitrix portal base URL used to build record links. |
| `bitrix_timeout_seconds` | Int | Timeout for Bitrix API calls. Default in metadata is `15`. |
| `bitrix_refresh_ttl_minutes` | Int | Cache/refresh TTL. Default in metadata is `60`. |

## Agent Operating Rules

- Use Frappe APIs or REST resource APIs. Avoid raw SQL unless there is no safer
  ORM path.
- If raw SQL is required, use parameterized queries only.
- Log server-side exceptions with `frappe.log_error()`, not `frappe.logger`.
- API responses should follow:

```json
{"success": true, "data": {}, "message": "Human-readable message."}
```

- Treat these fields as sensitive or semi-sensitive:
  - `Helpdesk Integrations Settings.bitrix_webhook_url`
  - `Helpdesk Integrations Settings.bitrix_responsible_webhook_url`
  - `Haravan Account Link.raw_profile`
  - `HD Customer Data.summary_json`
- Do not translate or rewrite user-generated ticket fields such as `subject`
  and `description`.
- For Haravan org identity, prefer this lookup order:
  1. `HD Customer.custom_haravan_orgid`
  2. `Haravan Account Link.haravan_orgid`
  3. `HD Ticket.custom_orgid`
  4. `HD Customer.domain` / `custom_myharavan`

## Quick Query Patterns

Find a customer by Haravan org ID:

```python
customer = frappe.db.get_value(
    "HD Customer",
    {"custom_haravan_orgid": int(orgid)},
    ["name", "customer_name", "domain"],
    as_dict=True,
)
```

Find a ticket's customer profile:

```python
ticket = frappe.db.get_value(
    "HD Ticket",
    ticket_name,
    ["name", "customer", "contact", "raised_by", "custom_orgid"],
    as_dict=True,
)
```

Find Haravan orgs linked to a user:

```python
links = frappe.get_all(
    "Haravan Account Link",
    filters={"user": user},
    fields=["haravan_orgid", "haravan_orgname", "haravan_roles", "hd_customer"],
)
```

Find Bitrix snapshots for a customer:

```python
rows = frappe.get_all(
    "HD Customer Data",
    filters={"hd_customer": hd_customer, "source": "bitrix"},
    fields=["entity_type", "external_id", "external_url", "confidence", "last_synced_at"],
)
```

## Source Of Truth In This Repository

| Area | File |
|---|---|
| Custom field creation | `login_with_haravan/setup/install.py` |
| Haravan -> Helpdesk sync | `login_with_haravan/engines/sync_helpdesk.py` |
| Bitrix customer profile enrichment | `login_with_haravan/engines/customer_enrichment.py` |
| Ticket CC behavior | `login_with_haravan/overrides/hd_ticket.py` |
| `Haravan Account Link` schema | `login_with_haravan/login_with_haravan/doctype/haravan_account_link/haravan_account_link.json` |
| `HD Customer Data` schema | `login_with_haravan/login_with_haravan/doctype/hd_customer_data/hd_customer_data.json` |
| Production routing Server Script template | `scripts/deploy_profile_ticket_routing.py` |
| Production metajson/Bitrix enrichment script | `scripts/deploy_bitrix_metajson_enrichment.py` |

## Routing v2 notes

- Current rollout uses Assignment Rules + consistency scripts.
- `Ticket - Snapshot Enrichment Fields` (`Before Insert`) snapshots create-time enrichment values.
- `Ticket - Normalize Enrichment Routing After Save` (`After Save`) normalizes values for all late flows (`email`, API, custom lookup) and sets `agent_group` best-effort without recursive save.
- Active assignment posture:
  - `AR01 - Partner Service Routing` is disabled (prevent partner dual model conflict).
  - `AR02 - SME 9M Scale` active, guarded by empty `agent_group`.
  - `AR03 - SME 9M Grow` active, guarded by empty `agent_group`.
  - `AR04 - CS60p Fallback` active, guarded by empty `agent_group`.
  - Partner routing operates through `Partner - ... - Support Rotation` rules using `agent_group`.
