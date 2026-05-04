# Site Config Secret Handoff

## Mục tiêu

Tất cả token/secret dùng cho Haravan Desk nên được đặt trong **Frappe Cloud > Site Config**, ngoại trừ Bitrix Customer Profile production hiện đang dùng **Helpdesk Integrations Settings** để Haravan team có UI quản trị token. Settings DocType, Server Script, Client Script, HD Form Script chỉ được giữ cấu hình không nhạy cảm như `enabled`, `model`, `timeout`, `default_project_id`, trừ field `bitrix_webhook_url` dạng `Password`.

Client Script và HD Form Script chạy trên browser nên tuyệt đối không chứa API token, webhook secret, access token, client secret.

## Site Config Keys

Vào Frappe Cloud:

```text
Dashboard > Sites > haravandesk.s.frappe.cloud > Site Config > Add Config > Custom Key
```

Thêm các key sau nếu tính năng tương ứng đang dùng:

| Nhóm | Key | Ghi chú |
| --- | --- | --- |
| Haravan OAuth | `haravan_account_login` | JSON: `{"client_id":"...","client_secret":"..."}`. Có thể thêm `redirect_uri` nếu cần ép domain |
| Haravan OAuth domain | `haravan_public_base_url` | Optional legacy/helper fallback. Ưu tiên dùng exact `haravan_account_login.redirect_uri` nếu cần override không migrate |
| Haravan OAuth fallback | `haravan_client_id`, `haravan_client_secret` | Chỉ dùng nếu Frappe Cloud không lưu được JSON object |
| AI Gemini | `gemini_api_key`, `gemini_model` | `gemini_model` không secret nhưng để cùng chỗ cho dễ vận hành |
| AI OpenRouter | `openrouter_api_key` | Dùng cho workflow toolbar nếu chọn OpenRouter |
| Bitrix | `bitrix_webhook_url`, `bitrix_responsible_webhook_url`, `bitrix_portal_url`, `bitrix_enabled`, `bitrix_timeout_seconds`, `bitrix_refresh_ttl_minutes`, `bitrix_company_field_map_json`, `bitrix_enum_fields_json` | Production hiện lưu trong `Helpdesk Integrations Settings`; webhook là `Password` và chỉ đọc server-side. `bitrix_webhook_url` dùng lấy customer/company, `bitrix_responsible_webhook_url` dùng `user.get` lấy người phụ trách |
| GitLab | `gitlab_token`, `gitlab_base_url` | Nếu bật GitLab popup/link issue |

Không paste secret vào chat, ticket, Git, hoặc file markdown. Tài liệu này chỉ ghi tên key.

## Code/Script Đã Chuẩn Hóa

Trong app `login_with_haravan`:

- Haravan OAuth callback đọc `haravan_account_login` trước, fallback `haravan_login`/flat keys, rồi mới fallback `Social Login Key`.
- Haravan OAuth mặc định tự sinh redirect URI theo request/current domain vì Social Login Key giữ callback path tương đối.
- Nếu cần ép domain không migrate/setup, đặt exact `haravan_account_login.redirect_uri`; Frappe core đọc key này ở runtime.
- Setup method không copy `client_secret` từ Site Config ngược vào `Social Login Key`.
- Diagnostic `login_with_haravan.diagnostics.get_haravan_login_status` trả masked status: `has_client_secret`, `client_secret_source`, `helpdesk_secret_status`.

Trong script/handoff liên quan:

- AI Server Scripts đọc `gemini_api_key`, `gemini_model`, `openrouter_api_key` từ Site Config trước; Settings DocType chỉ là fallback migration.
- GitLab backend đọc `gitlab_token`, `gitlab_base_url` từ Site Config trước; `GitLab Settings.access_token` chỉ là fallback migration.
- Bitrix Server Script production đọc `bitrix_webhook_url` và `bitrix_responsible_webhook_url` từ `Helpdesk Integrations Settings.get_password()`; HD Form Script chỉ gọi `haravan_bitrix_customer_profile`.
- Client Script / HD Form Script chỉ gọi server API, không lưu token.

## Pattern Cho Server Script Safe Exec

Dùng pattern này trong mọi Server Script cần secret:

```python
def read_site_conf(key, default=None):
    try:
        return frappe.local.conf[key]
    except Exception:
        return default


def read_password_if_available(doc, fieldname):
    try:
        value = doc.get_password(fieldname)
        if value:
            return value
    except Exception:
        pass
    try:
        return doc.get(fieldname)
    except Exception:
        return None
```

Quy tắc:

- Gọi `read_site_conf("...")` trước.
- Chỉ nếu thiếu thì fallback `get_password()` từ Settings DocType cũ.
- Không trả secret qua `frappe.response`.
- Không log secret. Error log chỉ ghi thiếu key hoặc source.

## Pattern Cho Custom App Python

Trong custom app, dùng helper:

```python
from login_with_haravan.engines.site_config import get_site_or_legacy_secret

token_info = get_site_or_legacy_secret(
    "bitrix_access_token",
    legacy_doc=settings,
    legacy_field="access_token",
)
token = token_info["value"]
source = token_info["source"]
```

Chỉ dùng `source` cho diagnostic/log. Không log `token`.

## Migration Checklist

1. Backup site trước khi đổi cấu hình.
2. Thêm toàn bộ Site Config keys cần dùng.
3. Deploy app/code mới.
4. Clear cache site.
5. Chạy diagnostic masked:

```text
login_with_haravan.diagnostics.get_haravan_login_status
```

6. Xác nhận:

```text
has_client_secret = true
client_secret_source = site_config
helpdesk_secret_status.<nhóm>.<key>.configured = true
```

7. Smoke test:

- Haravan login thành công và tạo/cập nhật `Haravan Account Link`.
- AI Summary / AI Reply gọi được model đang cấu hình.
- Bitrix Customer Profile mở được trên ticket test nếu đang bật.
- GitLab popup tạo/search/link issue được nếu đang bật.

8. Sau khi smoke test pass, xóa giá trị secret trong Settings DocType cũ:

- `Social Login Key.client_secret`
- `HD Bitrix Settings` token/webhook/client secret fields
- `HD AI Settings` hoặc `Boxme AI Integration Settings` API key fields
- `GitLab Settings.access_token`

Giữ lại non-secret config như `enabled`, `model`, `timeout`, `default_project_id`.

## Bàn Giao Cho Haravan Team

Haravan team cần giữ:

- Danh sách owner được quyền xem/sửa Site Config.
- Nơi tạo/rotate từng token: Haravan Partner App, Gemini/OpenRouter, Bitrix, GitLab.
- Lịch rotate token định kỳ hoặc sau nhân sự thay đổi.
- Checklist smoke test sau mỗi lần rotate.
- Quy định: Client Script / HD Form Script không bao giờ chứa token.

Khi cần thêm integration mới, đặt key theo prefix rõ ràng:

```text
<integration>_<purpose>
```

Ví dụ:

```text
zalo_access_token
zalo_webhook_secret
```

Sau đó thêm key vào diagnostic masked trước khi go-live.
