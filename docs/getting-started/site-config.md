# Cấu hình Site Config

## Tổng quan

Tất cả secret và cấu hình nhạy cảm được lưu trong **Frappe Cloud Site Config** (hoặc `site_config.json` với bench tự host).

::: danger QUY TẮC BẢO MẬT
- **KHÔNG BAO GIỜ** lưu secret trong code, Git, docs, hoặc browser-side script
- **KHÔNG BAO GIỜ** dùng `frappe.conf` trực tiếp trong client script
- Chỉ expose trạng thái (đã cấu hình/chưa) qua diagnostics API
- Tất cả truy cập secret phải qua server-side code
:::

## Các key cần cấu hình

### OAuth Haravan (bắt buộc)

```json
{
  "haravan_account_login": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
  }
}
```

| Key | Mô tả | Bắt buộc |
|---|---|---|
| `client_id` | App API Key từ Haravan Partner Dashboard | ✅ |
| `client_secret` | App API Secret từ Haravan Partner Dashboard | ✅ |
| `redirect_uri` | Override redirect URL (mặc định: tự phát hiện) | ❌ |
| `base_url` | Override base URL Haravan (mặc định: `https://accounts.haravan.com`) | ❌ |

### Bitrix CRM (bắt buộc cho enrichment)

```json
{
  "bitrix_webhook_url": "https://YOUR_DOMAIN.bitrix24.vn/rest/USER_ID/WEBHOOK_TOKEN"
}
```

| Key | Mô tả | Bắt buộc |
|---|---|---|
| `bitrix_webhook_url` | Incoming webhook URL của Bitrix24 | ✅ (cho enrichment) |

### GitLab Integration (tùy chọn)

```json
{
  "gitlab_token": "YOUR_GITLAB_TOKEN",
  "gitlab_project_id": "PROJECT_ID",
  "gitlab_base_url": "https://gitlab.com"
}
```

### AI Features (tùy chọn)

```json
{
  "gemini_api_key": "YOUR_GEMINI_API_KEY"
}
```

## Cách set trên Frappe Cloud

1. Đăng nhập [Frappe Cloud Dashboard](https://frappecloud.com/dashboard)
2. Vào **Sites** → chọn site
3. **Site Config** → **Edit**
4. Thêm key/value theo format JSON ở trên
5. **Save** → site tự restart

## Cách set trên Bench (tự host)

```bash
# Set từng key
bench --site your-site.local set-config haravan_account_login '{"client_id":"...","client_secret":"..."}' --as-dict

# Hoặc edit trực tiếp
vim sites/your-site.local/site_config.json
bench restart
```

## Kiểm tra trạng thái cấu hình

### API Diagnostics (admin only)

```bash
curl -H "Authorization: token API_KEY:API_SECRET" \
  "https://haravan.help/api/method/login_with_haravan.diagnostics.get_haravan_login_status"
```

Response trả về trạng thái các integration (tất cả secret được **mask**):

```json
{
  "message": {
    "oauth_configured": true,
    "bitrix_configured": true,
    "gitlab_configured": false,
    "client_id": "abc***xyz"
  }
}
```

## Pattern truy cập an toàn trong code

```python
# ✅ ĐÚNG — Server-side, có fallback
webhook_url = frappe.conf.get("bitrix_webhook_url")
if not webhook_url:
    frappe.throw("Bitrix webhook chưa cấu hình trong Site Config")

# ❌ SAI — Hardcode secret
webhook_url = "https://haravan.bitrix24.vn/rest/123/abc123"

# ❌ SAI — Expose ra client
frappe.response["webhook_url"] = webhook_url
```

## Tham chiếu

- [Cấu hình OAuth](/getting-started/oauth-setup) — Thiết lập OAuth ban đầu
- [Khắc phục sự cố](/getting-started/troubleshooting) — Xử lý lỗi cấu hình
