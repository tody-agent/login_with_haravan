---
title: Hanh vi tao User va Multi-org
description: Giai thich de ban giao cho Haravan ve cach Login With Haravan tao User, su dung email va xu ly nguoi dung thuoc nhieu to chuc.
keywords: haravan, user, email, multi org, hd customer, contact, helpdesk
robots: index, follow
---

# Login With Haravan tạo User như thế nào?

:::info Tóm tắt cho Haravan
Khi người dùng đăng nhập bằng **Login With Haravan**, hệ thống dùng email từ Haravan để đăng nhập hoặc tạo tài khoản `User` trên Frappe Helpdesk. Nếu cùng một email thuộc nhiều tổ chức Haravan, hệ thống vẫn giữ **một User duy nhất**, sau đó lưu thêm từng tổ chức vào bảng liên kết riêng.
:::

## 1. Có tạo tài khoản User không?

Có. Sau khi Haravan xác thực thành công, callback của app gọi cơ chế OAuth chuẩn của Frappe để đăng nhập user.

Nếu email đã tồn tại trong Frappe:

- Hệ thống dùng lại `User` đó.
- Không tạo user mới.
- Cập nhật thêm liên kết Haravan nếu đây là tổ chức mới.

Nếu email chưa tồn tại trong Frappe:

- Frappe tạo một `User` mới.
- `User.email` là email Haravan trả về.
- `User.name` thường chính là email đó, ví dụ `owner@minhhaistore.vn`.
- User được tạo dưới dạng `Website User`, phù hợp để dùng portal Helpdesk.
- Password được sinh ngẫu nhiên vì người dùng đăng nhập qua Haravan OAuth, không cần biết mật khẩu Frappe.
- App không gửi welcome email mặc định trong lúc tạo OAuth user.

## 2. Có dùng email không?

Có. Email là định danh chính để Frappe match hoặc tạo `User`.

Haravan phải trả về email trong profile đăng nhập. Nếu thiếu email, hệ thống không thể tạo phiên đăng nhập hợp lệ.

Ví dụ Haravan trả:

```json
{
  "sub": "u_1001",
  "email": "Owner@MinhHaiStore.vn",
  "orgid": "200000376735",
  "orgname": "Minh Hai Store",
  "role": ["owner"]
}
```

App sẽ chuẩn hóa email thành:

```text
owner@minhhaistore.vn
```

Sau đó Frappe dùng email này để tìm hoặc tạo `User`.

## 3. Những dữ liệu nào bắt buộc từ Haravan?

Callback cần tối thiểu ba nhóm thông tin:

| Dữ liệu | Ý nghĩa | Ví dụ |
|---|---|---|
| `sub`, `userid`, `user_id` hoặc `id` | ID người dùng Haravan | `u_1001` |
| `email` hoặc `email_address` | Email dùng để tạo/match Frappe User | `owner@minhhaistore.vn` |
| `orgid`, `org_id` hoặc `organization_id` | ID tổ chức/cửa hàng Haravan | `200000376735` |

Nếu thiếu một trong ba nhóm này, hệ thống sẽ dừng login và ghi log lỗi để debug.

## 4. Hệ thống lưu thêm gì sau khi login?

Sau khi Frappe login thành công, app lưu thêm dữ liệu Helpdesk:

| Nơi lưu | Mục đích |
|---|---|
| `User` | Tài khoản đăng nhập Frappe Helpdesk, định danh bằng email |
| `HD Customer` | Đại diện cho một tổ chức/cửa hàng Haravan |
| `Contact` | Hồ sơ liên hệ theo email để Helpdesk gắn ticket |
| `Haravan Account Link` | Bảng mapping giữa User Frappe, Haravan user ID, Haravan org ID và HD Customer |

Tên `HD Customer` được tạo theo mẫu:

```text
{Haravan Org Name} - {Haravan Org ID}
```

Ví dụ:

```text
Minh Hai Store - 200000376735
```

Bảng `Haravan Account Link` dùng key theo mẫu:

```text
HARAVAN-{orgid}-{userid}
```

Ví dụ:

```text
HARAVAN-200000376735-u_1001
```

## 5. Nếu một user thuộc nhiều org Haravan thì sao?

Nếu cùng một người dùng Haravan hoặc cùng một email đăng nhập vào nhiều tổ chức khác nhau, hệ thống xử lý như sau:

- Vẫn chỉ có **một Frappe User** theo email.
- Mỗi tổ chức Haravan tạo một `HD Customer` riêng.
- Mỗi cặp `orgid + userid` tạo một `Haravan Account Link` riêng.
- Khi tạo ticket, frontend có thể hiển thị dropdown để người dùng chọn tổ chức cần gửi ticket.

Ví dụ cùng email `owner@example.com` thuộc hai org:

| Lần login | Haravan user ID | Haravan org ID | Frappe User | HD Customer | Haravan Account Link |
|---|---|---|---|---|---|
| 1 | `u_1001` | `org_aaa` | `owner@example.com` | `Shop A - org_aaa` | `HARAVAN-org_aaa-u_1001` |
| 2 | `u_1001` | `org_bbb` | `owner@example.com` | `Shop B - org_bbb` | `HARAVAN-org_bbb-u_1001` |

Kết quả: user đăng nhập bằng cùng email, nhưng Helpdesk biết người này có quyền thao tác với nhiều customer/org khác nhau.

## 6. Quyền xem ticket theo role Haravan

App đang phân biệt quyền Helpdesk dựa trên role Haravan:

| Role Haravan | Cách link Contact | Hành vi trên Helpdesk |
|---|---|---|
| `owner` | Link `Contact` với `HD Customer` | Có thể thấy ticket của tổ chức |
| `admin` | Link `Contact` với `HD Customer` | Có thể thấy ticket của tổ chức |
| `staff` hoặc role khác | Không link `Contact` với `HD Customer` | Chỉ thấy ticket do chính user tạo |

Điểm này giúp tránh việc nhân viên thường thấy toàn bộ ticket của cửa hàng nếu Haravan không cấp vai trò quản lý.

## 7. Các case ví dụ

### Case A: User mới, lần đầu login

Haravan trả:

```json
{
  "sub": "u_2001",
  "email": "new-owner@example.com",
  "orgid": "org_001",
  "orgname": "New Shop",
  "role": ["owner"]
}
```

Kết quả:

- Tạo `User`: `new-owner@example.com`.
- Tạo `HD Customer`: `New Shop - org_001`.
- Tạo hoặc cập nhật `Contact` theo email.
- Vì role là `owner`, `Contact` được link với `HD Customer`.
- Tạo `Haravan Account Link`: `HARAVAN-org_001-u_2001`.

### Case B: User đã có trong Frappe

Nếu `owner@example.com` đã là `User` trong Frappe, khi login bằng Haravan với cùng email:

- Không tạo user mới.
- Đăng nhập vào user hiện có.
- Lưu thêm Haravan user ID, org ID và HD Customer vào `Haravan Account Link`.

### Case C: Cùng email, nhiều org

User `owner@example.com` login lần lượt vào `Shop A` và `Shop B`.

Kết quả:

- Frappe vẫn có một `User`: `owner@example.com`.
- Có hai `HD Customer`: `Shop A - org_a` và `Shop B - org_b`.
- Có hai dòng `Haravan Account Link`.
- Khi tạo ticket, user có thể chọn đúng tổ chức trong dropdown.

### Case D: Staff đăng nhập

Haravan trả role:

```json
{
  "sub": "u_3001",
  "email": "staff@example.com",
  "orgid": "org_001",
  "orgname": "New Shop",
  "role": ["staff"]
}
```

Kết quả:

- User vẫn được login/tạo bình thường.
- `HD Customer` và `Haravan Account Link` vẫn được tạo/cập nhật.
- `Contact` không được link vào `HD Customer`.
- Staff chỉ thấy ticket do chính họ tạo, không thấy toàn bộ ticket của org.

### Case E: Haravan không trả email

Nếu profile thiếu email:

```json
{
  "sub": "u_4001",
  "orgid": "org_001",
  "orgname": "New Shop"
}
```

Kết quả:

- Login bị dừng.
- Không tạo `User`.
- Hệ thống ghi log lỗi thiếu `email`.

## 8. Kết luận bàn giao

Thiết kế hiện tại phù hợp với mô hình Helpdesk:

- Email là tài khoản đăng nhập chính.
- Haravan org là customer/tổ chức trong Helpdesk.
- Multi-org được xử lý bằng bảng mapping, không nhân bản user.
- Role `owner/admin` có quyền theo tổ chức; `staff` bị giới hạn theo ticket cá nhân.

Khi Haravan kiểm thử, cần đảm bảo OAuth profile trả đủ `email`, `sub/userid`, `orgid`, `orgname` và `role` để hệ thống phân quyền đúng.
