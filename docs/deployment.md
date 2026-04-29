---
title: Triển khai (Deployment)
description: Hướng dẫn triển khai Login With Haravan lên Frappe Cloud
keywords: deployment, frappe cloud, bench
robots: index, follow
---

# 🚀 Triển khai (Deployment)

:::info Tóm tắt
Tài liệu hướng dẫn deploy app `login_with_haravan` lên môi trường Frappe Cloud và các lưu ý kỹ thuật.
:::

## 1. Yêu cầu hệ thống
- Frappe Framework v15+
- Frappe Helpdesk đã được cài đặt trên site.
- `bench` CLI.

## 2. Lệnh Build & Test
Trước khi đẩy code, hãy đảm bảo các test nội bộ vượt qua:
```bash
./test_gate.sh
# Hoặc
PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v
```

## 3. Triển khai Frappe Cloud
1. Cập nhật code lên branch `main` của repository GitHub.
2. Trên Frappe Cloud Dashboard, chuyển đến tab **Apps** của server/bench.
3. Nhấn **Update** để pull code mới nhất.
4. Chạy **Site Update** (migrate) để áp dụng các Custom Fields và schema mới.

Xem thêm `docs/DEPLOYMENT.md` để biết thêm chi tiết.
