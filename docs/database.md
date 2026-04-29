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
- `custom_shopplan_name` (Data): Gói dịch vụ (Scale, Growth,...).
- `custom_first_paid_date` (Datetime): Ngày thanh toán đầu tiên.

## 3. Contact (Được tự động tạo)
- `email_id`: Email từ Haravan.
- Lồng với `HD Customer` trong child table `links`.
