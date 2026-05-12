# Hướng dẫn Import dữ liệu qua Frappe API

Tài liệu này hướng dẫn cách sử dụng **Frappe REST API** để cập nhật và import dữ liệu từ Freshdesk (hoặc hệ thống khác) vào các DocType lõi của Frappe Helpdesk: `Customer`, `Contact`, và `HD Ticket`.

## 1. Xác thực (Authentication)

Để gọi API, bạn cần tạo thông tin xác thực (`API Key` và `API Secret`) trên một user có quyền tương tác với Helpdesk (ví dụ: System Manager hoặc Administrator).

**Cách tạo API Key & Secret:**
1. Đăng nhập vào Frappe Desk.
2. Vào **User list**, chọn user bạn muốn dùng cho tích hợp.
3. Kéo xuống phần **API Access**, chọn **Generate Keys**.
4. Lưu lại `API Key` và `API Secret`. (Lưu ý: API Secret chỉ hiện một lần duy nhất).

Trong các HTTP request, gửi header `Authorization` theo định dạng:
```http
Authorization: token {api_key}:{api_secret}
```

---

## 2. API Tạo Khách hàng (Customer)

**Endpoint:** `POST /api/resource/Customer`

Khách hàng (Customer) trong ERPNext/Frappe đại diện cho một tổ chức hoặc cửa hàng (Organization).

**Payload ví dụ:**
```json
{
    "customer_name": "Công ty TNHH Haravan",
    "customer_group": "Commercial",
    "territory": "Vietnam",
    "customer_type": "Company",
    "custom_orgid": "ORG123456",
    "custom_store_url": "haravan.myharavan.com"
}
```

*Lưu ý:*
- Nếu `Customer` đã tồn tại, bạn sử dụng `PUT /api/resource/Customer/{customer_name}` để cập nhật thông tin.
- Các field `custom_orgid` và `custom_store_url` là các trường custom để mapping với dữ liệu từ Bitrix/Haravan (nếu có).

---

## 3. API Tạo Liên hệ (Contact)

**Endpoint:** `POST /api/resource/Contact`

Liên hệ (Contact) là cá nhân gửi yêu cầu hỗ trợ. Một Contact cần được liên kết (link) với một Customer đã tạo ở bước trên thông qua child table `links`.

**Payload ví dụ:**
```json
{
    "first_name": "Nguyễn",
    "last_name": "Văn A",
    "email_id": "nguyenvana@haravan.com",
    "phone": "0987654321",
    "is_primary_contact": 1,
    "status": "Passive",
    "links": [
        {
            "link_doctype": "Customer",
            "link_name": "Công ty TNHH Haravan"
        }
    ]
}
```

*Lưu ý:*
- `link_name` chính là tên của Customer đã tạo thành công ở bước 2.
- Frappe dùng `email_id` để định danh khi nhận email tạo ticket. Đảm bảo email chính xác.

---

## 4. API Tạo Ticket (HD Ticket)

**Endpoint:** `POST /api/resource/HD Ticket`

Sau khi đã có Customer và Contact, bạn có thể tạo Ticket gán trực tiếp cho họ.

**Payload ví dụ:**
```json
{
    "subject": "[Hỗ trợ] Lỗi đồng bộ đơn hàng",
    "description": "<p>Đơn hàng không đồng bộ về hệ thống ERP.</p>",
    "status": "Open",
    "priority": "Medium",
    "customer": "Công ty TNHH Haravan",
    "raised_by": "nguyenvana@haravan.com",
    "custom_haravan_routing_reason": "Tự động import từ Freshdesk",
    "creation": "2024-05-10 10:00:00"
}
```

*Lưu ý:*
- `customer`: Tên của Customer (đã tạo ở bước 2).
- `raised_by`: Phải trùng với `email_id` của Contact (đã tạo ở bước 3).
- `creation`: Bạn có thể set thời gian tạo ticket gốc (từ Freshdesk) để giữ nguyên lịch sử. (Tùy thuộc vào quyền set `creation` của role gọi API).

---

## 5. Ví dụ mã nguồn (Python)

Dưới đây là một đoạn mã Python sử dụng thư viện `requests` để import một ticket đầy đủ quy trình:

```python
import requests
import json

URL = "https://support.haravan.com"
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"

headers = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# 1. Tạo Customer
customer_data = {
    "customer_name": "Cửa hàng Demo",
    "customer_group": "Commercial",
    "territory": "Vietnam"
}
res_customer = requests.post(f"{URL}/api/resource/Customer", headers=headers, json=customer_data)
print("Customer:", res_customer.json())

# 2. Tạo Contact
contact_data = {
    "first_name": "Trần",
    "last_name": "B",
    "email_id": "tranb@example.com",
    "links": [{"link_doctype": "Customer", "link_name": "Cửa hàng Demo"}]
}
res_contact = requests.post(f"{URL}/api/resource/Contact", headers=headers, json=contact_data)
print("Contact:", res_contact.json())

# 3. Tạo HD Ticket
ticket_data = {
    "subject": "Cần hỗ trợ cấu hình theme",
    "description": "Xin hướng dẫn cách thay đổi banner trang chủ.",
    "status": "Open",
    "customer": "Cửa hàng Demo",
    "raised_by": "tranb@example.com",
    "priority": "High"
}
res_ticket = requests.post(f"{URL}/api/resource/HD Ticket", headers=headers, json=ticket_data)
print("Ticket:", res_ticket.json())
```

## 6. Lưu ý khi Migration số lượng lớn

1. **Batching/Rate Limit:**
   - Frappe REST API mặc định là synchronous. Hãy gọi tuần tự (hoặc batch nhỏ) để tránh làm sập database connection (Error 429 Too Many Requests hoặc Database Deadlock).
2. **Dữ liệu Comment (Phản hồi):**
   - Comment trên ticket được lưu ở bảng (DocType) `Communication`. Để đính kèm comment vào Ticket, gọi `POST /api/resource/Communication` với field `reference_doctype="HD Ticket"` và `reference_name="Tên Ticket"`.
3. **Idempotency:**
   - Khi chạy script import, hãy lưu lại file mapping ID của Freshdesk và tên Ticket của Frappe để tránh tạo trùng lặp khi chạy lại script do lỗi giữa chừng.
