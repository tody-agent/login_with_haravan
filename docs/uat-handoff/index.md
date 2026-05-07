# Bộ tài liệu UAT và bàn giao Haravan Helpdesk

Tài liệu này dùng cho đội Haravan khi kiểm thử nghiệm thu và tiếp nhận vận hành hệ thống Helpdesk tại:

```text
https://haravan.help
```

Mục tiêu là giúp người kiểm thử đi từng bước, ghi nhận kết quả rõ ràng, và bàn giao lại cho đội vận hành sau khi hệ thống đạt yêu cầu.

## Cách dùng bộ tài liệu

1. Đọc [Bản đồ user story](./01-ban-do-user-story.md) để hiểu các nhóm nghiệp vụ chính.
2. Chuẩn bị tài khoản, dữ liệu mẫu và quyền truy cập theo [Kịch bản UAT](./02-checklist-uat.md).
3. Chạy từng checklist test, ghi kết quả vào cột `Kết quả`.
4. Với lỗi phát sinh, ghi ticket lỗi theo mẫu trong từng nhóm test.
5. Sau khi UAT đạt, dùng [Checklist bàn giao](./03-checklist-ban-giao.md) để xác nhận cấu hình, quyền, tài khoản và quy trình vận hành.

## Nhóm tính năng cần nghiệm thu

| Nhóm | Mục tiêu kiểm thử |
| --- | --- |
| Đăng nhập | Khách hàng đăng nhập bằng Haravan Account và được đưa vào đúng portal Helpdesk. |
| Đăng ký | Người dùng Haravan mới được tạo tài khoản Frappe Helpdesk đúng dữ liệu. |
| Tạo ticket | Khách hàng tạo ticket với đúng tổ chức, nội dung, file đính kèm và form trường bắt buộc. |
| Routing Assign | Ticket được gắn customer, nhóm xử lý, người phụ trách hoặc dữ liệu phân tuyến đúng cấu hình. |
| Đóng ticket | Agent xử lý, phản hồi và đóng ticket; khách hàng nhìn thấy trạng thái đúng. |
| Tích hợp | OAuth Haravan, Bitrix, GitLab, AI, email và CC hoạt động an toàn, không lộ secret. |
| Phân quyền | Owner/admin xem được ticket của tổ chức; staff chỉ xem ticket của chính mình. |
| Bàn giao vận hành | Haravan nắm được nơi cấu hình, cách test lại, cách báo lỗi và cách nâng cấp. |

## Quy ước ghi kết quả

| Giá trị | Ý nghĩa |
| --- | --- |
| Đạt | Test đúng kỳ vọng, không có lỗi chặn nghiệm thu. |
| Không đạt | Có lỗi ảnh hưởng nghiệp vụ hoặc dữ liệu. |
| Chưa test | Chưa đủ tài khoản, dữ liệu, quyền hoặc môi trường để chạy. |
| Không áp dụng | Kịch bản không thuộc phạm vi đợt nghiệm thu này. |

## Mẫu ghi lỗi

```text
Mã lỗi:
Nhóm tính năng:
Tài khoản test:
Thời điểm test:
Các bước đã làm:
Kết quả thực tế:
Kết quả mong đợi:
Ảnh chụp/video/log:
Mức độ ảnh hưởng:
Người phụ trách xử lý:
```

## Nguyên tắc an toàn khi UAT

- Không dán client secret, access token, webhook URL có secret hoặc private key vào tài liệu nghiệm thu.
- Chỉ dùng tài khoản test hoặc tài khoản được Haravan cho phép.
- Khi test tạo ticket thật, thêm tiền tố `[UAT]` vào tiêu đề để dễ lọc.
- Không xóa dữ liệu production nếu chưa có xác nhận của người phụ trách vận hành.
- Nếu cần test tích hợp có gửi email hoặc tạo GitLab issue thật, báo trước cho các bên nhận thông báo.
