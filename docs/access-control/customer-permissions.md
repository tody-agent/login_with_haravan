# Phân quyền khách hàng

## Mô hình phân quyền portal

Khách hàng Haravan đăng nhập portal (`haravan.help`) được phân quyền dựa trên:

1. **Vai trò tài khoản Haravan** — Owner, Admin, hoặc Staff
2. **Liên kết orgid** — Tài khoản được map với orgid của cửa hàng Haravan
3. **Phạm vi ticket** — Mặc định chỉ thấy ticket mình tạo

## Quy tắc hiển thị ticket

| Vai trò | Thấy ticket | Tạo ticket | Reply |
|---|---|---|---|
| **Owner/Admin** cửa hàng | Tất cả ticket của cửa hàng | ✅ | ✅ |
| **Staff** cửa hàng | Chỉ ticket mình tạo | ✅ | ✅ |
| **Guest** (chưa đăng nhập) | Không | ❌ | ❌ |

## Cách Frappe xác định phân quyền portal

1. User đăng nhập → Frappe check `User Type`
2. Nếu `Website User` → portal mode → chỉ thấy ticket `raised_by == user.email`
3. Nếu có `HD Customer` link → mở rộng scope theo customer
4. Assignment Rule / User Permission **không ảnh hưởng** portal user

::: tip Multi-org
Nếu một người quản lý nhiều cửa hàng Haravan (nhiều orgid), họ sẽ thấy ticket của **tất cả** cửa hàng đã link với email của họ.
:::

## Tham chiếu

- [RBAC tổng quan](/access-control/rbac) — Phân quyền nội bộ
- [User, email & multi-org](/access-control/user-cases) — Edge cases
