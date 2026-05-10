---
title: Ghi đè giao diện tiếng Việt
description: Cơ chế ép giao diện Helpdesk sang tiếng Việt và quy trình gỡ bỏ khi Frappe Helpdesk hỗ trợ native Vietnamese
keywords: frappe, helpdesk, tiếng việt, localization, ghi đè, haravan
robots: noindex, follow
---

# 🇻🇳 Ghi đè giao diện tiếng Việt

:::info Tóm tắt
Tài liệu mô tả cơ chế frontend override đang dùng để ép các nhãn giao diện Helpdesk về tiếng Việt trên customer portal Haravan. Đây là giải pháp **tạm thời có chủ đích** — gỡ bỏ khi Frappe Helpdesk hỗ trợ tiếng Việt đầy đủ.
:::

**URL áp dụng:**

```text
https://haravan.help/helpdesk/my-tickets
https://haravan.help/helpdesk/my-tickets/new
```

## Lý do tồn tại

Frappe Helpdesk hiện còn một số cụm từ frontend không đi qua translation layer thông thường của Frappe. Vì vậy, user đã chọn tiếng Việt vẫn thấy các nhãn tiếng Anh như:

- `Create`, `Filter`, `Columns`, `Last Modified`
- `Search`, `Subject`, `Status`, `Priority`
- `First response`, `Resolution`
- `Open`, `Resolved`, `Medium`
- `Empty - Choose a field to filter by`, `Add Filter`

**Nguyên tắc:** Không sửa Frappe core hoặc Helpdesk core. Tất cả override nằm trong custom app `login_with_haravan`.

## File liên quan

| File | Vai trò |
|------|---------|
| `login_with_haravan/public/js/helpdesk_vi_override.js` | Module frontend override — chứa dictionary, route guard, locale guard, MutationObserver, kill switch |
| `login_with_haravan/hooks.py` | Include script qua `web_include_js`, đặt sau các Helpdesk portal script khác |
| `login_with_haravan/tests/test_frontend_safety.py` | Test guard để đảm bảo override được scope đúng và không dùng API nguy hiểm |

## Cơ chế kích hoạt

Script chỉ chạy khi thoả **tất cả** điều kiện:

### 1. URL nằm trong customer Helpdesk route

```text
/helpdesk/my-tickets
/helpdesk/my-tickets/new
/my-tickets
/my-tickets/new
```

### 2. Locale được nhận diện là tiếng Việt

Kiểm tra theo thứ tự ưu tiên:

| Thứ tự | Nguồn |
|--------|-------|
| 1 | `frappe.boot.lang` |
| 2 | `frappe.boot.user_lang` |
| 3 | `frappe.boot.user.language` |
| 4 | `frappe.boot.sysdefaults.language` |
| 5 | `document.documentElement.lang` |
| 6 | `localStorage.preferred_language` |
| 7 | `localStorage.language` |
| 8 | `localStorage.lang` |
| 9 | Browser language fallback |

### 3. Không bật kill switch

Xem phần [Kill Switch](#kill-switch) bên dưới.

## Cơ chế dịch

Module sử dụng namespace:

```js
window.HaravanHelpdeskViOverride
```

### Các thành phần chính

| Thành phần | Chức năng |
|-----------|-----------|
| `TRANSLATIONS` | Dictionary exact-match cho button, toolbar, filter, sort, column, status, priority, SLA, empty/loading/toast, form tạo ticket |
| `translateRelativeTime()` | Dịch pattern thời gian như `in 4 days`, `12 hours ago`, `a day ago` |
| `translateElementAttributes()` | Dịch `placeholder`, `title`, `aria-label`, `label` |
| `translateTextNodes()` | Dịch text node khớp chính xác sau khi SPA render |
| `MutationObserver` | Theo dõi DOM mới của Vue SPA và chạy lại dịch sau khi dropdown/modal/table render |
| History watcher | Bắt `pushState`, `replaceState`, `popstate` để hỗ trợ SPA navigation |

Script **không** dùng replacement toàn trang bằng HTML. Nó chỉ đổi `nodeValue`, `textContent` của option, và attribute an toàn.

## Vùng không được dịch

Để tránh làm sai nội dung khách hàng, script bỏ qua các vùng:

| Loại | Selector/Quy tắc |
|------|-------------------|
| Input | `input`, `textarea`, `select` |
| Rich text editor | `.ProseMirror`, `.ql-editor`, `.tiptap`, `.text-editor` |
| Nội dung bài viết/comment | `.comment-content`, `.article-content`, `.ticket-subject`, `.ticket-description` |
| Marker thủ công | `[data-haravan-no-translate]`, `[data-haravan-user-content]`, `[data-user-content]` |
| Link ticket detail | Không phải route tạo ticket |

:::tip Mở rộng bảo vệ
Nếu sau này có component mới chưa được bảo vệ, thêm selector vào `CONTENT_SKIP_SELECTOR` hoặc `TEXT_SKIP_SELECTOR` **trước khi** mở rộng dictionary.
:::

## Kill Switch

Có 3 cách tắt override mà không cần gỡ code ngay:

### 1. Tắt bằng global flag

Chèn trước script override:

```js
window.HARAVAN_HELPDESK_VI_OVERRIDE_DISABLED = true;
```

### 2. Tắt bằng localStorage (cho một browser)

Mở DevTools Console:

```js
// Tắt
localStorage.setItem("haravan_helpdesk_vi_override_disabled", "1");
location.reload();

// Bật lại
localStorage.removeItem("haravan_helpdesk_vi_override_disabled");
location.reload();
```

### 3. Tắt bằng query string (debug nhanh)

```text
https://haravan.help/helpdesk/my-tickets?haravan_vi_override=0
https://haravan.help/helpdesk/my-tickets?hrv_vi_override=0
```

## Quy trình gỡ bỏ

:::warning Điều kiện
Chỉ gỡ bỏ khi upstream Frappe Helpdesk đã dịch đầy đủ các route customer portal.
:::

### Bước 1: Xác minh upstream đã cover native Vietnamese

Trên staging hoặc production clone:

1. Tạo user có language là Vietnamese.
2. Mở `/helpdesk/my-tickets`.
3. Mở filter dropdown, sort dropdown, columns dropdown.
4. Mở `/helpdesk/my-tickets/new`.
5. Tạo ticket test, kiểm tra validation, placeholder, toast, empty state.
6. Tìm cụm tiếng Anh còn sót bằng visual QA hoặc browser text scan.

Chỉ gỡ override khi **tất cả** các nhóm sau đã được dịch native:

- Navigation/page chrome
- Primary action và toolbar
- Search, autocomplete, picker
- Filter controls và operators
- Sort controls
- List footer và selection banner
- Column settings
- Ticket list fields
- Status, priority, SLA values
- New ticket form
- Empty/loading/toast states
- Relative time patterns

### Bước 2: Tắt tạm thời bằng kill switch

Trước khi xoá code, test bằng kill switch để so sánh:

```js
window.HARAVAN_HELPDESK_VI_OVERRIDE_DISABLED = true;
```

Nếu UI vẫn hoàn toàn tiếng Việt, tiếp tục bước xoá code.

### Bước 3–7: Xoá code và chạy test

1. Xoá include trong `hooks.py`.
2. Xoá file `login_with_haravan/public/js/helpdesk_vi_override.js`.
3. Cập nhật test guard trong `test_frontend_safety.py`.
4. Chạy `./test_gate.sh`.
5. Cập nhật tài liệu này thành archive note.

## Checklist vận hành

- [ ] Override chỉ chạy trên route customer portal.
- [ ] Override chỉ chạy khi user chọn tiếng Việt.
- [ ] Dictionary nằm trong một file duy nhất.
- [ ] Có kill switch để tắt nhanh.
- [ ] Không dịch input value hoặc rich-text content.
- [ ] Không dùng `.innerHTML`, `eval`, `new Function`, `document.write`, inline event handler.
- [ ] Test gate pass sau mỗi lần sửa dictionary.

## Bằng chứng Native Vietnamese

Hiện tại chưa có bằng chứng upstream đã cover đầy đủ tiếng Việt cho các route này. Khi có, thêm thông tin tại đây:

| Nguồn | Version/Commit | Ghi chú |
|-------|----------------|---------|
| Frappe Helpdesk | Chưa có | Chưa có |
