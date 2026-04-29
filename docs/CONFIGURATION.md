---
title: Cấu hình Haravan (Configuration)
description: Cấu hình OAuth cho Frappe Site và Haravan Partner Dashboard.
keywords: config, oauth, social login
robots: index, follow
---

# Cấu hình Tích hợp

## 1. Frappe Site Config

Bạn cần cung cấp Client ID và Secret cho Frappe Site.
Truy cập **Frappe Cloud > Site > Site Config > Add Config > Custom Key**.

- **Config name**:
  ```text
  haravan_login
  ```
- **Value**:
  ```json
  {
    "client_id": "HARAVAN_CLIENT_ID",
    "client_secret": "HARAVAN_CLIENT_SECRET"
  }
  ```

## 2. Social Login Key

Đảm bảo DocType `Social Login Key` có cấu hình như sau:

- **DocType**: `Social Login Key`
- **Social Login Provider**: `Custom`
- **Provider Name**: `Haravan Account`
- **Enable Social Login**: `Được tích chọn`
- **Client ID**: `HARAVAN_CLIENT_ID`
- **Client Secret**: `HARAVAN_CLIENT_SECRET`
- **Base URL**: `https://accounts.haravan.com`
- **Custom Base URL**: `Được tích chọn`
- **Authorize URL**: `/connect/authorize`
- **Access Token URL**: `/connect/token`
- **Redirect URL**: `/api/method/login_with_haravan.oauth.login_via_haravan`
- **API Endpoint**: `/connect/userinfo`
- **User ID Property**: `sub`
- **Sign ups**: `Allow`

**Auth URL Data**:
```json
{
  "response_mode": "query",
  "response_type": "code",
  "scope": "openid profile email org userinfo"
}
```

## 3. Haravan Partner Dashboard

Trên ứng dụng Public / Custom bên trong Haravan Partner Dashboard, bạn phải điền chính xác đường dẫn Redirect URL:

```text
https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan
```

**Lưu ý**: Client ID và Client Secret ở bước 1 và 2 phải được lấy ra từ ứng dụng chứa Redirect URL này.
