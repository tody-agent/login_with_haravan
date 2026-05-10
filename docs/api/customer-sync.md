---
title: API — Đồng bộ dữ liệu Khách hàng
description: Hướng dẫn tích hợp đồng bộ dữ liệu khách hàng (HD Customer) từ hệ thống nội bộ Haravan sang Frappe Helpdesk
keywords: api, đồng bộ, khách hàng, customer sync, hd customer, haravan
robots: index, follow
---

# 🔄 API: Đồng bộ dữ liệu Khách hàng

:::info Tóm tắt
Tài liệu hướng dẫn dành cho đội ngũ Tech Haravan để đồng bộ, tạo mới hoặc cập nhật dữ liệu khách hàng (DocType `HD Customer`) từ hệ thống nội bộ sang Frappe Helpdesk thông qua REST API chuẩn của Frappe.
:::

## 1. Cơ chế xác thực (Authentication)

Để gọi API của Frappe Helpdesk, bạn cần tạo **API Key** và **API Secret** của một User hệ thống (System User) có phân quyền (Role) cho phép tạo, sửa, đọc DocType `HD Customer`.

Thêm Header sau vào mọi request:

```http
Authorization: token {api_key}:{api_secret}
```

*Ví dụ:* `Authorization: token 1a2b3c4d5e6f7g8:9h8g7f6e5d4c3b2`

## 2. Thông tin đối tượng (Data Model)

DocType trên Helpdesk lưu trữ thông tin khách hàng tổ chức là: `HD Customer`

Các trường (fields) quan trọng cần lưu ý khi đồng bộ:

| Trường (Field) | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---|---|:---:|---|
| `customer_name` | Data | ✅ | Tên khách hàng (ID duy nhất của bản ghi). **Bắt buộc** theo định dạng `"{orgid} - {orgname}"` (VD: `123456 - Cửa hàng Demo Haravan`). Nếu sai định dạng, quy trình tự động map dữ liệu có thể lỗi. |
| `custom_haravan_orgid` | Int | ❌ | Mã tổ chức trên Haravan (Org ID). Rất quan trọng để các luồng enrichment nhận diện được khách. |
| `custom_myharavan` | Data | ❌ | Tên miền myharavan của khách hàng (VD: `demo-haravan.myharavan.com`). |
| `customer_group` | Link | ❌ | Nhóm khách hàng (Mặc định gửi `Commercial`). |
| `territory` | Link | ❌ | Khu vực (Mặc định gửi `All Territories`). |
| `custom_bitrix_company_id` | Data | ❌ | ID công ty trên hệ thống CRM Bitrix24 (nếu có map sẵn). |

## 3. API Tạo mới khách hàng (Create)

Sử dụng phương thức `POST` để tạo mới một `HD Customer` khi có một khách hàng / tenant mới được tạo trên hệ thống Haravan.

**Endpoint:**
```http
POST https://haravandesk.s.frappe.cloud/api/resource/HD%20Customer
```

**Payload (JSON):**
```json
{
  "customer_name": "123456 - Cửa hàng Demo Haravan",
  "custom_haravan_orgid": 123456,
  "custom_myharavan": "demo-haravan.myharavan.com"
}
```

**Response thành công (200 OK):**
```json
{
  "data": {
    "name": "123456 - Cửa hàng Demo Haravan",
    "customer_name": "123456 - Cửa hàng Demo Haravan",
    "custom_haravan_orgid": 123456,
    "custom_myharavan": "demo-haravan.myharavan.com",
    "creation": "2024-05-10 10:00:00.000000",
    "owner": "Administrator",
    "modified_by": "Administrator"
  }
}
```

## 4. API Cập nhật khách hàng (Update)

Sử dụng phương thức `PUT` để cập nhật thông tin khi khách hàng đổi tên tổ chức, thay đổi domain myharavan hoặc các thông tin khác. Bạn cần truyền đúng ID của bản ghi (`name` - tức là `customer_name`) vào URL.

**Endpoint:**
```http
PUT https://haravandesk.s.frappe.cloud/api/resource/HD%20Customer/{name}
```
*Lưu ý: tham số `{name}` phải được URL Encode. Ví dụ nếu tên là `123456 - Cửa hàng Demo`, url sẽ là `123456%20-%20C%E1%BB%ADa%20h%C3%A0ng%20Demo`.*

**Payload (JSON):**
```json
{
  "custom_myharavan": "demo-new.myharavan.com",
  "custom_bitrix_company_id": "998877"
}
```

## 5. API Kiểm tra/Tìm kiếm (Search)

Để kiểm tra xem một khách hàng đã tồn tại trên Helpdesk hay chưa thông qua `orgid` trước khi tạo mới.

**Endpoint:**
```http
GET https://haravandesk.s.frappe.cloud/api/resource/HD%20Customer?filters=[["custom_haravan_orgid","=",123456]]&fields=["name","customer_name","custom_haravan_orgid"]
```

**Response:**
```json
{
  "data": [
    {
      "name": "123456 - Cửa hàng Demo Haravan",
      "customer_name": "123456 - Cửa hàng Demo Haravan",
      "custom_haravan_orgid": 123456
    }
  ]
}
```

## 6. Các điểm cần lưu ý khi đồng bộ

1. **Naming Convention:** Bắt buộc tuân thủ quy tắc đặt tên `"{orgid} - {orgname}"` cho trường `customer_name`. Logic link ticket, OAuth và Metajson Enrichment trên Frappe Helpdesk hiện đang dựa vào cấu trúc tên này để map đúng đối tượng.
2. **Rate Limit:** API chuẩn của Frappe bị giới hạn truy cập (rate limit) cấu hình trên Site. Tránh gọi hàng loạt (brute-force) mà nên gọi real-time khi có event thay đổi, hoặc cấu hình batch delay. Nếu cần đồng bộ hàng nghìn record một lúc, hãy trao đổi với team vận hành để tạm thời nới lỏng rate limit.
3. **Phân quyền User:** API Key phải gắn với User có cấp quyền `System Manager` hoặc Role có đủ quyền Create/Write/Read trên `HD Customer`. Tuyệt đối không dùng API Key của `Administrator`.
