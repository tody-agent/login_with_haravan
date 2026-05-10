# Cấu hình OAuth Haravan

## Tổng quan

Haravan Helpdesk sử dụng OAuth 2.0 Authorization Code flow để cho phép merchant Haravan đăng nhập vào portal hỗ trợ bằng tài khoản Haravan của họ.

## Bước 1: Đăng ký App trên Haravan Partner Dashboard

1. Đăng nhập [Haravan Partner Dashboard](https://partners.haravan.com)
2. Tạo **App** mới hoặc chọn app đã có
3. Cấu hình callback URL:

```
https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan
```

4. Lấy:
   - **Client ID** (App API Key)
   - **Client Secret** (App API Secret)

::: danger BẢO MẬT
Client Secret **TUYỆT ĐỐI KHÔNG** được commit vào Git, lưu trong docs, hoặc hiển thị trên browser.
Chỉ lưu trong **Frappe Cloud Site Config**.
:::

## Bước 2: Cấu hình Social Login Key

Trên site Frappe Helpdesk:

1. Vào **Setup > Social Login Key**
2. Tạo hoặc chỉnh sửa key `haravan_account`:

| Field | Giá trị |
|---|---|
| Provider Name | `haravan_account` |
| Client ID | _(từ Partner Dashboard)_ |
| Client Secret | _(từ Partner Dashboard)_ |
| Base URL | `https://accounts.haravan.com` |
| Authorize URL | `/connect/authorize` |
| Access Token URL | `/connect/token` |
| Redirect URL | `/api/method/login_with_haravan.oauth.login_via_haravan` |
| API Endpoint | `https://accounts.haravan.com/connect/userinfo` |

::: tip Redirect URL
Để mặc định là **relative path** (`/api/method/...`) để Frappe tự dùng domain của request hiện tại.
Nếu cần override cứng, set trong Site Config key `haravan_account_login.redirect_uri`.
:::

## Bước 3: Kiểm tra trạng thái

Gọi API diagnostics (chỉ admin):

```
GET /api/method/login_with_haravan.diagnostics.get_haravan_login_status
```

Response sẽ trả về trạng thái OAuth đã cấu hình (mọi secret được mask).

## Bước 4: Test đăng nhập

1. Mở trình duyệt incognito
2. Truy cập `https://haravan.help`
3. Click **"Đăng nhập bằng Haravan"**
4. Đăng nhập bằng tài khoản Haravan merchant
5. Xác nhận redirect về portal thành công

## Lỗi thường gặp

### `invalid_request Invalid redirect_uri`

**Nguyên nhân:** URL callback đăng ký trên Haravan Partner Dashboard không khớp.

**Fix:** Đảm bảo redirect URL trên Haravan Partner Dashboard là chính xác:
```
https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan
```

### `imported module login-with-haravan not found`

**Nguyên nhân:** Package name dùng hyphen thay vì underscore.

**Fix:** Đảm bảo `pyproject.toml` và `setup.py` đều dùng:
```
name = "login_with_haravan"
```

### Không thấy nút "Đăng nhập bằng Haravan"

**Kiểm tra:**
1. Social Login Key đã được tạo và enable
2. Site Config key `haravan_account_login` có `client_id` hợp lệ
3. Custom app đã cài đặt thành công trên site

## Tham chiếu

- [Chi tiết luồng OAuth](/architecture/oauth-flow)
- [Site Config keys](/getting-started/site-config)
- [Khắc phục sự cố](/getting-started/troubleshooting)
