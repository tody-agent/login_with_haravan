---
title: Khắc phục sự cố (Troubleshooting)
description: Hướng dẫn xử lý các lỗi thường gặp trong quá trình cài đặt và vận hành tích hợp Haravan.
keywords: lỗi, khắc phục, sự cố, troubleshooting
robots: index, follow
---

# Khắc phục sự cố

## 1. Lỗi: `invalid_request Invalid redirect_uri`

**Nguyên nhân:**
Haravan từ chối yêu cầu đăng nhập trước khi Frappe có cơ hội chạy callback. Lỗi này xuất phát từ việc URL cấu hình trên Partner Dashboard không khớp.

**Cách khắc phục:**
1. Mở domain đang dùng làm primary, ví dụ `https://haravan.help/login`.
2. Chuột phải vào nút `Login with Haravan Account` và chọn "Copy link address" (Sao chép địa chỉ liên kết).
3. Giải mã tham số `redirect_uri` trong liên kết vừa sao chép.
4. Đảm bảo nó khớp hoàn toàn với domain đã cấu hình:
   ```text
   https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan
   ```
5. Đảm bảo bạn đã nhập chính xác URL này vào phần **Redirect URLs** trên Haravan Partner Dashboard.
6. Nếu domain primary vừa đổi, ưu tiên mở login bằng domain mới để hệ thống tự sinh callback. Nếu cần ép domain, cấu hình `haravan_account_login.redirect_uri` trong Site Config; không cần migrate/setup.

## 2. Nút "Login with Haravan" không xuất hiện

**Cách kiểm tra:**
- App đã được cài đặt vào site chưa, hay mới chỉ tải về bench.
- DocType `Social Login Key` có tên `haravan_account` đã tồn tại chưa.
- Tuỳ chọn `Enable Social Login` đã được tích chưa.
- `Client ID` đã có trong `Social Login Key` hoặc Site Config chưa.
- Diagnostic có báo `has_client_secret: true` và `client_secret_source: site_config` chưa.
- Base URL của Provider phải là `https://accounts.haravan.com`.
- Thử xoá bộ nhớ đệm (clear site cache) sau khi chỉnh sửa Social Login Key.

## 3. Frappe Cloud Báo lỗi không thể cài đặt App

**Cách kiểm tra:**
- `pyproject.toml` và `setup.py` phải chứa thuộc tính `name = "login_with_haravan"`.
- Các file `hooks.py` và `patches.txt` phải nằm trong thư mục `login_with_haravan/`.
- Không được có thư mục `tests/` ngoài cùng (chỉ ở trong `login_with_haravan/tests/`).

## 4. Không tạo được `Haravan Account Link`

Kiểm tra Frappe Error Log xem có các cảnh báo sau:
```text
Haravan social login failed
Haravan Account Link persistence failed
```

**Nguyên nhân có thể:**
- Thông tin người dùng (userinfo) trả về từ Haravan không có `email` hoặc `orgid`.
- User này đã bị vô hiệu hoá trên Frappe.
- Tính năng tự động đăng ký (Sign ups) bị tắt trên Social Login Key.

## 5. Bị lỗi `417: Uncaught Exception` sau khi gọi callback

Kiểm tra Error Log gần nhất với tiêu đề: `Haravan social login failed`.

Bên trong log sẽ cung cấp trường `stage` mô tả giai đoạn xảy ra lỗi:
```text
get_info_via_oauth
normalize_haravan_profile
login_oauth_user
```
Bạn cũng có thể thử chạy hàm sau trong Desk (với quyền System Manager) để kiểm tra tình trạng kết nối:
```text
login_with_haravan.diagnostics.get_haravan_login_status
```

Diagnostic chỉ trả trạng thái masked như `has_client_secret` và `client_secret_source`;
không trả plaintext Client Secret, API token, hoặc webhook secret.

## 6. Người dùng bị chuyển hướng về `/desk` thay vì trang Portal

**Luồng hoạt động mong muốn:**
```text
/helpdesk/my-tickets/new
  -> /login?redirect-to=/helpdesk/my-tickets/new
  -> Login with Haravan Account
  -> /helpdesk/my-tickets/new
```

Ứng dụng có nhúng script `/assets/login_with_haravan/js/haravan_login_redirect.js` trên website. Nó lưu `redirect-to` vào cookie và ghi đè `state.redirect_to` trước khi điều hướng sang Haravan. Nếu bạn bị văng về `/desk`, có thể luồng chặn cookie bị lỗi hoặc session expired.

Trong trường hợp không tìm thấy đường dẫn hợp lệ, callback sẽ dự phòng chuyển về `/helpdesk/my-tickets`.
