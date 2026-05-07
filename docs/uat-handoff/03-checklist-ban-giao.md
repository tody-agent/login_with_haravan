# Checklist bàn giao vận hành Haravan Helpdesk

Tài liệu này dùng sau khi UAT đạt để bàn giao hệ thống cho Haravan vận hành. Mỗi mục nên có người nhận, ngày xác nhận và ghi chú nếu còn ngoại lệ.

## 1. Thông tin hệ thống

| Hạng mục | Giá trị cần bàn giao | Người nhận | Trạng thái |
| --- | --- | --- | --- |
| Domain production | `https://haravan.help` |  | Chưa bàn giao |
| Frappe Cloud site slug | `haravandesk.s.frappe.cloud` |  | Chưa bàn giao |
| Repository source code | `https://github.com/tody-agent/login_with_haravan` |  | Chưa bàn giao |
| App Frappe | `login_with_haravan` |  | Chưa bàn giao |
| OAuth callback | `/api/method/login_with_haravan.oauth.login_via_haravan` |  | Chưa bàn giao |
| Public callback URL | `https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan` |  | Chưa bàn giao |

## 2. Bàn giao quyền truy cập

| Quyền | Mục đích | Người nhận | Trạng thái |
| --- | --- | --- | --- |
| Frappe Cloud site admin | Cấu hình site, xem logs, site config. |  | Chưa bàn giao |
| Frappe Desk admin | Cấu hình Helpdesk, template, user, ticket. |  | Chưa bàn giao |
| Helpdesk agent | Tiếp nhận và xử lý ticket. |  | Chưa bàn giao |
| Haravan Partner Dashboard | Quản lý OAuth app và callback URL. |  | Chưa bàn giao |
| Bitrix admin/webhook owner | Quản lý webhook customer và responsible. |  | Chưa bàn giao |
| GitLab project quyền phù hợp | Kiểm tra label, assignee, issue tạo từ ticket. |  | Chưa bàn giao |

## 3. Bàn giao cấu hình đăng nhập Haravan

| Mục kiểm tra | Cách xác nhận | Trạng thái |
| --- | --- | --- |
| Haravan OAuth app đúng môi trường production | Callback URL trong Partner Dashboard khớp chính xác production callback. | Chưa xác nhận |
| Scope đúng | Scope gồm `openid profile email org userinfo`. | Chưa xác nhận |
| Client ID đúng | Client ID trong Frappe thuộc cùng app Haravan đang có callback. | Chưa xác nhận |
| Client Secret lưu an toàn | Secret nằm trong Site Config hoặc cấu hình server-side, không nằm trong client script. | Chưa xác nhận |
| Social Login Key bật | `Login With Haravan` đang enabled trong Frappe. | Chưa xác nhận |
| Redirect sau login đúng | Người dùng quay về portal Helpdesk, không vào Desk nội bộ. | Chưa xác nhận |

## 4. Bàn giao cấu hình tài khoản và phân quyền

| Mục kiểm tra | Cách xác nhận | Trạng thái |
| --- | --- | --- |
| User mới được tạo theo email Haravan | Test bằng tài khoản mới, kiểm tra `User`. | Chưa xác nhận |
| Contact được tạo theo email | Kiểm tra `Contact.email_id`. | Chưa xác nhận |
| HD Customer được tạo theo org Haravan | Kiểm tra `HD Customer.custom_haravan_orgid`. | Chưa xác nhận |
| Haravan Account Link lưu mapping | Kiểm tra user ID, org ID, org name. | Chưa xác nhận |
| Owner/admin xem ticket toàn tổ chức | Test hai user cùng org. | Chưa xác nhận |
| Staff chỉ xem ticket của mình | Test staff không thấy ticket người khác. | Chưa xác nhận |

## 5. Bàn giao form tạo ticket

Trang cấu hình chính:

```text
HD Ticket Template - Default
```

| Mục kiểm tra | Người vận hành cần biết | Trạng thái |
| --- | --- | --- |
| Thêm field vào form ticket | Tạo custom field trên `HD Ticket`, sau đó thêm fieldname vào template. | Chưa bàn giao |
| Field bắt buộc | Tick required trong template và test portal. | Chưa bàn giao |
| Field ẩn với khách hàng | Tick hide from customer nếu field chỉ dùng nội bộ. | Chưa bàn giao |
| Field dependency | Cấu hình parent/child trong Helpdesk settings hoặc HD Form Script. | Chưa bàn giao |
| Multi-org selector | Khi user có nhiều org, chọn đúng customer trước khi gửi ticket. | Chưa bàn giao |
| Smoke test sau khi đổi form | Tạo một ticket test `[UAT]` và kiểm tra agent thấy đủ dữ liệu. | Chưa bàn giao |

## 6. Bàn giao routing và assign

| Mục kiểm tra | Người vận hành cần biết | Trạng thái |
| --- | --- | --- |
| Customer trên ticket | Ticket phải gắn đúng `HD Customer`. | Chưa bàn giao |
| Product suggestion | Cập nhật tại `HD Ticket Product Suggestion`. | Chưa bàn giao |
| GitLab labels | Nhập label text, phân cách bằng dấu phẩy. | Chưa bàn giao |
| GitLab assignee | Nhập GitLab user ID dạng số, không nhập email hoặc username. | Chưa bàn giao |
| Responsible từ Bitrix | Dữ liệu lấy từ `ASSIGNED_BY_ID` và `user.get`, chỉ ghi khi user active có email. | Chưa bàn giao |
| Routing reason/status | Khi routing sai, kiểm tra org ID, Bitrix match, product suggestion và cấu hình team. | Chưa bàn giao |

## 7. Bàn giao xử lý và đóng ticket

| Mục kiểm tra | Quy trình vận hành đề xuất | Trạng thái |
| --- | --- | --- |
| Agent tiếp nhận ticket mới | Lọc ticket mới, kiểm tra customer, contact, nội dung và file đính kèm. | Chưa bàn giao |
| Agent phản hồi khách | Reply trong Helpdesk, kiểm tra người nhận và CC nếu có. | Chưa bàn giao |
| Ghi chú nội bộ | Dùng internal note khi không muốn gửi cho khách. | Chưa bàn giao |
| Đóng ticket | Chỉ đóng sau khi đã phản hồi hoặc có kết luận xử lý. | Chưa bàn giao |
| Reopen/follow-up | Nếu khách phản hồi lại sau khi đóng, làm theo workflow Helpdesk đã thống nhất. | Chưa bàn giao |

## 8. Bàn giao tích hợp

### Haravan OAuth

| Mục | Nơi cấu hình | Trạng thái |
| --- | --- | --- |
| Client ID/Secret | Frappe Cloud Site Config hoặc cấu hình server-side tương ứng. | Chưa bàn giao |
| Callback URL | Haravan Partner Dashboard. | Chưa bàn giao |
| Social Login Key | Frappe Desk. | Chưa bàn giao |

### Bitrix

| Mục | Nơi cấu hình | Trạng thái |
| --- | --- | --- |
| Bật/tắt Bitrix | `Helpdesk Integrations Settings`. | Chưa bàn giao |
| Customer webhook | Password field server-side, scope `crm`. | Chưa bàn giao |
| Responsible webhook | Password field server-side, scope `user_basic`. | Chưa bàn giao |
| Portal URL | Dùng tạo link mở CRM Bitrix. | Chưa bàn giao |
| Timeout/TTL | Dùng kiểm soát thời gian gọi API và cache. | Chưa bàn giao |

### GitLab

| Mục | Nơi cấu hình | Trạng thái |
| --- | --- | --- |
| Project mặc định | Cấu hình Helpdesk/GitLab hiện có. | Chưa bàn giao |
| Labels | GitLab project và `HD Ticket Product Suggestion`. | Chưa bàn giao |
| Assignee | GitLab user ID trong `HD Ticket Product Suggestion`. | Chưa bàn giao |

### AI

| Mục | Nơi cấu hình | Trạng thái |
| --- | --- | --- |
| API key | Site Config hoặc cấu hình server-side được chuẩn hóa. | Chưa bàn giao |
| Model | Site Config hoặc settings tương ứng. | Chưa bàn giao |
| Smoke test | Mở ticket test, bấm phân tích/soạn phản hồi, kiểm tra lỗi. | Chưa bàn giao |

### Email

| Mục | Cách xác nhận | Trạng thái |
| --- | --- | --- |
| Acknowledgement email | Khách tạo ticket và nhận email xác nhận. | Chưa bàn giao |
| Agent reply email | Agent reply, khách nhận email. | Chưa bàn giao |
| CC email | CC hợp lệ nhận email, CC sai bị chặn. | Chưa bàn giao |

## 9. Checklist smoke test sau mỗi lần đổi cấu hình

Chạy checklist ngắn này sau khi đổi OAuth, form ticket, routing, Bitrix, GitLab, AI hoặc email.

| Bước | Thao tác | Kết quả mong đợi |
| --- | --- | --- |
| 1 | Login bằng tài khoản owner. | Vào portal thành công. |
| 2 | Login bằng tài khoản staff. | Vào portal thành công, quyền xem ticket đúng. |
| 3 | Tạo ticket `[UAT] Smoke test`. | Ticket tạo thành công. |
| 4 | Agent mở ticket. | Customer, contact, org, nội dung đúng. |
| 5 | Bấm xem hồ sơ khách hàng nếu Bitrix bật. | Popup trả dữ liệu hoặc trạng thái rõ ràng. |
| 6 | Kiểm tra product suggestion/GitLab nếu có dùng. | Label/assignee đúng cấu hình. |
| 7 | Agent reply. | Reply lưu và email gửi đúng nếu email bật. |
| 8 | Đóng ticket. | Portal hiển thị ticket đã đóng. |

## 10. Khi nào gọi đội kỹ thuật

Gọi đội kỹ thuật khi gặp một trong các trường hợp sau:

- Haravan báo `invalid_request Invalid redirect_uri`.
- Login thành công ở Haravan nhưng Frappe không tạo user hoặc không vào portal.
- Ticket tạo ra không có customer/contact/org dù user đã có Haravan Account Link.
- Staff thấy ticket của người khác hoặc owner/admin không thấy ticket cùng tổ chức.
- Bitrix popup báo lỗi server, timeout kéo dài hoặc không match dù org ID đúng.
- GitLab issue tạo sai project, sai assignee hoặc không có label dù cấu hình đúng.
- AI báo lỗi token/model hoặc trả nội dung không phù hợp.
- Email gửi sai người nhận, gửi trùng bất thường hoặc CC không đúng.
- Cần thêm field mới, workflow mới hoặc logic routing phức tạp hơn cấu hình hiện tại.

## 11. Biên bản bàn giao mẫu

```text
Tên dự án:
Môi trường bàn giao:
Ngày bàn giao:

Đại diện Haravan:
Đại diện kỹ thuật:
Đại diện quản lý dự án:

Phạm vi đã bàn giao:
- Đăng nhập Haravan:
- Đăng ký user/customer/contact:
- Tạo ticket:
- Routing/assign:
- Đóng ticket:
- Tích hợp Bitrix:
- Tích hợp GitLab:
- AI:
- Email:
- Phân quyền:

Danh sách lỗi còn mở:
1.
2.
3.

Ngoại lệ đã thống nhất:
1.
2.
3.

Kết luận:
Haravan xác nhận đã nhận tài liệu, quyền truy cập cần thiết và quy trình vận hành cơ bản.

Chữ ký/xác nhận:
```
