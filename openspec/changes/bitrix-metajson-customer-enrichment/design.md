# Design: Bitrix Metajson Customer Enrichment

## Context & Technical Approach

The user prefers a Desk-managed Server Script instead of custom app runtime code. The repository therefore keeps only the deployment/audit script in `scripts/`, while the production logic runs as Frappe `Server Script` API method `haravan_bitrix_metajson_company_enrichment`.

The sync is best-effort and bounded:

- missing `orgid` returns a skip response without logging,
- disabled/missing Bitrix config returns a skip response,
- `bitrix_refresh_ttl_minutes` prevents repeated API calls,
- Bitrix `DATE_MODIFY` and field-level comparisons prevent unnecessary writes,
- `HD Customer` creation/update is done only when a Bitrix company exists,
- duplicate Bitrix companies use the first result because the Bitrix query orders by newest `DATE_MODIFY`.

## Proposed Changes

### `scripts/deploy_bitrix_metajson_enrichment.py`

- Create/update `Server Script`: `Metajson - Bitrix Company Enrichment API`.
- API method: `haravan_bitrix_metajson_company_enrichment`.
- Create guard `Custom Field` records on `HD Customer` through REST, not app migration:
  - `custom_bitrix_last_checked_at`
  - `custom_bitrix_company_modified_at`
  - `custom_bitrix_not_found_at`

### Server Script Runtime

- Read `orgid`, optional `force`, and optional `hd_customer` from `frappe.form_dict`.
- Read `bitrix_webhook_url`, `bitrix_portal_url`, timeout, TTL, and enabled flag from `Helpdesk Integrations Settings`.
- Query Bitrix `crm.company.list` by `UF_CRM_HARAVAN_ORG_ID`, fallback to `UF_CRM_COMPANY_ID`.
- Resolve or create `HD Customer` if a company is found.
- Update only existing fields, based on DocType metadata.
- Upsert `HD Customer Data` snapshot when available.
- Keep source top-level, without helper functions or imports, to avoid Frappe safe_exec helper lookup issues.

### Tests

- Add unit coverage that the deployment script carries a compile-safe Server Script, does not depend on `login_with_haravan`, contains TTL/lock guards, and creates only the intended guard custom fields.

## Verification

- Run targeted Server Script source tests.
- Run `./test_gate.sh` before completion.
