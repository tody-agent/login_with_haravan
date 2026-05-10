---
title: Khắc phục sự cố
description: Hướng dẫn xử lý các lỗi thường gặp khi cài đặt và vận hành tích hợp Haravan.
keywords: lỗi, khắc phục, sự cố, troubleshooting
robots: index, follow
---

# 🔧 Khắc phục sự cố

## 1. Lỗi `invalid_request Invalid redirect_uri`

**Nguyên nhân:** Haravan từ chối yêu cầu đăng nhập **trước khi** Frappe có cơ hội chạy callback. Lỗi này do URL cấu hình trên Partner Dashboard không khớp với URL mà Frappe gửi đi.

**Cách khắc phục:**

1. Mở domain đang dùng làm primary, ví dụ `https://haravan.help/login`.
2. Chuột phải vào nút **Login With Haravan** → **Sao chép địa chỉ liên kết**.
3. Giải mã tham số `redirect_uri` trong liên kết vừa sao chép.
4. Đảm bảo nó khớp **hoàn toàn** với URL đã đăng ký:
   ```text
   https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan
   ```
5. Kiểm tra URL trên phần **Redirect URLs** trong Haravan Partner Dashboard.
6. Nếu domain vừa đổi: ưu tiên mở login bằng domain mới để hệ thống tự sinh callback. Nếu cần ép domain, cấu hình `haravan_account_login.redirect_uri` trong Site Config — không cần migrate.

## 2. Nút "Login With Haravan" không xuất hiện

**Danh sách kiểm tra:**

- [ ] App đã được cài vào site chưa? (Hay mới chỉ tải về bench)
- [ ] DocType `Social Login Key` với tên `haravan_account` đã tồn tại chưa?
- [ ] Tuỳ chọn **Enable Social Login** đã bật chưa?
- [ ] `Client ID` đã có trong `Social Login Key` hoặc Site Config chưa?
- [ ] Diagnostic có báo `has_client_secret: true` và `client_secret_source: site_config` chưa?
- [ ] Base URL của Provider là `https://accounts.haravan.com` chưa?
- [ ] Đã xoá bộ nhớ đệm (clear site cache) sau khi chỉnh sửa Social Login Key chưa?

## 3. Frappe Cloud báo lỗi không thể cài đặt App

**Danh sách kiểm tra:**

- [ ] `pyproject.toml` và `setup.py` chứa `name = "login_with_haravan"` (dấu gạch dưới, không phải gạch ngang).
- [ ] Các file `hooks.py` và `patches.txt` nằm trong thư mục `login_with_haravan/`.
- [ ] Không có thư mục `tests/` ngoài cùng (chỉ đặt ở `login_with_haravan/tests/`).

## 4. Không tạo được `Haravan Account Link`

Kiểm tra Frappe Error Log với các tiêu đề:
```text
Haravan social login failed
Haravan Account Link persistence failed
```

**Nguyên nhân có thể:**
- Thông tin userinfo từ Haravan không có `email` hoặc `orgid`.
- User bị vô hiệu hoá trên Frappe.
- Tính năng tự động đăng ký (Sign ups) bị tắt trên Social Login Key.

## 5. Lỗi `417: Uncaught Exception` sau khi gọi callback

Kiểm tra Error Log gần nhất với tiêu đề `Haravan social login failed`. Bên trong log có trường `stage` cho biết giai đoạn lỗi:

| Stage | Ý nghĩa |
|-------|---------|
| `get_info_via_oauth` | Lỗi khi đổi code lấy token hoặc gọi userinfo |
| `normalize_haravan_profile` | Lỗi khi chuẩn hóa dữ liệu profile |
| `login_oauth_user` | Lỗi khi đăng nhập user vào Frappe |

Chạy diagnostic (quyền System Manager) để kiểm tra tình trạng kết nối:
```text
login_with_haravan.diagnostics.get_haravan_login_status
```

:::tip Bảo mật
Diagnostic chỉ trả trạng thái masked (`has_client_secret`, `client_secret_source`) — không trả plaintext Client Secret, API token, hay webhook secret.
:::

## 6. Người dùng bị chuyển hướng về `/desk` thay vì Portal

**Luồng mong muốn:**
```text
/helpdesk/my-tickets/new
  → /login?redirect-to=/helpdesk/my-tickets/new
  → Login With Haravan
  → /helpdesk/my-tickets/new
```

Ứng dụng nhúng script `/assets/login_with_haravan/js/haravan_login_redirect.js` trên website. Script lưu `redirect-to` vào cookie và ghi đè `state.redirect_to` trước khi điều hướng sang Haravan. Nếu bị văng về `/desk`, kiểm tra:

- Cookie bị block bởi trình duyệt?
- Session đã hết hạn?
- Luồng chặn cookie bị lỗi?

Trong trường hợp không tìm thấy đường dẫn hợp lệ, callback sẽ dự phòng chuyển về `/helpdesk/my-tickets`.
