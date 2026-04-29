---
title: Cơ sở dữ liệu
description: Cấu trúc cơ sở dữ liệu của ứng dụng Login With Haravan
keywords: database, schema, doctype, frappe
robots: index, follow
---

# 🗄️ Cơ sở dữ liệu

:::info Tóm tắt
Dữ liệu của Login With Haravan chủ yếu mở rộng từ các DocType có sẵn của Frappe/Helpdesk, cộng thêm `Haravan Account Link` để quản lý liên kết.
:::

## 1. Haravan Account Link (Custom DocType)
Lưu trữ thông tin liên kết giữa người dùng và tổ chức Haravan.
- `user` (Link - User): User ID trong Frappe.
- `haravan_userid` (Data): ID của người dùng trên Haravan.
- `haravan_orgid` (Data): ID tổ chức trên Haravan.
- `haravan_orgname` (Data): Tên tổ chức.
- `hd_customer` (Link - HD Customer): Khách hàng tương ứng trên Helpdesk.

## 2. HD Customer (Được mở rộng)
Ứng dụng thêm các **Custom Fields** vào `HD Customer`:
- `custom_haravan_orgid` (Int): Tránh trùng lặp, định danh duy nhất org.
- `custom_myharavan` (Data): Tên miền phụ (subdomain).
- `custom_bitrix_company_id` (Data): ID công ty trong Bitrix.
- `custom_bitrix_company_url` (Data): Link mở công ty trong Bitrix.
- `custom_bitrix_match_confidence` (Percent): Độ tin cậy khi liên kết dữ liệu.
- `custom_bitrix_sync_status` (Data): Trạng thái đồng bộ hồ sơ.
- `custom_bitrix_last_synced_at` (Datetime): Lần lấy dữ liệu Bitrix gần nhất.

## 3. Contact (Được tự động tạo)
- `email_id`: Email từ Haravan.
- Lồng với `HD Customer` trong child table `links`.
- Có thể lưu `custom_bitrix_contact_id`, `custom_bitrix_contact_url`, `custom_bitrix_last_synced_at` nếu match được Bitrix Contact.

## 4. HD Customer Data (Custom DocType)
Lưu snapshot có tổ chức cho dữ liệu lấy theo nhu cầu từ Bitrix.
- `hd_customer` (Link - HD Customer)
- `contact` (Link - Contact)
- `source`: `bitrix`
- `entity_type`: `company` hoặc `contact`
- `external_id`, `external_url`
- `summary_json`: Dữ liệu tóm tắt đã chuẩn hóa để hiển thị trong Customer Profile.
- `match_key`, `confidence`, `last_synced_at`
