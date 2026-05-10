# Lưu ý safe_exec (RestrictedPython)

> Bài học từ audit 2026-05-10 — Các gotcha khi viết Server Script trên Frappe Cloud

## Tổng quan

Frappe Cloud chạy Server Script trong môi trường `safe_exec` (RestrictedPython). Môi trường này có nhiều hạn chế so với Python thường.

::: warning QUAN TRỌNG
Các quy tắc dưới đây là **bắt buộc** cho mọi Server Script chạy trên Frappe Cloud.
Vi phạm sẽ gây `NameError` runtime mà **không có lỗi compile time**.
:::

## Quy tắc bắt buộc

### 1. Không dùng helper lồng helper

**❌ SAI:**
```python
def extract_candidates(text):
    def clean_candidate(s):  # Helper trong helper
        return s.strip()
    return [clean_candidate(c) for c in text.split(",")]
```

**✅ ĐÚNG:**
```python
# Inline thành block thẳng, không dùng def lồng nhau
candidates = []
for c in text.split(","):
    candidates.append(c.strip())
```

**Nguyên nhân:** RestrictedPython rewrite scope — hàm con không thấy hàm con khác qua closure.

### 2. Không dùng `any()`/`all()` với biến closure

**❌ SAI:**
```python
s_low = s.lower()
is_domain = any(sfx in s_low for sfx in [".vn", ".com"])
# NameError: name 's_low' is not defined
```

**✅ ĐÚNG:**
```python
s_low = s.lower()
is_domain = False
for sfx in [".vn", ".com", ".net", ".store", ".shop", ".asia"]:
    if sfx in s_low:
        is_domain = True
        break
```

**Nguyên nhân:** Generator/comprehension tạo scope mới, không thấy biến closure.

### 3. Không dùng `lambda` capture biến ngoài

**❌ SAI:**
```python
threshold = 10
items = filter(lambda x: x > threshold, numbers)
```

**✅ ĐÚNG:**
```python
threshold = 10
items = []
for x in numbers:
    if x > threshold:
        items.append(x)
```

### 4. Luôn dùng try/except + log error

```python
SCRIPT_TITLE = "Server Script - Enrichment - Auto Customer Sync From OrgID"
try:
    # ... logic chính ...
    pass
except Exception as e:
    frappe.log_error(
        message=f"ticket={doc.name}, error={str(e)}",
        title=SCRIPT_TITLE
    )
```

::: tip frappe.log_error
- `title` → lưu vào cột `error` của Error Log
- `message` → lưu vào cột `method` của Error Log
- Query log nên lọc theo `error` hoặc `method LIKE`
:::

### 5. Không dùng `doc.save()` trong After Save script

```python
# ❌ SAI — gây infinite loop
doc.save()

# ✅ ĐÚNG — ghi trực tiếp không trigger lại
frappe.db.set_value("HD Ticket", doc.name, {
    "custom_orgid": orgid,
    "customer": customer_name
}, update_modified=False)
```

## Tóm tắt nhanh

| Tránh | Dùng thay thế |
|---|---|
| `def` lồng `def` | Inline hoặc tuần tự |
| `any(... for ...)` với closure | `for` loop tường minh |
| `all(... for ...)` với closure | `for` loop tường minh |
| List/dict/set comprehension với closure | `for` loop + `append` |
| `lambda` capture biến ngoài | `for` loop hoặc truyền tham số |
| `doc.save()` trong After Save | `frappe.db.set_value(update_modified=False)` |
| `except: pass` (swallow error) | `except: frappe.log_error(...)` |

## Tham chiếu

- [Script Catalog](/operations/script-catalog) — Danh sách script production
- [Bitrix Routing](/integrations/bitrix-routing) — Luồng enrichment
