## 1. Bảng mapping chính xác

### Các trường yêu cầu (11 field gốc + ID)

| Hiển thị popup | Field Bitrix | Giá trị mẫu | Loại |
|---|---|---|---|
| Tên Công ty | `TITLE` | `" ĐẦM XINH Shop - 1000069494"` | string |
| Company ID (Haravan) | `UF_CRM_COMPANY_ID` | `1000069494` | string/integer |
| Bitrix ID (nội bộ) | `ID` | `63962` | integer |
| Current_HSI_Segment | `UF_CRM_CURRENT_HSI_SEGMENT` | `"HSI_1"` | string |
| Current_HSI_Detail | `UF_CRM_CURRENT_HSI_DETAIL` | `"0E-7"` | string (số dạng scientific) |
| Last_HSI_Segment | `UF_CRM_LAST_HSI_SEGMENT` | `"HSI_1"` | string |
| Last_HSI_Detail | `UF_CRM_LAST_HSI_DETAIL` | `"0E-7"` | string |
| Gói Shopplan hiện tại | `UF_CRM_CURRENT_SHOPPLAN` | `"Chuyên nghiệp"` | string |
| Ngày tạo shop | `UF_CRM_DATE_CREATED_SHOP` | `"2016-01-19T11:12:14+03:00"` | datetime |
| Ngày ký gói Shopplan đầu tiên | `UF_CRM_FIRST_PAID_DATE` | `"2016-01-20T12:42:35+03:00"` | datetime |
| Ngày ký gói Shopplan hiện tại | `UF_CRM_DATE_SIGNED_CURRENT_SHOPPLAN` | `"2016-01-20T12:43:00+03:00"` | datetime |
| Ngày hết hạn Shopplan | `UF_CRM_DATE_EXPIRED_SHOPPLAN` | `"2020-01-20T12:42:37+03:00"` | datetime |

### Các trường bonus đáng cân nhắc thêm vào popup

| Hiển thị | Field Bitrix | Giá trị mẫu | Ghi chú |
|---|---|---|---|
| Chủ shop | `UF_CRM_SHOP_OWNER_NAME` | `"Thảo Vũ Phương"` | Hữu ích cho agent |
| Email chủ shop | `UF_CRM_SHOP_OWNER_EMAIL` | `"damdepdamxinh@gmail.com"` | |
| SĐT chủ shop | `UF_CRM_SHOP_OWNER_PHONE_NUMBER` | `"0906665140"` | |
| Tên store | `UF_CRM_STORENAME` | `" ĐẦM XINH Shop"` | Phần tên không có ID |
| Membership | `UF_CRM_HARAVAN_MEMBERSHIP` | `"Member"` | |
| Update note | `UF_CRM_661742530FDE6` | `"UPDATE ALL 06-05-2024"` | Ghi chú gần nhất |
| Ngày tạo Bitrix | `DATE_CREATE` | `"2024-03-31T03:12:32+03:00"` | Khác với "Ngày tạo shop" |
| Phụ trách (Assigned) | `ASSIGNED_BY_ID` | `338` | Cần resolve qua `user.get` |

---

## 2. Quan sát quan trọng từ dữ liệu

### 2.1 Timezone Bitrix là `+03:00` (Moscow)

Dù portal là `.vn`, server Bitrix trả timezone Moscow. Khi hiển thị cho agent Việt Nam:
- Convert sang `+07:00` (Asia/Ho_Chi_Minh) **hoặc**
- Hiển thị đúng ngày (bỏ giờ) vì các field này về bản chất là ngày, không phải timestamp.

Khuyến nghị: **chỉ hiển thị ngày** (`dd/mm/yyyy`), tránh confusion về timezone.

### 2.2 `UF_CRM_CURRENT_HSI_DETAIL = "0E-7"` là số khoa học

Đây là cách Python/PHP serialize `Decimal(0)` ở precision 7 → `"0.0000000"`. Có 2 hướng xử lý:

**Cách A**: Convert về float để hiển thị đẹp:
```python
try:
    v = float(value)
    value = f"{v:.4f}"  # "0.0000"
except (ValueError, TypeError):
    pass
```

**Cách B**: Hiển thị raw, agent quen với format này.

Khuyến nghị: dùng Cách A, format thành `"0.00"` hoặc `"—"` nếu = 0.

### 2.3 `UF_CRM_CURRENT_SHOPPLAN` đã là text "Chuyên nghiệp"

→ Field này là **string thường**, không phải enumeration. **KHÔNG cần** resolve qua `userfield.list` để lấy label. Hiển thị trực tiếp.

### 2.4 `TITLE` chứa cả tên + Company ID

`" ĐẦM XINH Shop - 1000069494"` — có khoảng trắng đầu và đuôi là Haravan ID. Dùng `UF_CRM_STORENAME` (`" ĐẦM XINH Shop"`) sẽ sạch hơn cho hiển thị tên thuần. Tốt nhất `.strip()` trước khi render.

### 2.5 Nhiều UF rỗng — không vấn đề

Phần lớn `UF_CRM_xxxxxxxxx` là rỗng (do legacy field cũ chưa dùng). Code chỉ map những field cần là đủ.

---

## 3. Code Server Script Frappe (đã update với mapping thật)

```python
import frappe
import requests
from datetime import datetime

# === 1. Validate ===
orgid = frappe.form_dict.get("orgid")
if not orgid:
    frappe.throw("Thiếu orgid")

allowed_roles = {"Agent", "HD Agent", "HD Manager", "System Manager"}
if not (set(frappe.get_roles()) & allowed_roles):
    frappe.throw("Không có quyền xem hồ sơ khách hàng", frappe.PermissionError)

webhook_url = frappe.conf.get("bitrix_webhook_url")
if not webhook_url:
    frappe.throw("Chưa cấu hình bitrix_webhook_url")

# === 2. Cache ===
cache_key = f"bitrix_company_orgid_{orgid}"
cached = frappe.cache().get_value(cache_key)
if cached:
    frappe.response["message"] = cached
    return

# === 3. Field mapping (CHÍNH XÁC theo data thật) ===
FIELD_MAP = {
    # Định danh
    "ID":                                  "bitrix_id",
    "TITLE":                               "title_full",
    "UF_CRM_STORENAME":                    "company_name",
    "UF_CRM_COMPANY_ID":                   "company_id",

    # HSI
    "UF_CRM_CURRENT_HSI_SEGMENT":          "current_hsi_segment",
    "UF_CRM_CURRENT_HSI_DETAIL":           "current_hsi_detail",
    "UF_CRM_LAST_HSI_SEGMENT":             "last_hsi_segment",
    "UF_CRM_LAST_HSI_DETAIL":              "last_hsi_detail",

    # Shopplan
    "UF_CRM_CURRENT_SHOPPLAN":             "current_shopplan",
    "UF_CRM_DATE_CREATED_SHOP":            "shop_created_date",
    "UF_CRM_FIRST_PAID_DATE":              "first_shopplan_date",
    "UF_CRM_DATE_SIGNED_CURRENT_SHOPPLAN": "current_shopplan_date",
    "UF_CRM_DATE_EXPIRED_SHOPPLAN":        "shopplan_expiry",

    # Bonus — chủ shop & metadata
    "UF_CRM_SHOP_OWNER_NAME":              "owner_name",
    "UF_CRM_SHOP_OWNER_EMAIL":             "owner_email",
    "UF_CRM_SHOP_OWNER_PHONE_NUMBER":      "owner_phone",
    "UF_CRM_HARAVAN_MEMBERSHIP":           "membership",
    "ASSIGNED_BY_ID":                      "assigned_by_id",
}

DATE_FIELDS = {
    "shop_created_date",
    "first_shopplan_date",
    "current_shopplan_date",
    "shopplan_expiry",
}

DECIMAL_FIELDS = {
    "current_hsi_detail",
    "last_hsi_detail",
}

# === 4. Gọi Bitrix ===
try:
    resp = requests.post(
        webhook_url + "crm.company.list.json",
        json={
            "FILTER": {"UF_CRM_COMPANY_ID": str(orgid)},
            "SELECT": list(FIELD_MAP.keys()),
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
except requests.exceptions.Timeout:
    frappe.throw("Bitrix24 timeout, vui lòng thử lại")
except requests.exceptions.RequestException as e:
    frappe.log_error(f"Bitrix call failed: {e}", "Bitrix Integration")
    frappe.throw("Không kết nối được Bitrix24")

if data.get("error"):
    frappe.throw(f"Bitrix error: {data.get('error_description', data['error'])}")

results = data.get("result", [])
if not results:
    frappe.throw(f"Không tìm thấy công ty với Company ID = {orgid}")
if len(results) > 1:
    frappe.log_error(
        f"Multiple companies for UF_CRM_COMPANY_ID={orgid}: "
        f"{[r['ID'] for r in results]}",
        "Bitrix Integration - Duplicate"
    )

raw = results[0]

# === 5. Transform ===
def parse_bitrix_date(value):
    """Bitrix trả ISO 8601 với timezone +03:00. Trả về 'dd/mm/yyyy' theo VN."""
    if not value:
        return None
    try:
        # parse ISO, giữ timezone gốc, chỉ lấy phần ngày
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return value

def format_decimal(value):
    """Convert '0E-7' → '0.00' để dễ đọc."""
    if value in (None, ""):
        return None
    try:
        f = float(value)
        if f == 0:
            return "0"
        return f"{f:.4f}".rstrip("0").rstrip(".")
    except (ValueError, TypeError):
        return value

result = {}
for bx_field, out_key in FIELD_MAP.items():
    value = raw.get(bx_field)

    # Strip whitespace cho string
    if isinstance(value, str):
        value = value.strip()

    # Multi-value (PHONE/EMAIL gốc, không áp với UF_CRM_SHOP_OWNER_*)
    if isinstance(value, list) and value and isinstance(value[0], dict):
        value = value[0].get("VALUE")

    # Format
    if out_key in DATE_FIELDS:
        value = parse_bitrix_date(value)
    elif out_key in DECIMAL_FIELDS:
        value = format_decimal(value)

    result[out_key] = value

# === 6. (Tuỳ chọn) Resolve assigned user → tên ===
# Cần scope user_basic. Nếu chưa cấp, comment block này.
if result.get("assigned_by_id"):
    try:
        user_resp = requests.post(
            webhook_url + "user.get.json",
            json={"ID": result["assigned_by_id"]},
            timeout=5,
        ).json()
        if user_resp.get("result"):
            u = user_resp["result"][0]
            result["assigned_by_name"] = f"{u.get('NAME','')} {u.get('LAST_NAME','')}".strip()
    except Exception as e:
        frappe.log_error(f"Resolve user failed: {e}", "Bitrix Integration")

# === 7. Cache & return ===
frappe.cache().set_value(cache_key, result, expires_in_sec=300)
frappe.response["message"] = result
```

---

## 4. Update Form Script (popup HTML)

```javascript
function render_profile_dialog(data) {
    const fmt = (v) => v || '<span class="text-muted">—</span>';

    const html = `
    <div class="customer-profile">
        <table class="table table-bordered" style="margin-bottom:0;">
            <tr>
                <th colspan="2" style="background:#1f6feb;color:white;">
                    Thông tin chung
                </th>
            </tr>
            <tr>
                <th style="width:40%;">Tên Công ty</th>
                <td><b>${fmt(data.company_name)}</b></td>
            </tr>
            <tr>
                <th>Company ID (Haravan)</th>
                <td><code>${fmt(data.company_id)}</code></td>
            </tr>
            <tr>
                <th>Membership</th>
                <td>${fmt(data.membership)}</td>
            </tr>

            <tr>
                <th colspan="2" style="background:#f5f7fa;">Chủ shop</th>
            </tr>
            <tr><th>Họ tên</th><td>${fmt(data.owner_name)}</td></tr>
            <tr><th>Email</th><td>${fmt(data.owner_email)}</td></tr>
            <tr><th>SĐT</th><td>${fmt(data.owner_phone)}</td></tr>

            <tr>
                <th colspan="2" style="background:#f5f7fa;">Phân khúc HSI</th>
            </tr>
            <tr>
                <th>Current HSI Segment</th>
                <td><span class="badge badge-info">${fmt(data.current_hsi_segment)}</span></td>
            </tr>
            <tr><th>Current HSI Detail</th><td>${fmt(data.current_hsi_detail)}</td></tr>
            <tr>
                <th>Last HSI Segment</th>
                <td><span class="badge badge-secondary">${fmt(data.last_hsi_segment)}</span></td>
            </tr>
            <tr><th>Last HSI Detail</th><td>${fmt(data.last_hsi_detail)}</td></tr>

            <tr>
                <th colspan="2" style="background:#f5f7fa;">Shopplan</th>
            </tr>
            <tr>
                <th>Gói hiện tại</th>
                <td><b style="color:#1f6feb;">${fmt(data.current_shopplan)}</b></td>
            </tr>
            <tr><th>Ngày tạo shop</th><td>${fmt(data.shop_created_date)}</td></tr>
            <tr><th>Ngày ký gói đầu tiên</th><td>${fmt(data.first_shopplan_date)}</td></tr>
            <tr><th>Ngày ký gói hiện tại</th><td>${fmt(data.current_shopplan_date)}</td></tr>
            <tr><th>Ngày hết hạn</th><td>${fmt(data.shopplan_expiry)}</td></tr>
        </table>
    </div>`;

    const d = new frappe.ui.Dialog({
        title: __('Hồ sơ khách hàng - {0}', [data.company_name || data.company_id]),
        size: 'large',
        fields: [{ fieldtype: 'HTML', fieldname: 'profile_html' }],
        primary_action_label: __('Mở trên Bitrix24'),
        primary_action() {
            window.open(
                `https://haravan.bitrix24.vn/crm/company/details/${data.bitrix_id}/`,
                '_blank'
            );
            d.hide();
        },
        secondary_action_label: __('Đóng'),
        secondary_action() { d.hide(); }
    });

    d.fields_dict.profile_html.$wrapper.html(html);
    d.show();
}
```

> Đã sửa: nút "Mở trên Bitrix24" dùng `data.bitrix_id` (= `63962`), KHÔNG dùng `company_id` (Haravan ID, không phải Bitrix ID nội bộ).

---

## 5. Output dự kiến của API sau khi transform

Khi gọi `GET /api/method/get_bitrix_company?orgid=1000069494`:

```json
{
  "message": {
    "bitrix_id": "63962",
    "title_full": "ĐẦM XINH Shop - 1000069494",
    "company_name": "ĐẦM XINH Shop",
    "company_id": "1000069494",

    "current_hsi_segment": "HSI_1",
    "current_hsi_detail": "0",
    "last_hsi_segment": "HSI_1",
    "last_hsi_detail": "0",

    "current_shopplan": "Chuyên nghiệp",
    "shop_created_date": "19/01/2016",
    "first_shopplan_date": "20/01/2016",
    "current_shopplan_date": "20/01/2016",
    "shopplan_expiry": "20/01/2020",

    "owner_name": "Thảo Vũ Phương",
    "owner_email": "damdepdamxinh@gmail.com",
    "owner_phone": "0906665140",
    "membership": "Member",

    "assigned_by_id": "338",
    "assigned_by_name": "Nguyễn Văn A"
  }
}
```

---

## 6. Một vài cảnh báo từ data này

1. **Shop đã hết hạn từ 2020** (`shopplan_expiry: 20/01/2020`). Có thể agent cần thấy cảnh báo hết hạn ngay trên popup. Gợi ý: thêm logic so sánh ngày hiện tại với `shopplan_expiry`, nếu < today → hiển thị badge đỏ "ĐÃ HẾT HẠN".

2. **HSI Detail = `0E-7`** ở cả current và last → khách hàng có HSI score = 0, có thể là tài khoản không active. Đáng để team CS biết.

3. **`COMPANY_TYPE` rỗng** trên record này. Nếu logic Frappe có filter "chỉ show CUSTOMER", sẽ bỏ sót những record như thế này. Kiểm tra lại.

4. **`HAS_PHONE = N`, `HAS_EMAIL = N`** ở field chuẩn của Bitrix, nhưng `UF_CRM_SHOP_OWNER_PHONE_NUMBER` và `UF_CRM_SHOP_OWNER_EMAIL` thì có. Tức là bên Haravan-Bitrix lưu contact ở UF chứ không dùng field PHONE/EMAIL chuẩn. → Đúng, popup nên lấy từ UF như code đã làm.

---

## 7. Logic gợi ý: cảnh báo Shopplan hết hạn

Thêm vào Server Script:

```python
from datetime import datetime, timezone

# Sau khi build result, thêm:
expiry_str = raw.get("UF_CRM_DATE_EXPIRED_SHOPPLAN")
if expiry_str:
    try:
        expiry = datetime.fromisoformat(expiry_str)
        now = datetime.now(timezone.utc)
        days_left = (expiry - now).days
        result["shopplan_status"] = (
            "expired" if days_left < 0
            else "expiring_soon" if days_left < 30
            else "active"
        )
        result["shopplan_days_left"] = days_left
    except Exception:
        pass
```

Phía client render thêm badge trạng thái:
```javascript
const status_badge = {
  expired: '<span class="badge badge-danger">ĐÃ HẾT HẠN</span>',
  expiring_soon: '<span class="badge badge-warning">SẮP HẾT HẠN</span>',
  active: '<span class="badge badge-success">CÒN HIỆU LỰC</span>'
}[data.shopplan_status] || '';
```
