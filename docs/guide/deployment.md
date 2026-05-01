---
title: Triển khai lên Production
description: Quy trình end-to-end từ viết code, đẩy lên GitHub, đến deploy lên Frappe Cloud.
keywords: triển khai, deployment, github, frappe cloud, migrate
robots: index, follow
---

# 🚀 Triển khai lên Production

:::info Mục tiêu
Hướng dẫn quy trình end-to-end từ lúc Developer viết code trên máy cá nhân, đẩy lên GitHub, đến cập nhật và deploy ứng dụng trên Frappe Cloud.
:::

## Giai đoạn 1: Lập trình & Kiểm thử (Local)

### 1.1. Viết code

- **Logic & API:** Viết mới hoặc sửa tại `login_with_haravan/engines/` hoặc `oauth.py`.
- **Database Schema:** Nếu cần thêm Custom Field vào `HD Customer`, định nghĩa trong `login_with_haravan/setup/install.py` qua hook `after_migrate`. Khi deploy, lệnh migrate sẽ tự động tạo trường mà không cần thao tác tay.

### 1.2. Kiểm thử

Trước khi push code, **bắt buộc** chạy test cục bộ:

```bash
# Chạy Unit Tests
PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v
```

Nếu source code có `./test_gate.sh`, hãy chạy nó để kiểm tra đầy đủ hơn (lint, compile, wheel build).

## Giai đoạn 2: Quản lý phiên bản (GitHub)

Frappe Cloud kéo code trực tiếp từ GitHub, do đó việc cập nhật GitHub là bắt buộc.

### 2.1. Ship code

Sau khi test pass trên local:

```bash
npm run ship
```

Lệnh `ship.sh` sẽ tự động:
1. Chạy test gate (pre-push hook)
2. Push nhánh hiện tại lên remote
3. Merge về `main`
4. Push `main`

:::warning Quy tắc nhánh
Không push trực tiếp lên `main` khi đang làm feature/fix branch. Luôn dùng `npm run ship` để đảm bảo an toàn.
:::

## Giai đoạn 3: Triển khai trên Frappe Cloud

Frappe Cloud chia làm 2 cấp: **Bench** (chứa mã nguồn App) và **Site** (chứa database từng khách hàng).

### 3.1. Thêm App lần đầu

Nếu `Frappe x Haravan` chưa có trên Frappe Cloud:

1. Đăng nhập [Frappe Cloud Dashboard](https://frappecloud.com/dashboard).
2. Vào tab **Apps** → chọn **New App**.
3. Chọn **GitHub** → tìm repo `tody-agent/login_with_haravan`, nhánh `main`.
4. Nhấn **Validate** để Frappe Cloud kiểm tra (`hooks.py`, `setup.py`).
5. Thêm App vào Bench đang chạy phiên bản Frappe tương ứng.

### 3.2. Cập nhật App đã có

1. Mở Frappe Cloud Dashboard.
2. Vào **Benches** → chọn Bench chứa app.
3. Chuyển sang tab **Apps**.
4. Nhấn **Update** (hoặc Fetch Updates) để Bench pull commit mới nhất từ `main`.

### 3.3. Chạy Migration cho Site

Sau khi Bench có mã nguồn mới, database trên Site vẫn là phiên bản cũ. Cần chạy **Migrate**:

1. Từ Frappe Cloud, vào tab **Sites**.
2. Chọn site đích (ví dụ: `haravandesk.s.frappe.cloud`).
3. Nhấn nút **Update** (hoặc Deploy / Migrate).
4. Tiến trình sẽ:
   - Đưa site vào chế độ bảo trì (Maintenance Mode).
   - Cập nhật mã nguồn mới nhất từ Bench.
   - Chạy `bench migrate` — kích hoạt hook `after_migrate` trong `install.py` để tạo/cập nhật bảng DB.
   - Dọn cache và khởi động lại dịch vụ.

:::tip Kiểm tra lịch sử Deploy
Nếu sau Update mà tính năng mới không chạy, vào tab **Jobs** của Site trên Frappe Cloud để xem log chi tiết `bench migrate` — tìm lỗi cú pháp Python hoặc lỗi SQL bị từ chối.
:::
