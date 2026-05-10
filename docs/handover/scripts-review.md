# Scripts Review Checklist

> Cập nhật: 2026-05-10 | Site: https://haravandesk.s.frappe.cloud/

## Tóm tắt inventory

### Server Script active
- **API**: 19 script active
- **DocType Event**: 16 script active
- **Scheduler Event**: 3 script active
- 4 script `Patch - ...` vẫn đang active (cần review disable)

### Form/Client Script active
- **HD Form Script**: 13 active cho `HD Ticket`
- **Client Script**: 1 active (`Onboarding - Agent Ticket Dialog`)

## Vấn đề ưu tiên

### P0 — Đã xử lý ✅

- [x] Bỏ debug logger local khỏi Form Script production
- [x] Thêm permission gate cho API mutate (transfer, AI reply, agent create)
- [x] Giảm swallow exception — thêm `frappe.log_error()` cho outer catch

### P0 — Chưa xử lý

- [ ] Giảm/loại bỏ `ignore_permissions=True` trong transfer flow
- [ ] Hợp nhất hai luồng assignment đang cạnh tranh (event sync + scheduler)

### P1 — Refactor

- [ ] Chuyển `Patch - ...` scripts sang disabled
- [ ] Review data retention Email Queue
- [ ] Review luồng public hóa attachment
- [ ] Chuẩn hóa external request guard (timeout, cache, allowlist)
- [ ] Chuẩn hóa response envelope

### P2 — Maintainability

- [ ] Tách shared JS utilities cho Form Script
- [ ] Đưa option/filter rules ra config
- [ ] Giảm `window.location.reload()` sau action
- [ ] Cải thiện Client Script Agent Ticket Dialog

## Kế hoạch cải tiến

### Phase 1: Safety cleanup ✅ Done
### Phase 2: Stabilize routing/assignment ⏳ Pending
### Phase 3: Data/security hardening ⏳ Pending
### Phase 4: Maintainability ⏳ Pending

## Tham chiếu

- [Script Catalog](/operations/script-catalog) — Registry đầy đủ
- [safe_exec Gotchas](/architecture/safe-exec) — Lưu ý code
