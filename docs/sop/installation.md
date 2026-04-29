---
title: Cài đặt và Thiết lập
description: Hướng dẫn SOP từng bước để cài đặt và thiết lập ứng dụng
keywords: sop, installation, setup
robots: index, follow
---

# 📋 SOP: Cài đặt và Thiết lập

:::info Tóm tắt
Quy trình chuẩn để cài đặt ứng dụng trên môi trường local và cấu hình liên kết với Haravan Partner Dashboard.
:::

## 1. Cài đặt Local

Thực thi tuần tự các lệnh sau trong thư mục `frappe-bench`:

```bash
# 1. Symlink app vào bench
ln -sfn /Volumes/Data/Haravan/login_with_haravan apps/login_with_haravan

# 2. Cài đặt Python dependencies
./env/bin/pip install -e apps/login_with_haravan

# 3. Cài app vào site
bench --site boxme.localhost install-app login_with_haravan

# 4. Cấu hình Credentials
bench --site boxme.localhost set-config haravan_login '{"client_id":"YOUR_ID","client_secret":"YOUR_SECRET"}'

# 5. Khởi tạo Social Login Key
bench --site boxme.localhost execute login_with_haravan.setup.install.configure_haravan_social_login

# 6. Xóa cache
bench --site boxme.localhost clear-cache
```

## 2. Cấu hình Haravan Partner App

<details>
<summary>Xem chi tiết các bước trên Haravan Dashboard</summary>

1. Đăng nhập vào Haravan Partner Dashboard.
2. Chọn **Apps** -> Ứng dụng Public / Custom.
3. Trong phần **Redirect URLs**, điền:
   `https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan`
4. Lấy Client ID và Client Secret cập nhật vào Frappe.
</details>

## 3. Troubleshoot nhanh
Nếu cài đặt thất bại do thiếu module, kiểm tra lại `pyproject.toml` đảm bảo `name = "login_with_haravan"`.
