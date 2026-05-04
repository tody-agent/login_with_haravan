# Tài liệu tích hợp: Hiển thị hồ sơ khách hàng từ Bitrix24 trong Frappe Helpdesk Ticket

## 1. Mục tiêu & Luồng nghiệp vụ

Trong mỗi **HD Ticket** của Frappe Helpdesk có thể có `custom_orgid` hoặc các field org id liên quan. API sẽ dùng các giá trị này làm ứng viên `Company ID (Haravan)` bên Bitrix24, tức field `UF_CRM_COMPANY_ID`, rồi fallback qua `HD Customer.custom_haravan_orgid`, email/phone/domain nếu không match. Khi agent đang xử lý ticket, ấn nút **“Xem hồ sơ khách hàng”** trên form ticket để mở popup hiển thị thông tin công ty được kéo realtime từ Bitrix24.

```
┌─────────────────┐   click    ┌──────────────┐   API call   ┌──────────────┐
│ HD Ticket Form  │ ─────────► │ Server Script│ ───────────► │  Bitrix24    │
│ custom_orgid=10 │            │ (whitelisted)│              │  crm.company │
└─────────────────┘            └──────────────┘              └──────────────┘
        ▲                              │
        │      hiển thị popup          │
        └──────────────────────────────┘
```

Vì sao cần Server Script làm trung gian (không gọi thẳng Bitrix từ Form Script)?

* Giấu webhook secret của Bitrix (không lộ ra browser).
* Tránh CORS.
* Có thể cache, log, transform dữ liệu trước khi trả về client.

---

## 2. Mapping fields Bitrix24 ↔ Hiển thị

| Trường hiển thị (label)         | Field Bitrix24                   | Loại       | Ghi chú                        |
| ----------------------------------- | -------------------------------- | ----------- | ------------------------------- |
| Tên Công ty                       | `UF_CRM_STORENAME` / `TITLE`   | string      | Ưu tiên store name sạch, fallback `TITLE` |
| Company ID (Haravan)                | `UF_CRM_COMPANY_ID`            | string/int  | Giá trị business id từ Haravan |
| Bitrix ID nội bộ                    | `ID`                           | integer     | Chỉ dùng để mở URL/details |
| Current_HSI_Segment                 | `UF_CRM_CURRENT_HSI_SEGMENT`   | string      | Custom field                    |
| Current_HSI_Detail                  | `UF_CRM_CURRENT_HSI_DETAIL`    | string      | Custom field                    |
| Last_HSI_Segment                    | `UF_CRM_LAST_HSI_SEGMENT`      | string      | Custom field                    |
| Last_HSI_Detail                     | `UF_CRM_LAST_HSI_DETAIL`       | string      | Custom field                    |
| Gói Shopplan hiện tại            | `UF_CRM_CURRENT_SHOPPLAN`      | string      | Đã là text, không cần enum resolve |
| Ngày tạo shop                     | `UF_CRM_DATE_CREATED_SHOP`     | datetime    | Hiển thị `dd/MM/yyyy` |
| Ngày ký gói Shopplan đầu tiên | `UF_CRM_FIRST_PAID_DATE`       | datetime    | Hiển thị `dd/MM/yyyy` |
| Ngày ký gói Shopplan hiện tại  | `UF_CRM_DATE_SIGNED_CURRENT_SHOPPLAN` | datetime | Hiển thị `dd/MM/yyyy` |
| Ngày hết hạn Shopplan            | `UF_CRM_DATE_EXPIRED_SHOPPLAN` | datetime    | Dùng tính trạng thái shopplan |
| Người phụ trách                  | `ASSIGNED_BY_ID` → `user.get` | integer → user | Resolve bằng webhook Responsible, chỉ cập nhật khi `ACTIVE = true` |

---

## 3. Bước chuẩn bị: Lấy tên chính xác của custom fields trong Bitrix

### 3.1 Tạo Inbound Webhook lấy Customer/Company

1. Vào  **Applications → Developer resources → Other → Inbound webhook** .
2. Cấp scope: `crm`.
3. Lưu lại URL có dạng:
   ```
   https://your-portal.bitrix24.com/rest/1/abc123xyzsecret/
   ```
4. Cấu hình URL này vào field **Bitrix Customer Inbound Webhook URL** (`bitrix_webhook_url`) trong **Helpdesk Integrations Settings**.

### 3.2 Tạo Inbound Webhook lấy Responsible/User

Tạo thêm một inbound webhook riêng để gọi `user.get`:

1. Vào **Applications → Developer resources → Other → Inbound webhook**.
2. Cấp scope: `user_basic`.
3. Bitrix sẽ sinh URL dạng:
   ```text
   https://haravan.bitrix24.vn/rest/57792/{new_secret_key}/
   ```
4. Test nhanh API:
   ```bash
   curl "https://haravan.bitrix24.vn/rest/57792/{new_secret_key}/user.get.json?ID={ASSIGNED_BY_ID}"
   ```
5. Cấu hình URL này vào field **Bitrix Responsible Inbound Webhook URL** (`bitrix_responsible_webhook_url`) trong **Helpdesk Integrations Settings**.

API chỉ dùng các trường `ACTIVE`, `EMAIL`, `NAME`, `LAST_NAME`, `USER_TYPE`. Nếu `ACTIVE = true`, hệ thống cập nhật `EMAIL` vào `HD Ticket.custom_responsible`.

### 3.3 Lấy danh sách custom fields của Company

Gọi 1 lần để khám phá schema:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{}' \
  "https://your-portal.bitrix24.com/rest/1/abc123xyzsecret/crm.company.userfield.list.json"
```

Response sẽ trả về list, tìm các trường tương ứng theo `EDIT_FORM_LABEL`:

```json
{
  "result": [
    {
      "FIELD_NAME": "UF_CRM_1713790573",
      "USER_TYPE_ID": "string",
      "EDIT_FORM_LABEL": "Current HSI Segment",
      "MULTIPLE": "N"
    },
    {
      "FIELD_NAME": "UF_CRM_1713790580",
      "USER_TYPE_ID": "date",
      "EDIT_FORM_LABEL": "Ngày hết hạn Shopplan"
    }
  ]
}
```

Ghi lại `FIELD_NAME` thực tế. Trong tài liệu này tôi sẽ dùng các hằng số mang tính minh hoạ — bạn thay vào code cho đúng.

### 3.4 Test thử lấy 1 company

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"ID": 10}' \
  "https://your-portal.bitrix24.com/rest/1/abc123xyzsecret/crm.company.get.json"
```

Đảm bảo trả ra đầy đủ field cần thiết trước khi sang bước tiếp.

---

## 4. Cấu hình Frappe: Lưu Bitrix credentials an toàn

Production `haravandesk.s.frappe.cloud` dùng Single DocType **Helpdesk Integrations Settings** tại:

```text
/desk/helpdesk-integrations-settings
```

Trong tab **Bitrix**, cấu hình phải tách rõ 2 webhook:

1. **Bitrix Customer Inbound Webhook URL** (`bitrix_webhook_url`)
   - Dùng để lấy hồ sơ customer/company.
   - Bitrix method: `crm.company.list`, `crm.company.get`, và các method `crm.*` liên quan.
   - Scope cần cấp trong Bitrix inbound webhook: `crm`.
2. **Bitrix Responsible Inbound Webhook URL** (`bitrix_responsible_webhook_url`)
   - Dùng để resolve `ASSIGNED_BY_ID` thành người phụ trách.
   - Bitrix method: `user.get`.
   - Scope cần cấp trong Bitrix inbound webhook: `user_basic`.
   - Có thể nhập base webhook `https://haravan.bitrix24.vn/rest/57792/{new_secret_key}/` hoặc full template `https://haravan.bitrix24.vn/rest/57792/{new_secret_key}/user.get.json?ID={ASSIGNED_BY_ID}`.
   - API test mẫu: mở full template với một `ASSIGNED_BY_ID` thật.

Nếu production form vẫn chỉ hiện field cũ **Bitrix Webhook URL**, chạy script metadata patch:

```bash
export HARAVAN_HELP_SITE='https://haravandesk.s.frappe.cloud'
export HARAVAN_HELP_API_KEY='...'
export HARAVAN_HELP_API_SECRET='...'
npm run patch:bitrix-settings
```

Script sẽ đổi label/description của webhook cũ thành customer webhook và tạo thêm field password responsible webhook. Script không in secret ra terminal và có backup metadata trong thư mục `backups/`.

Các field Bitrix đang dùng:

| Field | Type | Ghi chú |
| --- | --- | --- |
| `bitrix_enabled` | Check | Bật/tắt integration |
| `bitrix_webhook_url` | Password | Bitrix Customer Inbound Webhook URL, dùng lấy customer/company bằng `crm.company.*`, scope `crm` |
| `bitrix_responsible_webhook_url` | Password | Bitrix Responsible Inbound Webhook URL, dùng resolve `ASSIGNED_BY_ID` bằng `user.get`, scope `user_basic` |
| `bitrix_portal_url` | Data | Optional, dùng tạo link mở Bitrix CRM |
| `bitrix_timeout_seconds` | Int | Timeout cấu hình vận hành |
| `bitrix_refresh_ttl_minutes` | Int | TTL cache hồ sơ |
| `bitrix_company_field_map_json` | Code / JSON | Map field Bitrix sang key trả về UI |
| `bitrix_enum_fields_json` | Code / JSON | Danh sách field enum cần resolve label |

Client Script và HD Form Script không được chứa token. Server Script đọc webhook bằng:

```python
settings = frappe.get_doc("Helpdesk Integrations Settings")
customer_webhook_url = settings.get_password("bitrix_webhook_url")
responsible_webhook_url = settings.get_password("bitrix_responsible_webhook_url")
```

---

## 5. Server Script: API trung gian gọi Bitrix

### 5.1 Tạo Server Script

Vào  **Server Script List → New** :

* **Script Type** : `API`
* **Script name** : `Profile - Bitrix Customer API`
* **API Method** : `haravan_bitrix_customer_profile`
* **Allow Guest** : `No` (yêu cầu đăng nhập Frappe)
* **Nguồn cấu hình** : `Helpdesk Integrations Settings`

Luồng hiện tại:

1. Nhận `ticket` và optional `refresh`.
2. Kiểm tra quyền đọc `HD Ticket`.
3. Tạo danh sách ứng viên Company ID từ `HD Ticket.custom_haravan_profile_orgid`, `HD Ticket.custom_orgid`, `HD Ticket.custom_org_id`, `HD Customer.custom_haravan_orgid`, và phần số đầu trong tên `HD Customer` nếu có.
4. Với từng ứng viên, gọi `crm.company.list` filter `UF_CRM_COMPANY_ID`. `ID` của Bitrix chỉ là internal id để mở link `/crm/company/details/{ID}/`.
5. Nếu company có `ASSIGNED_BY_ID`, gọi tiếp webhook responsible bằng method `user.get` với `ID = ASSIGNED_BY_ID`.
6. Nếu user trả về `ACTIVE = true`, cập nhật `EMAIL` vào `HD Ticket.custom_responsible`; nếu inactive/missing/thiếu email thì chỉ trả trạng thái trong response, không ghi field.
7. Nếu không match theo Company ID, fallback qua Contact email/phone và HD Customer domain.
8. Trả response chuẩn `{"success": bool, "data": {}, "message": str}` với `data.bitrix.company` đã normalize theo `bitrix_company_field_map_json` và `data.bitrix.responsible` nếu có.

Ví dụ `bitrix_company_field_map_json` mặc định:

```json
{
  "ID": "bitrix_id",
  "TITLE": "title_full",
  "UF_CRM_STORENAME": "company_name",
  "UF_CRM_COMPANY_ID": "company_id",
  "UF_CRM_CURRENT_HSI_SEGMENT": "current_hsi_segment",
  "UF_CRM_CURRENT_HSI_DETAIL": "current_hsi_detail",
  "UF_CRM_LAST_HSI_SEGMENT": "last_hsi_segment",
  "UF_CRM_LAST_HSI_DETAIL": "last_hsi_detail",
  "UF_CRM_CURRENT_SHOPPLAN": "current_shopplan",
  "UF_CRM_DATE_CREATED_SHOP": "shop_created_date",
  "UF_CRM_FIRST_PAID_DATE": "first_shopplan_date",
  "UF_CRM_DATE_SIGNED_CURRENT_SHOPPLAN": "current_shopplan_date",
  "UF_CRM_DATE_EXPIRED_SHOPPLAN": "shopplan_expiry",
  "UF_CRM_SHOP_OWNER_NAME": "owner_name",
  "UF_CRM_SHOP_OWNER_EMAIL": "owner_email",
  "UF_CRM_SHOP_OWNER_PHONE_NUMBER": "owner_phone",
  "UF_CRM_HARAVAN_MEMBERSHIP": "membership",
  "ASSIGNED_BY_ID": "assigned_by_id"
}
```

### 5.2 Ghi chú transform

Các field HSI/Shopplan trong mapping hiện tại là string, không cần resolve enum. Ngày Bitrix trả dạng ISO với timezone `+03:00`, UI chỉ hiển thị ngày `dd/MM/yyyy`. Các giá trị HSI detail kiểu `"0E-7"` được format thành `"0"`.

Production Server Script đang giữ helper inline để normalize payload. Nếu logic Bitrix tiếp tục lớn hơn, nên chuyển phần client/mapping/cache sang custom app có version control và unit test đầy đủ.

---

## 6. Form Script: Nút và Popup trong HD Ticket

### 6.1 HD Form Script đang dùng ở production

Production dùng **HD Form Script** `Profile - Ticket Customer Button`, không dùng browser token và không gọi Bitrix trực tiếp.

```javascript
function setupForm({ doc, call, $dialog, createToast }) {
  const METHOD = "haravan_bitrix_customer_profile";
  // Action "Customer Profile" gọi:
  // call(METHOD, { ticket: doc.name, refresh: 0 })
  // Action "Refresh Bitrix Profile" gọi:
  // call(METHOD, { ticket: doc.name, refresh: 1 })
}
```

Popup hiển thị các nhóm: `HD Customer`, `Contact`, `Bitrix Company`, `HSI`, `Shopplan`, `Bitrix Contact`.

### 6.2 Link mở Bitrix

Server Script tự build `company.url` / `contact.url` từ `bitrix_portal_url` hoặc suy ra từ `bitrix_webhook_url`.
Browser chỉ render link đã được server trả về, không cần đưa webhook hoặc token vào `frappe.boot`.

---

## 7. Frappe Helpdesk UI (Vue app) – Lưu ý quan trọng

Frappe Helpdesk có nhiều lớp UI:

1. **HD Form Script** trên agent ticket form — production đang dùng `Profile - Ticket Customer Button`.
2. **Frappe Desk truyền thống** (`/app/hd-ticket/...`) — có thể dùng Client Script nếu cần.
3. **Custom app JS** — repo vẫn có `customer_profile_panel.js` làm panel phụ.

Không sửa Frappe core hoặc Helpdesk core cho integration này.

---

## 8. Test toàn bộ luồng

1. **Test Server Script trực tiếp** qua URL:

   ```
   GET /api/method/haravan_bitrix_customer_profile?ticket=61104
   Headers: Authorization: token <api_key>:<api_secret>
   ```

   Kết quả mong đợi: JSON với `message.success` và `message.data.bitrix.status`.
2. **Test trong Desk** :

* Mở 1 HD Ticket có `custom_orgid = 10`.
* Bấm menu **Customer → Customer Profile** hoặc **Refresh Bitrix Profile**.
* Popup phải hiện đúng dữ liệu.

1. **Edge cases cần test** :

* Ticket không có `custom_orgid` → API fallback qua email/phone/domain/Haravan org id hoặc trả `missing_orgid`.
* `custom_orgid` không tồn tại bên Bitrix → popup hiển thị `not_found`.
* Bitrix down/timeout → unfreeze UI, báo lỗi.
* User không có quyền → 403, không gọi được API.

---

## 9. (Khuyến nghị) Chuyển sang Custom App

Khi tích hợp lớn hơn, không nên giữ logic trong Server Script. Tạo app:

```bash
bench new-app bitrix_integration
bench --site your-site install-app bitrix_integration
```

Cấu trúc:

```
bitrix_integration/
├── bitrix_integration/
│   ├── api.py              ← whitelisted methods
│   ├── bitrix_client.py    ← class wrap requests + retry + cache
│   └── field_mapping.py    ← FIELD_MAP, ENUM_FIELDS
└── hooks.py
```

`api.py`:

```python
import frappe
from .bitrix_client import BitrixClient
from .field_mapping import transform_company

@frappe.whitelist()
def get_bitrix_company(orgid):
    if not orgid:
        frappe.throw("Thiếu orgid")
    raw = BitrixClient().get_company(int(orgid))
    return transform_company(raw)
```

Form Script chỉ cần đổi `method`:

```javascript
method: 'bitrix_integration.api.get_bitrix_company'
```

Lợi ích: version control bằng Git, unit test được, có thể chia sẻ giữa nhiều site, tránh giới hạn của Server Script sandbox.

---

## 10. Checklist hoàn thành

* [ ] Đã tạo Inbound Webhook Bitrix với scope `crm`.
* [ ] Đã chạy `crm.company.userfield.list` để lấy đúng tên `UF_CRM_*` thực tế và update `FIELD_MAP`.
* [ ] Đã lưu `bitrix_webhook_url` vào `site_config.json` (KHÔNG hard-code).
* [ ] Đã tạo Server Script API `get_bitrix_company` và test thành công bằng curl.
* [ ] Đã tạo Client Script trên `HD Ticket`, nút hiện đúng khi có `custom_orgid`.
* [ ] Đã test popup hiển thị đầy đủ 11 trường, format ngày đúng locale.
* [ ] Đã xử lý lỗi (timeout, không tìm thấy, không quyền).
* [ ] Đã quyết định phương án Desk vs Vue UI cho agent.

Bạn muốn tôi viết tiếp phần nào: **(a)** code đầy đủ của custom app `bitrix_integration` với retry/cache, **(b)** script khám phá schema tự động (chạy 1 lần in ra mapping table), hay **©** mở rộng popup với tab “Lịch sử Lead/Deal” của công ty đó từ Bitrix?
