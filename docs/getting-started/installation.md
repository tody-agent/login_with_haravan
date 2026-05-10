# Cài đặt & Thiết lập

## Yêu cầu hệ thống

- **Frappe Framework** v15+
- **Frappe Helpdesk** (bản chính thức từ Frappe)
- **Python** 3.10+
- **MariaDB** 10.6+
- **Frappe Cloud** hoặc Bench tự host

## Cài đặt trên Frappe Cloud

### Bước 1: Thêm app vào Frappe Cloud

1. Đăng nhập [Frappe Cloud Dashboard](https://frappecloud.com/dashboard)
2. Vào **Apps** → **Add App**
3. Nhập repository: `https://github.com/tody-agent/login_with_haravan`
4. Branch: `main`

### Bước 2: Cài app lên site

1. Vào **Sites** → chọn site cần cài
2. **Install App** → chọn `login_with_haravan`
3. Chờ app cài đặt hoàn tất

### Bước 3: Chạy setup tự động

App sẽ tự động chạy `after_install` hook để:
- Tạo `Social Login Key` cho Haravan
- Tạo DocType `Haravan Account Link`
- Cấu hình OAuth provider

## Cài đặt trên Bench (tự host)

```bash
# Từ thư mục bench
bench get-app https://github.com/tody-agent/login_with_haravan.git
bench --site your-site.local install-app login_with_haravan
bench --site your-site.local migrate
bench restart
```

## Xác minh cài đặt

```bash
# Kiểm tra app đã cài
bench --site your-site.local list-apps

# Kiểm tra compile
python3 -m compileall -q login_with_haravan

# Chạy test
PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v
```

## Cấu trúc package bắt buộc

Để Frappe Cloud nhận diện đúng, app **phải** có các file sau:

```
login_with_haravan/
├── hooks.py           # Required
├── modules.txt        # Required
├── patches.txt        # Required
├── __init__.py
├── login_with_haravan/
│   └── doctype/       # DocType schemas
├── engines/           # Business logic
├── oauth.py           # OAuth callback
├── setup/
│   └── install.py     # After-install setup
└── tests/             # Tests (PHẢI trong package, không ở root)
```

::: warning Lưu ý quan trọng
- **Package name phải là** `login_with_haravan` (underscore), KHÔNG phải `login-with-haravan` (hyphen)
- **Tests phải nằm trong** `login_with_haravan/tests/`, không phải root `tests/`
- Frappe Cloud sẽ báo lỗi `imported module not found` nếu tên sai
:::

## Bước tiếp theo

Sau khi cài đặt thành công:
1. [Cấu hình OAuth Haravan](/getting-started/oauth-setup)
2. [Thiết lập Site Config](/getting-started/site-config)
3. [Triển khai production](/getting-started/deployment)
