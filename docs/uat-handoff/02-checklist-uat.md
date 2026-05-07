# Checklist UAT Haravan Helpdesk

Tài liệu này là checklist test nghiệm thu theo từng nhóm tính năng. Người test có thể copy từng bảng sang Google Sheet hoặc điền trực tiếp vào file khi cần.

## Chuẩn bị trước UAT

| Hạng mục | Cách kiểm tra | Kết quả |
| --- | --- | --- |
| Domain production mở được | Truy cập `https://haravan.help`. | Chưa test |
| Có tài khoản Haravan owner | Tài khoản thuộc ít nhất một org test. | Chưa test |
| Có tài khoản Haravan admin | Tài khoản thuộc cùng org với owner. | Chưa test |
| Có tài khoản Haravan staff | Tài khoản staff không có quyền quản trị org. | Chưa test |
| Có tài khoản multi-org | Một email thuộc ít nhất hai tổ chức Haravan. | Chưa test |
| Có tài khoản agent Helpdesk | Agent đăng nhập được Desk/Helpdesk. | Chưa test |
| Có quyền kiểm tra cấu hình | Admin có quyền xem Social Login Key, HD Ticket Template, Helpdesk Integrations Settings. | Chưa test |
| Có dữ liệu Bitrix test | Có ít nhất một company có Haravan org ID tương ứng. | Chưa test |
| Có GitLab project test | Có label và assignee test nếu kiểm thử GitLab. | Chưa test |

## 1. Đăng nhập

### LG-01: Hiển thị nút Login With Haravan

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Mở `https://haravan.help/login`. | Trang login hiển thị bình thường. | Chưa test |
| 2 | Tìm nút `Login with Haravan Account` hoặc nhãn tiếng Việt tương ứng. | Nút đăng nhập Haravan hiển thị rõ ràng. | Chưa test |
| 3 | Copy link của nút đăng nhập. | Link trỏ đến `accounts.haravan.com` và có `redirect_uri`. | Chưa test |
| 4 | Decode `redirect_uri`. | Giá trị đúng là `https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan`. | Chưa test |

### LG-02: Đăng nhập thành công bằng owner

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Mở `https://haravan.help/helpdesk`. | Nếu chưa login, hệ thống yêu cầu đăng nhập. | Chưa test |
| 2 | Bấm login Haravan và đăng nhập bằng tài khoản owner. | Haravan xác thực thành công. | Chưa test |
| 3 | Cho phép ứng dụng nếu Haravan hỏi quyền. | Người dùng được redirect về `haravan.help`. | Chưa test |
| 4 | Kiểm tra portal Helpdesk. | Người dùng vào được danh sách ticket hoặc trang tạo ticket. | Chưa test |
| 5 | Admin kiểm tra `Haravan Account Link`. | Có record đúng email, user ID, org ID, org name, HD Customer. | Chưa test |

### LG-03: Đăng nhập thất bại được báo rõ

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Dùng tài khoản hoặc cấu hình test có thể tạo lỗi, ví dụ redirect sai trên môi trường staging. | Haravan hoặc Frappe báo lỗi rõ, không vào trạng thái trắng trang. | Chưa test |
| 2 | Kiểm tra Error Log hoặc thông báo kỹ thuật. | Có thông tin đủ để phân biệt sai redirect, thiếu email, thiếu orgid hoặc lỗi token. | Chưa test |

## 2. Đăng ký

### RG-01: User mới đăng nhập lần đầu

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Chuẩn bị email Haravan chưa tồn tại trong Frappe. | Email chưa có trong `User`. | Chưa test |
| 2 | Đăng nhập bằng Haravan Account đó. | Login thành công. | Chưa test |
| 3 | Admin mở `User`. | Có user mới theo email Haravan, dạng website user. | Chưa test |
| 4 | Admin mở `Contact`. | Có contact tương ứng email. | Chưa test |
| 5 | Admin mở `HD Customer`. | Có customer theo tổ chức Haravan. | Chưa test |
| 6 | Admin mở `Haravan Account Link`. | Có mapping đúng user, email, orgid, userid. | Chưa test |

### RG-02: User đã tồn tại không bị tạo trùng

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Chọn một email đã có `User` trong Frappe. | Xác nhận chỉ có một user với email đó. | Chưa test |
| 2 | Đăng nhập Haravan bằng email này. | Login thành công. | Chưa test |
| 3 | Kiểm tra lại danh sách `User`. | Không tạo thêm user trùng email. | Chưa test |
| 4 | Kiểm tra `Haravan Account Link`. | Mapping Haravan được thêm hoặc cập nhật đúng. | Chưa test |

### RG-03: Multi-org

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Dùng tài khoản cùng email thuộc hai org Haravan. | Haravan trả được hai ngữ cảnh org hoặc người dùng có thể login từng org. | Chưa test |
| 2 | Đăng nhập với org thứ nhất. | Có `HD Customer` và `Haravan Account Link` cho org thứ nhất. | Chưa test |
| 3 | Đăng nhập với org thứ hai. | Có thêm `HD Customer` và `Haravan Account Link` cho org thứ hai. | Chưa test |
| 4 | Mở trang tạo ticket. | Có thể chọn đúng tổ chức khi tạo ticket. | Chưa test |

## 3. Tạo ticket

### TK-01: Tạo ticket cơ bản

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Đăng nhập portal bằng khách hàng owner. | Vào được Helpdesk portal. | Chưa test |
| 2 | Mở trang tạo ticket mới. | Form tạo ticket hiển thị. | Chưa test |
| 3 | Nhập tiêu đề `[UAT] Test tạo ticket cơ bản`. | Tiêu đề được nhận. | Chưa test |
| 4 | Nhập mô tả lỗi rõ ràng. | Mô tả được nhận, không mất format cơ bản. | Chưa test |
| 5 | Chọn loại ticket/sản phẩm/nhóm vấn đề nếu form có. | Lựa chọn lưu đúng. | Chưa test |
| 6 | Bấm gửi. | Ticket được tạo thành công và có mã ticket. | Chưa test |
| 7 | Agent mở ticket trong Helpdesk. | Agent thấy đúng subject, description, raised_by, contact, customer. | Chưa test |

### TK-02: Validate field bắt buộc

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Mở form tạo ticket. | Form hiển thị bình thường. | Chưa test |
| 2 | Bỏ trống từng field bắt buộc rồi bấm gửi. | Hệ thống báo thiếu field, không tạo ticket rỗng. | Chưa test |
| 3 | Nhập đủ field bắt buộc. | Gửi ticket thành công. | Chưa test |

### TK-03: Đính kèm file

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Tạo ticket có file ảnh hoặc PDF test. | Upload không lỗi. | Chưa test |
| 2 | Gửi ticket. | Ticket được tạo thành công. | Chưa test |
| 3 | Agent mở ticket. | File đính kèm xem hoặc tải được. | Chưa test |

### TK-04: Staff tạo ticket

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Đăng nhập bằng tài khoản staff. | Vào portal thành công. | Chưa test |
| 2 | Tạo ticket `[UAT] Staff tạo ticket`. | Ticket tạo thành công. | Chưa test |
| 3 | Staff mở danh sách ticket của mình. | Thấy ticket vừa tạo. | Chưa test |
| 4 | Staff tìm ticket của owner/admin cùng org. | Không thấy ticket không thuộc mình. | Chưa test |

## 4. Routing Assign

### RT-01: Ticket tự gắn customer/org

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Tạo ticket bằng tài khoản chỉ thuộc một org. | Ticket được tạo. | Chưa test |
| 2 | Agent mở ticket. | Field `customer` gắn đúng `HD Customer`. | Chưa test |
| 3 | Kiểm tra org ID trên customer hoặc ticket. | Org ID đúng với Haravan org của người tạo. | Chưa test |

### RT-02: Multi-org chọn đúng customer

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Đăng nhập bằng tài khoản multi-org. | Portal nhận biết nhiều org. | Chưa test |
| 2 | Tạo ticket và chọn org A. | Ticket gắn customer của org A. | Chưa test |
| 3 | Tạo ticket khác và chọn org B. | Ticket gắn customer của org B. | Chưa test |

### RT-03: Product suggestion và GitLab metadata

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Mở `HD Ticket Product Suggestion`. | Có record test với product/module/label/assignee. | Chưa test |
| 2 | Tạo hoặc mở ticket chọn đúng product suggestion. | Ticket lưu được product suggestion. | Chưa test |
| 3 | Mở popup tạo GitLab issue nếu có trong quy trình. | Label và assignee được prefill theo record cấu hình. | Chưa test |
| 4 | Nếu test tạo issue thật, tạo issue test. | GitLab issue có đúng title, link ticket, label, assignee. | Chưa test |

### RT-04: Responsible từ Bitrix

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Chọn ticket có customer map được sang Bitrix company. | Ticket có org ID hoặc customer đúng. | Chưa test |
| 2 | Agent bấm xem hoặc refresh hồ sơ khách hàng. | API gọi Bitrix thành công. | Chưa test |
| 3 | Kiểm tra field người phụ trách trên ticket. | Nếu Bitrix responsible active và có email, field `custom_responsible` được cập nhật. | Chưa test |
| 4 | Kiểm tra trường hợp responsible inactive hoặc thiếu email. | Hệ thống không ghi sai email, chỉ báo trạng thái phù hợp. | Chưa test |

## 5. Đóng ticket

### CL-01: Agent phản hồi ticket

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Agent mở ticket `[UAT]`. | Ticket mở được. | Chưa test |
| 2 | Agent gửi reply cho khách hàng. | Reply lưu trong timeline. | Chưa test |
| 3 | Khách hàng mở portal. | Khách thấy phản hồi mới. | Chưa test |
| 4 | Kiểm tra email nếu bật gửi mail. | Email đến đúng người nhận. | Chưa test |

### CL-02: CC email

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Agent nhập CC hợp lệ vào field CC của ticket nếu quy trình có dùng. | Field lưu được danh sách email hợp lệ. | Chưa test |
| 2 | Agent gửi reply. | Email gửi tới người nhận chính và CC. | Chưa test |
| 3 | Nhập email CC sai định dạng. | Hệ thống báo lỗi, không gửi email sai. | Chưa test |

### CL-03: Đóng ticket

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Agent xử lý xong ticket test. | Ticket có phản hồi cuối hoặc ghi chú xử lý. | Chưa test |
| 2 | Agent chuyển status sang trạng thái đóng. | Status được cập nhật thành closed/resolved theo cấu hình Helpdesk. | Chưa test |
| 3 | Khách hàng mở portal. | Ticket hiển thị trạng thái đã đóng. | Chưa test |
| 4 | Lọc danh sách ticket theo trạng thái. | Ticket xuất hiện đúng ở nhóm đã đóng. | Chưa test |

## 6. Tích hợp

### IN-01: Haravan OAuth

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Kiểm tra Social Login Key `Login With Haravan`. | Provider bật, client ID đúng, redirect URL là callback tương đối hoặc URL đúng domain. | Chưa test |
| 2 | Kiểm tra Haravan Partner Dashboard. | Callback URL khớp chính xác production callback. | Chưa test |
| 3 | Kiểm tra scope. | Scope gồm `openid profile email org userinfo`. | Chưa test |
| 4 | Test login thật. | Không gặp lỗi `invalid_request Invalid redirect_uri`. | Chưa test |

### IN-02: Bitrix profile

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Admin kiểm tra `Helpdesk Integrations Settings`. | Bitrix bật và webhook đã cấu hình server-side. | Chưa test |
| 2 | Agent mở ticket có org ID match Bitrix. | Ticket mở được. | Chưa test |
| 3 | Bấm `Xem hồ sơ khách hàng` hoặc nút tương ứng. | Popup hiển thị dữ liệu customer/contact/Bitrix. | Chưa test |
| 4 | Bấm refresh nếu có. | Dữ liệu cập nhật hoặc trả trạng thái cached/not_found rõ ràng. | Chưa test |
| 5 | Kiểm tra browser devtools nếu cần. | Không thấy webhook secret hoặc token trong response/client script. | Chưa test |

### IN-03: AI hỗ trợ

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Mở ticket test có nội dung đủ dài. | Ticket mở được. | Chưa test |
| 2 | Bấm nút AI phân tích hoặc hỗ trợ trả lời nếu đang bật. | AI trả kết quả hữu ích hoặc báo lỗi cấu hình rõ ràng. | Chưa test |
| 3 | Kiểm tra nội dung ticket gốc. | AI không tự ý làm mất subject/description/comment gốc. | Chưa test |

### IN-04: Email thông báo

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Khách tạo ticket mới. | Hệ thống gửi acknowledgement nếu cấu hình email bật. | Chưa test |
| 2 | Agent reply. | Khách nhận email reply. | Chưa test |
| 3 | Kiểm tra người nhận. | Không gửi cho sai customer hoặc sai org. | Chưa test |

## 7. Phân quyền

### PR-01: Owner/admin xem ticket toàn tổ chức

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Owner tạo ticket A. | Ticket A tạo thành công. | Chưa test |
| 2 | Admin cùng org đăng nhập portal. | Admin thấy ticket A nếu quy trình cho phép owner/admin xem org-wide. | Chưa test |
| 3 | Admin tạo ticket B. | Ticket B tạo thành công. | Chưa test |
| 4 | Owner mở portal. | Owner thấy ticket B. | Chưa test |

### PR-02: Staff chỉ xem ticket của mình

| Bước | Thao tác | Kết quả mong đợi | Kết quả |
| --- | --- | --- | --- |
| 1 | Staff tạo ticket C. | Ticket C tạo thành công. | Chưa test |
| 2 | Staff mở danh sách ticket. | Staff thấy ticket C. | Chưa test |
| 3 | Staff tìm ticket A/B của owner/admin. | Staff không thấy ticket A/B nếu không phải người tạo. | Chưa test |

## Checklist kết thúc UAT

| Hạng mục | Tiêu chí đạt | Kết quả |
| --- | --- | --- |
| Đăng nhập | Owner, admin, staff đăng nhập được bằng Haravan. | Chưa test |
| Đăng ký | User/Contact/HD Customer/Haravan Account Link tạo đúng. | Chưa test |
| Tạo ticket | Ticket tạo được, đúng customer/contact/org, đúng field bắt buộc. | Chưa test |
| Routing Assign | Product suggestion, Bitrix responsible, customer segment hoạt động theo phạm vi đã bật. | Chưa test |
| Đóng ticket | Agent reply và đóng ticket, khách thấy trạng thái đúng. | Chưa test |
| Tích hợp | OAuth, Bitrix, GitLab, AI, email đạt hoặc có danh sách ngoại lệ đã thống nhất. | Chưa test |
| Phân quyền | Owner/admin/staff có quyền xem đúng. | Chưa test |
| Bảo mật | Không lộ secret trên browser, tài liệu, ticket hoặc log người dùng. | Chưa test |

## Mẫu tổng kết UAT

```text
Ngày test:
Môi trường:
Người test phía Haravan:
Người hỗ trợ kỹ thuật:

Tổng số test case:
Số case đạt:
Số case không đạt:
Số case chưa test:
Số lỗi chặn nghiệm thu:

Kết luận:
Đề xuất go-live:
Các việc cần làm sau UAT:
```
