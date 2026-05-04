---
title: Bắt đầu & Cấu hình
description: Hướng dẫn cấu hình OAuth cho Frappe Site, Social Login Key, và Haravan Partner Dashboard.
keywords: cấu hình, cài đặt, oauth, social login, haravan
robots: index, follow
---

# ⚙️ Bắt đầu & Cấu hình

:::info Mục tiêu
Hướng dẫn từng bước thiết lập kết nối OAuth giữa Frappe Helpdesk và Haravan Account. Sau khi hoàn thành, nút "Login with Haravan Account" sẽ xuất hiện trên trang đăng nhập.
:::

## 1. Cấu hình Frappe Site Config

Cung cấp Client ID và Secret cho Frappe Site. Truy cập **Frappe Cloud → Site → Site Config → Add Config → Custom Key**.

- **Tên config:**
  ```text
  haravan_account_login
  ```
- **Giá trị:**
  ```json
  {
    "client_id": "HARAVAN_CLIENT_ID",
    "client_secret": "HARAVAN_CLIENT_SECRET"
  }
  ```

:::tip Quy ước ưu tiên key
`haravan_account_login` là key ưu tiên vì Frappe core đọc theo quy ước `{provider}_login` với provider là `haravan_account`. App vẫn hỗ trợ `haravan_login` và hai key rời `haravan_client_id`/`haravan_client_secret` để tương thích ngược — nhưng **không nên dùng** cho cấu hình mới.
:::

### Tuỳ chọn: Cố định domain callback

Mặc định, app tự dùng domain hiện tại của request vì `Social Login Key.redirect_url` được giữ dạng path tương đối:

```text
/api/method/login_with_haravan.oauth.login_via_haravan
```

Nếu cần cố định domain (không muốn chạy migrate/setup), thêm `redirect_uri` vào key `haravan_account_login`:

```json
{
  "client_id": "HARAVAN_CLIENT_ID",
  "client_secret": "HARAVAN_CLIENT_SECRET",
  "redirect_uri": "https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan"
}
```

Khi đổi primary domain, cách tốt nhất là mở login bằng domain mới để hệ thống tự sinh callback. Nếu muốn ép domain, chỉ cần đổi `redirect_uri` trong Site Config và cập nhật URL tương ứng trong Haravan Partner Dashboard.

### Các key cấu hình khác

Các token/secret khác của Helpdesk cũng nên đặt ở Site Config:

| Key | Mô tả |
|-----|-------|
| `gemini_api_key` | API key cho Gemini AI |
| `gemini_model` | Model Gemini sử dụng |
| `openrouter_api_key` | API key OpenRouter |
| `bitrix_webhook_url` | Webhook URL Bitrix lấy customer/company (`crm`) |
| `bitrix_responsible_webhook_url` | Webhook URL Bitrix lấy người phụ trách (`user.get`, scope `user_basic`) |
| `bitrix_access_token` | Access token Bitrix |
| `bitrix_enabled` | Bật/tắt tích hợp Bitrix |
| `bitrix_timeout_seconds` | Timeout gọi Bitrix |
| `bitrix_refresh_ttl_minutes` | TTL refresh token Bitrix |

:::tip Cấu hình Bitrix trong Helpdesk Integrations Settings
Trên production `https://haravandesk.s.frappe.cloud/desk/helpdesk-integrations-settings`, tab **Bitrix** cần có 2 webhook riêng:

- **Bitrix Customer Inbound Webhook URL**: lấy customer/company bằng `crm.company.*`, scope Bitrix `crm`.
- **Bitrix Responsible Inbound Webhook URL**: lấy người phụ trách bằng `user.get?ID={ASSIGNED_BY_ID}`, scope Bitrix `user_basic`.

Nếu màn hình chỉ có field **Bitrix Webhook URL**, chạy `npm run patch:bitrix-settings` với `HARAVAN_HELP_SITE`, `HARAVAN_HELP_API_KEY`, `HARAVAN_HELP_API_SECRET` để cập nhật metadata form.
:::

## 2. Cấu hình Social Login Key

Đảm bảo DocType `Social Login Key` có cấu hình như sau:

| Trường | Giá trị |
|--------|---------|
| **Social Login Provider** | `Custom` |
| **Provider Name** | `Haravan Account` |
| **Enable Social Login** | ✅ Bật |
| **Client ID** | `HARAVAN_CLIENT_ID` |
| **Client Secret** | Để trống nếu `haravan_account_login` đã có `client_secret` |
| **Base URL** | `https://accounts.haravan.com` |
| **Custom Base URL** | ✅ Bật |
| **Authorize URL** | `/connect/authorize` |
| **Access Token URL** | `/connect/token` |
| **Redirect URL** | `/api/method/login_with_haravan.oauth.login_via_haravan` |
| **API Endpoint** | `/connect/userinfo` |
| **User ID Property** | `sub` |
| **Sign ups** | `Allow` |

**Auth URL Data:**
```json
{
  "response_mode": "query",
  "response_type": "code",
  "scope": "openid profile email org userinfo"
}
```

## 3. Cấu hình Haravan Partner Dashboard

Trên ứng dụng Public / Custom trong Haravan Partner Dashboard, điền chính xác Redirect URL:

```text
https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan
```

:::warning Lưu ý quan trọng
- Client ID và Client Secret ở Site Config phải lấy từ ứng dụng chứa Redirect URL này.
- Không lưu plaintext secret trong Settings DocType sau khi smoke test production đã pass.
- Nếu Haravan trả lỗi `invalid_request Invalid redirect_uri`, xem [Khắc phục sự cố](/guide/troubleshooting#_1-loi-invalid-request-invalid-redirect-uri).
:::
