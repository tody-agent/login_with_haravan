---
title: Cấp quyền Helpdesk sau khi Login With Haravan
description: Hướng dẫn bàn giao cho Haravan về cách cấp quyền truy cập Helpdesk Portal và Desk sau khi nhân viên đăng nhập bằng Haravan.
keywords: haravan, helpdesk, desk, role, hd agent, employee access
robots: index, follow
---

# Cấp quyền Helpdesk sau khi Login With Haravan

:::info Mục tiêu
Sau khi nhân viên đăng nhập bằng **Login With Haravan**, Frappe có thể tự tạo hoặc match `User` theo email. Bước tiếp theo là cấp đúng quyền để người đó vào được **Helpdesk Portal** hoặc **Desk**.
:::

## 1. Login With Haravan tạo gì?

Khi OAuth thành công, hệ thống xử lý các bản ghi sau:

| Bản ghi | Mục đích |
|---|---|
| `User` | Tài khoản đăng nhập Frappe, định danh bằng email Haravan |
| `HD Customer` | Tổ chức/cửa hàng Haravan |
| `Contact` | Hồ sơ liên hệ theo email |
| `Haravan Account Link` | Mapping giữa Frappe User, Haravan user ID, Haravan org ID và HD Customer |

Role từ Haravan (`owner`, `admin`, `staff`) chỉ quyết định phạm vi ticket của cửa hàng:

| Haravan role | Quyền ticket portal |
|---|---|
| `owner`, `admin` | Contact được link với `HD Customer`, có thể thấy ticket của tổ chức |
| `staff` hoặc role khác | Không link Contact với `HD Customer`, chỉ thấy ticket do chính user tạo |

Role từ Haravan **không tự động biến user thành nhân viên nội bộ trên Desk**. Nếu cần dùng Desk, phải cấp thêm role/agent trong Frappe Helpdesk.

## 2. Chọn loại quyền cần cấp

| Nhu cầu | Cấp quyền |
|---|---|
| Khách hàng/nhân viên shop chỉ tạo và theo dõi ticket của họ | Giữ dạng Website User/Portal User, không cần cấp Desk |
| Admin/owner của shop cần thấy ticket toàn shop trên portal | Đảm bảo Haravan trả `role: ["admin"]` hoặc `role: ["owner"]` |
| Nhân viên CS/Support của Haravan cần xử lý ticket trong Desk | Cấp quyền Desk và tạo `HD Agent` |
| Quản trị viên hệ thống cần cấu hình app, role, integration | Cấp `System Manager` rất hạn chế |

## 3. Cấp quyền Helpdesk Portal

Portal là màn hình dành cho customer tạo và xem ticket.

Thông thường user login bằng Haravan đã đủ để vào portal nếu site cho phép Website User dùng Helpdesk portal. Kiểm tra:

1. Mở **Desk → User**.
2. Tìm user theo email Haravan.
3. Đảm bảo user đang **Enabled**.
4. Nếu user là khách hàng/shop staff, giữ user ở dạng portal/website user.
5. Không cấp role Desk nếu họ không phải nhân viên support nội bộ.

Với owner/admin của shop:

1. Haravan OAuth phải trả `role` là `owner` hoặc `admin`.
2. Cho user login lại bằng Login With Haravan.
3. Vào **Contact** theo email đó.
4. Kiểm tra bảng **Links** có dòng:

```text
Link Doctype: HD Customer
Link Name: {Tên shop} - {Haravan orgid}
```

Nếu có link này, user có thể thấy ticket thuộc `HD Customer` tương ứng theo cơ chế permission của Helpdesk.

## 4. Cấp quyền Desk cho nhân viên support Haravan

Desk là màn hình nội bộ để agent xử lý ticket. Chỉ cấp cho nhân viên Haravan/support team.

Thao tác thủ công:

1. Mở **Desk → User**.
2. Tìm user theo email đã login bằng Haravan.
3. Tắt cờ **User Type = Website User** nếu site yêu cầu Desk user phải là System User.
4. Cấp các role tối thiểu theo Helpdesk đang cài:

| Role | Khi nào dùng |
|---|---|
| `Desk User` hoặc role tương đương | Cho phép vào Desk |
| `Agent` / `HD Agent` role nếu site có | Cho phép thao tác nghiệp vụ Helpdesk |
| `System Manager` | Chỉ dùng cho người quản trị cấu hình, không cấp đại trà |

5. Mở DocType **HD Agent**.
6. Tạo hoặc kiểm tra agent cho user đó:

```text
User: email nhân viên
Agent Name: tên nhân viên
Enabled: checked
```

7. Gán agent vào group/team nếu Helpdesk đang dùng assignment group.
8. Cho user logout/login lại.
9. Kiểm tra user mở được:

```text
/app
/app/hd-ticket
```

:::warning Không cấp Desk cho customer/shop staff
Nếu user chỉ là nhân viên shop đăng nhập để gửi ticket, không nên cấp Desk hoặc HD Agent. Cấp Desk biến họ thành người dùng nội bộ và có thể làm rộng phạm vi truy cập hơn mong muốn.
:::

## 5. Cấp quyền admin quản trị

Chỉ cấp `System Manager` cho số ít tài khoản vận hành. Role này dùng để:

- Cấu hình `Social Login Key`.
- Chạy setup/migrate config.
- Quản lý role và permission.
- Cấu hình `Helpdesk Integrations Settings`.
- Kiểm tra `Error Log` khi OAuth lỗi.

Không dùng `System Manager` để cấp quyền xử lý ticket hằng ngày.

## 6. Checklist bàn giao cho Haravan

Sau khi một nhân viên login lần đầu:

| Bước | Kiểm tra |
|---|---|
| 1 | `User` tồn tại theo email Haravan |
| 2 | `User` đang Enabled |
| 3 | `Haravan Account Link` có đúng `haravan_orgid`, `haravan_userid`, `haravan_roles` |
| 4 | Nếu là owner/admin shop, `Contact` có link tới `HD Customer` |
| 5 | Nếu là support agent nội bộ, user có role Desk/Agent |
| 6 | Nếu là support agent nội bộ, có bản ghi `HD Agent` |
| 7 | User logout/login lại và test vào đúng màn hình |

## 7. Khi nào cần tự động hóa?

Nếu Haravan muốn nhân viên support nội bộ được cấp quyền Desk tự động sau lần login đầu tiên, nên thêm một whitelist email/domain rõ ràng, ví dụ:

```text
@haravan.com
@seedcom.vn
```

Sau đó mới tự động cấp role Desk và tạo `HD Agent`. Không nên tự động cấp Desk chỉ dựa trên Haravan role `admin`, vì `admin` có thể là admin của một shop/customer, không phải nhân viên support nội bộ của Haravan.

Khuyến nghị an toàn:

| Điều kiện | Hành động tự động |
|---|---|
| Email thuộc domain nội bộ Haravan và nằm trong allowlist | Cấp Desk/Agent, tạo `HD Agent` |
| Email là owner/admin shop nhưng không thuộc allowlist nội bộ | Chỉ cấp quyền portal theo `HD Customer` |
| Email là staff shop | Chỉ cho xem ticket cá nhân |

## 8. Lỗi thường gặp

### User login được nhưng không vào Desk được

Kiểm tra user có role Desk/Agent chưa và có phải System User không. Sau khi đổi role, yêu cầu user logout/login lại.

### User vào portal nhưng không thấy ticket của shop

Kiểm tra Haravan trả `role` là `owner` hoặc `admin`, sau đó kiểm tra `Contact → Links` đã có `HD Customer` chưa.

### User là nhân viên support nhưng không thấy ticket queue

Kiểm tra bản ghi `HD Agent`, agent group/team, assignment rule, và permission của DocType `HD Ticket`.

### Không nên sửa tay dữ liệu nào?

Không sửa trực tiếp `Haravan Account Link` nếu không cần thiết. Đây là bảng mapping do app cập nhật sau OAuth login. Nếu sai role/org, nên kiểm tra payload Haravan trả về và cho user login lại.
