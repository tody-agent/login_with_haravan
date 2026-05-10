# Phân quyền & RBAC

## Tổng quan mô hình phân quyền

Haravan Helpdesk sử dụng mô hình **RBAC (Role-Based Access Control)** của Frappe, mở rộng bằng:
- **Role Profile** theo quy ước tên `HD-{Department}-{Level}`
- **User Permission** để giới hạn dữ liệu theo department/team
- **Assignment Rule** để tự động phân ticket theo `agent_group`

## Role Profile Naming Convention

```
HD-{Department}-{Level}
```

| Department | Level | Role Profile | Ví dụ |
|---|---|---|---|
| CS | Agent | `HD-CS-Agent` | Agent xử lý ticket CS thường |
| CS | Manager | `HD-CS-Manager` | Quản lý team CS |
| Ecom | Agent | `HD-Ecom-Agent` | Agent xử lý ticket Ecom |
| Ecom | Manager | `HD-Ecom-Manager` | Quản lý team Ecom |
| Admin | Admin | `HD-Admin` | Quản trị toàn hệ thống |

## Ma trận quyền chi tiết

### Quyền theo vai trò

| Tính năng | Agent | Manager | Admin |
|---|---|---|---|
| Xem ticket team mình | ✅ | ✅ | ✅ |
| Xem ticket tất cả team | ❌ | ✅ | ✅ |
| Xử lý / reply ticket | ✅ | ✅ | ✅ |
| Chuyển ticket sang team khác | ✅ | ✅ | ✅ |
| Quản lý agent trong team | ❌ | ✅ | ✅ |
| Cấu hình Assignment Rule | ❌ | ❌ | ✅ |
| Quản lý Server Script | ❌ | ❌ | ✅ |
| Xem Error Log | ❌ | ❌ | ✅ |
| Quản lý Site Config | ❌ | ❌ | ✅ |

### User Permission Matrix

| Cần giới hạn | DocType filter | Mô tả |
|---|---|---|
| Team ticket | `HD Team` → agent_group | Agent chỉ thấy ticket team mình |
| Department | `Department` | Manager thấy tất cả ticket trong department |
| Full access | _(không set)_ | Admin thấy tất cả |

## Cấp quyền cho agent mới

### Bước 1: Tạo User

1. Vào **Setup > User** → **Add User**
2. Nhập email, tên agent
3. Set **User Type** = `System User`

### Bước 2: Gán Role Profile

1. Vào tab **Roles** của User
2. Chọn **Role Profile** phù hợp (ví dụ: `HD-CS-Agent`)
3. Role Profile sẽ tự động gán tất cả role cần thiết

### Bước 3: Set User Permission (nếu cần giới hạn team)

1. Vào **Setup > User Permission** → **Add**
2. User: _(agent email)_
3. Allow: `HD Team`
4. For Value: _(tên team, ví dụ: "CS 60p")_

### Bước 4: Thêm vào HD Team

1. Vào **Helpdesk > HD Team** → chọn team
2. Thêm agent vào danh sách member
3. Save

## Assignment Rule và Routing

Ticket được route tự động theo `agent_group`:

| Rule | Priority | Điều kiện | Team |
|---|---|---|---|
| Partner - ... - Support Rotation | Cao nhất | `agent_group == "Partner - ..."` | Partner team |
| AR02 - SME 9M Scale | 300 | `agent_group == "Medium - Scale"` | Medium Scale team |
| AR03 - SME 9M Grow | 200 | `agent_group == "Medium - Grow"` | Medium Grow team |
| AR04 - CS60p Fallback | 100 | `agent_group == "CS 60p"` | CS 60p (mặc định) |

::: info Fallback rule
Nếu không xác định được team, ticket **luôn** fallback về `CS 60p`.
:::

## Kiểm tra phân quyền

1. Đăng nhập bằng tài khoản agent cần kiểm tra
2. Vào **Helpdesk > HD Ticket** — chỉ nên thấy ticket team mình
3. Thử chuyển ticket — phải có quyền write
4. Kiểm tra **User Permission** nếu agent thấy quá nhiều/ít ticket

## Tham chiếu

- [Cấp quyền Portal/Desk cho nhân viên](/access-control/employee-access)
- [User, email & multi-org](/access-control/user-cases)
- [Phân quyền khách hàng](/access-control/customer-permissions)
