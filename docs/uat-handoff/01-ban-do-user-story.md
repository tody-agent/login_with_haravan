# Bản đồ user story Haravan Helpdesk

Tài liệu này mô tả hành trình người dùng theo dạng user story mapping. Mỗi nhóm tính năng đi từ mục tiêu nghiệp vụ, vai trò người dùng, câu chuyện cần đạt, đến tiêu chí nghiệm thu.

## Vai trò tham gia UAT

| Vai trò | Mô tả | Ví dụ người test |
| --- | --- | --- |
| Khách hàng owner | Chủ cửa hàng Haravan, có quyền xem ticket của tổ chức. | Chủ shop test |
| Khách hàng admin | Nhân sự quản trị cửa hàng, có quyền xem ticket của tổ chức. | Quản lý vận hành shop |
| Khách hàng staff | Nhân viên cửa hàng, chỉ xem ticket do mình tạo. | Nhân viên xử lý đơn |
| Agent hỗ trợ | Nhân viên Haravan tiếp nhận và xử lý ticket. | CS/Support |
| Quản trị Helpdesk | Người cấu hình form, routing, template và tích hợp. | Admin hệ thống |
| Kỹ thuật tích hợp | Người kiểm tra OAuth, Bitrix, GitLab, AI, email. | Dev/IT |

## 1. Đăng nhập

### Mục tiêu

Khách hàng dùng Haravan Account để vào Helpdesk mà không cần tạo mật khẩu riêng trên Frappe.

### User stories

| Mã | Câu chuyện người dùng | Tiêu chí nghiệm thu |
| --- | --- | --- |
| LG-01 | Là khách hàng Haravan, tôi muốn bấm `Login with Haravan Account` để đăng nhập Helpdesk. | Nút đăng nhập hiển thị trên trang login và chuyển đến Haravan đúng callback. |
| LG-02 | Là khách hàng đã đăng nhập Haravan thành công, tôi muốn được đưa về trang Helpdesk đang mở trước đó. | Sau callback, người dùng vào đúng portal Helpdesk, không bị đưa nhầm về Desk nội bộ. |
| LG-03 | Là khách hàng thuộc nhiều tổ chức, tôi muốn hệ thống ghi nhận đúng tổ chức Haravan của tôi. | `Haravan Account Link` có đúng user ID, org ID, org name và HD Customer. |
| LG-04 | Là quản trị viên, tôi muốn lỗi login được ghi nhận đủ để debug. | Khi thiếu email/orgid/userid hoặc sai redirect, hệ thống có thông tin lỗi rõ ràng trong log. |

## 2. Đăng ký

### Mục tiêu

Người dùng Haravan lần đầu đăng nhập sẽ được tạo tài khoản Helpdesk và dữ liệu khách hàng tương ứng.

### User stories

| Mã | Câu chuyện người dùng | Tiêu chí nghiệm thu |
| --- | --- | --- |
| RG-01 | Là khách hàng mới, tôi muốn đăng nhập lần đầu và có tài khoản Helpdesk tự động. | Hệ thống tạo `User` dạng website user theo email Haravan. |
| RG-02 | Là khách hàng mới, tôi muốn cửa hàng của mình được tạo thành customer trong Helpdesk. | Hệ thống tạo hoặc cập nhật `HD Customer` theo Haravan org ID. |
| RG-03 | Là khách hàng đã có user Frappe, tôi muốn đăng nhập Haravan bằng cùng email mà không bị tạo trùng. | Hệ thống dùng lại `User` hiện có và chỉ thêm mapping Haravan nếu cần. |
| RG-04 | Là owner/admin, tôi muốn thấy ticket của tổ chức. | `Contact` được link với `HD Customer`. |
| RG-05 | Là staff, tôi chỉ được thấy ticket của chính mình. | `Contact` không được link org-wide và portal không hiện ticket người khác. |

## 3. Tạo ticket

### Mục tiêu

Khách hàng tạo được yêu cầu hỗ trợ đầy đủ thông tin, đúng cửa hàng/tổ chức, và ticket đi vào Helpdesk để agent xử lý.

### User stories

| Mã | Câu chuyện người dùng | Tiêu chí nghiệm thu |
| --- | --- | --- |
| TK-01 | Là khách hàng, tôi muốn mở form tạo ticket từ portal. | Trang tạo ticket mở được sau đăng nhập. |
| TK-02 | Là khách hàng, tôi muốn chọn đúng tổ chức/cửa hàng khi có nhiều org. | Dropdown tổ chức hiển thị đúng danh sách org được liên kết. |
| TK-03 | Là khách hàng, tôi muốn nhập tiêu đề, mô tả, loại vấn đề và thông tin bắt buộc. | Form validate đúng field bắt buộc, không cho gửi thiếu dữ liệu quan trọng. |
| TK-04 | Là khách hàng, tôi muốn đính kèm hình ảnh hoặc file lỗi. | File đính kèm được lưu cùng ticket và agent xem được. |
| TK-05 | Là agent, tôi muốn ticket có đúng `HD Customer`, `Contact`, `raised_by` và dữ liệu Haravan. | Ticket mới chứa đúng customer/contact/orgid để xử lý và phân tuyến. |

## 4. Routing Assign

### Mục tiêu

Ticket sau khi tạo được phân loại, gắn nhóm xử lý, người phụ trách hoặc dữ liệu gợi ý đúng theo cấu hình vận hành.

### User stories

| Mã | Câu chuyện người dùng | Tiêu chí nghiệm thu |
| --- | --- | --- |
| RT-01 | Là agent, tôi muốn ticket có thông tin customer segment hoặc shopplan khi có dữ liệu Bitrix. | Field segment/shopplan được cập nhật hoặc hiển thị trong hồ sơ khách hàng. |
| RT-02 | Là quản trị vận hành, tôi muốn ticket được gợi ý sản phẩm/module phù hợp. | `HD Ticket Product Suggestion` prefill đúng label, module hoặc GitLab metadata. |
| RT-03 | Là agent, tôi muốn thấy người phụ trách từ Bitrix khi có dữ liệu. | `custom_responsible` được cập nhật khi Bitrix trả về responsible active có email. |
| RT-04 | Là lead support, tôi muốn biết lý do ticket được routing. | Ticket hoặc popup có thông tin routing reason/status dễ hiểu. |

## 5. Đóng ticket

### Mục tiêu

Agent có thể phản hồi, xử lý, chuyển trạng thái và đóng ticket; khách hàng theo dõi được kết quả.

### User stories

| Mã | Câu chuyện người dùng | Tiêu chí nghiệm thu |
| --- | --- | --- |
| CL-01 | Là agent, tôi muốn trả lời ticket cho khách hàng. | Reply được gửi và lưu trong timeline ticket. |
| CL-02 | Là khách hàng, tôi muốn nhận email hoặc thông báo khi agent phản hồi. | Email/thông báo đến đúng người nhận, CC đúng nếu có cấu hình. |
| CL-03 | Là agent, tôi muốn đóng ticket sau khi xử lý xong. | Status chuyển sang trạng thái đóng theo workflow Helpdesk. |
| CL-04 | Là khách hàng, tôi muốn nhìn thấy ticket đã đóng trên portal. | Portal hiển thị trạng thái đóng và lịch sử trao đổi. |
| CL-05 | Là agent, tôi muốn mở lại ticket khi khách phản hồi thêm nếu quy trình cho phép. | Ticket có thể reopen hoặc tạo follow-up theo quy trình Haravan. |

## 6. Tích hợp

### Mục tiêu

Các tích hợp bên ngoài hoạt động đúng, bảo mật, và có cách kiểm tra rõ ràng khi lỗi.

### User stories

| Mã | Câu chuyện người dùng | Tiêu chí nghiệm thu |
| --- | --- | --- |
| IN-01 | Là khách hàng, tôi muốn Haravan OAuth xác thực ổn định. | Redirect URL, scope, client ID/secret đúng cấu hình. |
| IN-02 | Là agent, tôi muốn xem hồ sơ khách hàng từ Bitrix trong ticket. | Popup hồ sơ hiển thị công ty, HSI, shopplan, responsible nếu có. |
| IN-03 | Là agent, tôi muốn tạo hoặc chuẩn bị GitLab issue từ ticket. | Label, assignee và product suggestion được prefill đúng cấu hình. |
| IN-04 | Là agent, tôi muốn dùng AI hỗ trợ phân tích hoặc soạn phản hồi nếu được bật. | Nút AI hoạt động, không làm mất nội dung ticket, lỗi được báo dễ hiểu. |
| IN-05 | Là quản trị, tôi muốn secret được lưu server-side. | Token không xuất hiện trong browser, client script, tài liệu hoặc ticket. |

## 7. Bàn giao vận hành

### Mục tiêu

Haravan có thể tự vận hành các tác vụ hằng ngày và biết khi nào cần gọi đội kỹ thuật.

### User stories

| Mã | Câu chuyện người dùng | Tiêu chí nghiệm thu |
| --- | --- | --- |
| HO-01 | Là admin Haravan, tôi muốn biết nơi cấu hình form tạo ticket. | Biết mở `HD Ticket Template - Default` và chỉnh field đúng cách. |
| HO-02 | Là admin Haravan, tôi muốn biết nơi cấu hình product suggestion. | Biết thêm/sửa/import `HD Ticket Product Suggestion`. |
| HO-03 | Là admin Haravan, tôi muốn biết nơi cấu hình token tích hợp. | Biết Site Config hoặc Helpdesk Integrations Settings, không lộ secret. |
| HO-04 | Là vận hành, tôi muốn có checklist smoke test sau mỗi lần đổi cấu hình. | Có thể chạy lại checklist ngắn để xác nhận hệ thống vẫn ổn. |
| HO-05 | Là quản lý dự án, tôi muốn có biên bản nghiệm thu. | Có danh sách test đã đạt, lỗi còn mở, người phụ trách và ngày ký nhận. |
