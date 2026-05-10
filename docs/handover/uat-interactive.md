---
title: Checklist nghiệm thu & bàn giao
description: Checklist tương tác — tích chọn, ghi chú, lưu tiến độ trên trình duyệt, xuất báo cáo.
---

# ✅ Checklist nghiệm thu & bàn giao

Trang này giúp đội Haravan **kiểm tra từng bước** trước khi nhận bàn giao hệ thống Helpdesk tại [haravan.help](https://haravan.help).

- ✅ **Tích chọn** từng mục đã kiểm tra xong
- 📝 **Ghi chú** kết quả hoặc lỗi cho từng mục
- 💾 **Tự lưu** trên trình duyệt — mở lại vẫn còn
- 🔍 **Lọc** theo mức ưu tiên hoặc trạng thái
- 📋 **Xuất báo cáo** Markdown gửi cho team

::: tip Mức ưu tiên
- 🔴 **P0 — Chặn nghiệm thu:** Phải đạt 100% mới go-live.
- 🟡 **P1 — Quan trọng:** Nên xong trước go-live.
- 🔵 **P2 — Bổ sung:** Có thể làm sau go-live.
:::

<script setup>
const uatGroups = [
  {
    title: "Cấu hình domain & hạ tầng",
    icon: "🌐",
    description: "Domain, DNS, SSL và Frappe Cloud site phải sẵn sàng trước mọi bước khác.",
    items: [
      { id: "dom-01", label: "Domain support.haravan.com trỏ DNS đúng về Frappe Cloud", priority: "P0", category: "domain" },
      { id: "dom-02", label: "SSL certificate hoạt động — truy cập https://support.haravan.com không báo lỗi bảo mật", priority: "P0", category: "domain" },
      { id: "dom-03", label: "Frappe Cloud site slug haravandesk.s.frappe.cloud chạy bình thường", priority: "P0", category: "domain" },
      { id: "dom-04", label: "Custom domain đã liên kết trong Frappe Cloud Dashboard > Sites > Domain", priority: "P0", category: "domain" },
      { id: "dom-05", label: "Truy cập support.haravan.com/login hiển thị trang đăng nhập", priority: "P0", category: "domain" },
      { id: "dom-06", label: "Truy cập support.haravan.com/helpdesk hiển thị portal khách hàng", priority: "P0", category: "domain" },
      { id: "dom-06b", label: "Domain Freshdesk cũ trỏ về hotro.haravan.com để dự phòng", priority: "P0", category: "domain" },
      { id: "dom-07", label: "Gắn Google Analytics (GA4) — đã có mã tracking trên portal và trang login", priority: "P1", category: "domain" },
      { id: "dom-08", label: "GA4 đang nhận được dữ liệu realtime khi truy cập site", priority: "P1", category: "domain" }
    ]
  },
  {
    title: "Cấu hình email gửi & nhận",
    icon: "📧",
    description: "Email inbound (nhận), outbound (gửi), default sender phải hoạt động đúng.",
    items: [
      { id: "mail-01", label: "Email Account mặc định (Default Outgoing) đã cấu hình — kiểm tra tại Setup > Email Account", priority: "P0", category: "email" },
      { id: "mail-02", label: "Gửi email test từ hệ thống — khách hàng nhận được email", priority: "P0", category: "email" },
      { id: "mail-03", label: "Email gửi đi hiển thị đúng tên người gửi và địa chỉ reply-to", priority: "P0", category: "email" },
      { id: "mail-04", label: "Email Inbound (nhận vào) đã cấu hình — kiểm tra tại Setup > Email Account > Enable Incoming", priority: "P1", category: "email" },
      { id: "mail-05", label: "Khách gửi email reply → hệ thống nhận và tạo comment vào đúng ticket", priority: "P1", category: "email" },
      { id: "mail-06", label: "Email thông báo khi tạo ticket mới — khách nhận xác nhận tự động", priority: "P1", category: "email" },
      { id: "mail-07", label: "Email thông báo khi agent trả lời — khách nhận email phản hồi", priority: "P0", category: "email" },
      { id: "mail-08", label: "CC email hoạt động — thêm CC hợp lệ, người nhận CC nhận được email", priority: "P1", category: "email" },
      { id: "mail-09", label: "Email không vào spam — kiểm tra SPF/DKIM/DMARC nếu dùng domain riêng", priority: "P1", category: "email" },
      { id: "mail-10", label: "Nhập CC sai định dạng → hệ thống báo lỗi, không gửi sai", priority: "P2", category: "email" }
    ]
  },
  {
    title: "Cấu hình token & secret tích hợp",
    icon: "🔑",
    description: "Tất cả token, API key, webhook phải được lưu đúng nơi (Site Config server-side), không lộ ra trình duyệt.",
    items: [
      { id: "tok-01", label: "OAuth Haravan: client_id và client_secret đã nhập trong Site Config > haravan_account_login", priority: "P0", category: "token" },
      { id: "tok-02", label: "Bitrix webhook: bitrix_webhook_url đã nhập trong Site Config", priority: "P0", category: "token" },
      { id: "tok-03", label: "GitLab token: gitlab_token và gitlab_project_id đã nhập trong Site Config", priority: "P1", category: "token" },
      { id: "tok-04", label: "AI (Gemini): gemini_api_key đã nhập trong Site Config", priority: "P1", category: "token" },
      { id: "tok-05", label: "Social Login Key 'Login With Haravan' đã bật trong Frappe Desk", priority: "P0", category: "token" },
      { id: "tok-06", label: "Helpdesk Integrations Settings: Bitrix bật, các field webhook/portal/timeout đã điền", priority: "P0", category: "token" },
      { id: "tok-07", label: "Kiểm tra browser devtools — không thấy secret, token, webhook URL trong response", priority: "P0", category: "token" },
      { id: "tok-08", label: "Chạy API diagnostics xác nhận oauth_configured=true, bitrix_configured=true", priority: "P1", category: "token" },
      { id: "tok-09", label: "GA4 Measurement ID đã gắn đúng (nếu dùng server-side hoặc gtag)", priority: "P1", category: "token" }
    ]
  },
  {
    title: "Migration dữ liệu từ Freshdesk",
    icon: "📦",
    description: "Kiểm tra dữ liệu đã được chuyển từ Freshdesk sang Helpdesk an toàn và đầy đủ.",
    items: [
      { id: "mig-01", label: "Dữ liệu Customer (Tên, Email, Điện thoại, OrgID) đã được import đầy đủ", priority: "P0", category: "migration" },
      { id: "mig-02", label: "Dữ liệu Open Tickets từ Freshdesk đã được tạo mới trên Frappe Helpdesk", priority: "P0", category: "migration" },
      { id: "mig-03", label: "Ticket import có đầy đủ nội dung mô tả, attachment và lịch sử phản hồi", priority: "P1", category: "migration" },
      { id: "mig-04", label: "Ticket đã đóng trên Freshdesk được lưu trữ an toàn hoặc import dưới dạng Closed", priority: "P2", category: "migration" },
      { id: "mig-05", label: "Mapping đúng người phụ trách (assignee) đối với open tickets", priority: "P1", category: "migration" }
    ]
  },
  {
    title: "Đăng nhập Haravan",
    icon: "🔐",
    description: "Khách hàng dùng tài khoản Haravan để vào portal — không cần tạo mật khẩu riêng.",
    items: [
      { id: "lg-01", label: "Trang login có nút 'Đăng nhập bằng Haravan' hiển thị rõ ràng", priority: "P0", category: "login" },
      { id: "lg-02", label: "Bấm nút → chuyển đến accounts.haravan.com với redirect_uri đúng", priority: "P0", category: "login" },
      { id: "lg-03", label: "Haravan Partner Dashboard: callback URL khớp chính xác https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan", priority: "P0", category: "login" },
      { id: "lg-04", label: "Scope OAuth gồm: openid profile email org userinfo", priority: "P0", category: "login" },
      { id: "lg-05", label: "Owner đăng nhập → vào portal Helpdesk (không vào Desk nội bộ)", priority: "P0", category: "login" },
      { id: "lg-06", label: "Admin đăng nhập → vào portal Helpdesk", priority: "P0", category: "login" },
      { id: "lg-07", label: "Staff đăng nhập → vào portal Helpdesk", priority: "P0", category: "login" },
      { id: "lg-08", label: "Đăng nhập xong → Haravan Account Link có đúng email, user ID, org ID, org name", priority: "P0", category: "login" },
      { id: "lg-09", label: "Đăng nhập thất bại → có thông báo lỗi rõ ràng, không trắng trang", priority: "P1", category: "login" },
      { id: "lg-10", label: "Error Log ghi đủ thông tin lỗi để debug (thiếu email, sai redirect...)", priority: "P1", category: "login" }
    ]
  },
  {
    title: "Tạo tài khoản tự động",
    icon: "👤",
    description: "Lần đầu đăng nhập, hệ thống tự tạo User, Contact, HD Customer, Haravan Account Link.",
    items: [
      { id: "rg-01", label: "Email mới chưa có trong Frappe → đăng nhập → tạo User (website user)", priority: "P0", category: "register" },
      { id: "rg-02", label: "Tự tạo Contact theo email", priority: "P0", category: "register" },
      { id: "rg-03", label: "Tự tạo HD Customer theo tổ chức Haravan", priority: "P0", category: "register" },
      { id: "rg-04", label: "Tự tạo Haravan Account Link (email, user ID, org ID)", priority: "P0", category: "register" },
      { id: "rg-05", label: "Email đã có User → đăng nhập không tạo trùng, chỉ cập nhật mapping", priority: "P0", category: "register" },
      { id: "rg-06", label: "Tài khoản thuộc 2 tổ chức → có HD Customer và Link cho cả 2 org", priority: "P1", category: "register" },
      { id: "rg-07", label: "Multi-org: tạo ticket → chọn được đúng tổ chức", priority: "P1", category: "register" }
    ]
  },
  {
    title: "Tạo yêu cầu hỗ trợ (ticket)",
    icon: "🎫",
    description: "Khách tạo ticket đúng form, đúng tổ chức, đính kèm được file.",
    items: [
      { id: "tk-01", label: "Khách mở được trang tạo ticket sau khi đăng nhập", priority: "P0", category: "ticket" },
      { id: "tk-02", label: "Form hiển thị đúng template (HD Ticket Template - Default)", priority: "P0", category: "ticket" },
      { id: "tk-03", label: "Nhập tiêu đề + mô tả + chọn loại vấn đề → gửi → có mã ticket", priority: "P0", category: "ticket" },
      { id: "tk-04", label: "Bỏ trống trường bắt buộc → báo lỗi rõ, không tạo ticket rỗng", priority: "P0", category: "ticket" },
      { id: "tk-05", label: "Đính kèm ảnh/PDF → upload thành công → agent xem/tải được", priority: "P1", category: "ticket" },
      { id: "tk-06", label: "Agent mở ticket → thấy đúng tiêu đề, nội dung, người gửi, tổ chức", priority: "P0", category: "ticket" },
      { id: "tk-07", label: "Staff tạo ticket → chỉ thấy ticket của mình, không thấy của người khác", priority: "P0", category: "ticket" }
    ]
  },
  {
    title: "Phân tuyến & giao ticket cho đúng team",
    icon: "🔀",
    description: "Đây là phần quan trọng nhất — ticket phải đến đúng phòng ban/team dựa trên segment, partner, shopplan.",
    items: [
      { id: "rt-01", label: "Ticket tự gắn đúng HD Customer theo org người tạo", priority: "P0", category: "routing" },
      { id: "rt-02", label: "Org ID trên ticket khớp với Haravan org của khách", priority: "P0", category: "routing" },
      { id: "rt-03", label: "Khách SME (không có Bitrix evidence) → ticket vào team CS 60p", priority: "P0", category: "routing" },
      { id: "rt-04", label: "Khách Medium + shopplan Scale → ticket vào team Medium - Scale", priority: "P0", category: "routing" },
      { id: "rt-05", label: "Khách Medium + shopplan Grow → ticket vào team Medium - Grow", priority: "P0", category: "routing" },
      { id: "rt-06", label: "Khách có Partner service → ticket vào team Partner tương ứng", priority: "P0", category: "routing" },
      { id: "rt-07", label: "Service group = Ecom + có Bitrix evidence → ticket vào team Service Ecom", priority: "P0", category: "routing" },
      { id: "rt-08", label: "Service group = Ecom nhưng thiếu evidence → fallback về CS 60p (không route nhầm)", priority: "P0", category: "routing" },
      { id: "rt-09", label: "Bitrix không có dữ liệu hoặc timeout → ticket vẫn tạo, fallback CS 60p", priority: "P0", category: "routing" },
      { id: "rt-10", label: "Agent đã gán team thủ công → routing script không ghi đè", priority: "P1", category: "routing" },
      { id: "rt-11", label: "custom_haravan_routing_reason ghi rõ lý do route (Auto-routed / Fallback / Manual)", priority: "P1", category: "routing" },
      { id: "rt-12", label: "Assignment Rule ưu tiên: Partner (cao nhất) > Medium Scale (300) > Medium Grow (200) > CS 60p (100)", priority: "P0", category: "routing" },
      { id: "rt-13", label: "Ticket gán xong → agent nhận ToDo phân công", priority: "P0", category: "routing" },
      { id: "rt-14", label: "Round-robin: ticket chia đều giữa các agent trong cùng team", priority: "P1", category: "routing" },
      { id: "rt-15", label: "Multi-org: chọn org A → gắn customer org A; chọn org B → gắn customer org B", priority: "P1", category: "routing" },
      { id: "rt-16", label: "Product Suggestion: chọn gợi ý sản phẩm → ticket lưu đúng product_line, product_feature", priority: "P1", category: "routing" },
      { id: "rt-17", label: "Bitrix responsible: custom_responsible cập nhật khi Bitrix trả user active có email", priority: "P1", category: "routing" },
      { id: "rt-18", label: "Bitrix responsible inactive/thiếu email → không ghi sai, chỉ báo trạng thái", priority: "P1", category: "routing" }
    ]
  },
  {
    title: "Xử lý & đóng ticket",
    icon: "✉️",
    description: "Agent trả lời, đóng ticket — khách thấy trạng thái đúng trên portal.",
    items: [
      { id: "cl-01", label: "Agent mở ticket → gửi phản hồi → phản hồi lưu trong timeline", priority: "P0", category: "close" },
      { id: "cl-02", label: "Khách mở portal → thấy phản hồi mới từ agent", priority: "P0", category: "close" },
      { id: "cl-03", label: "Agent chuyển trạng thái → đóng/resolved thành công", priority: "P0", category: "close" },
      { id: "cl-04", label: "Khách mở portal → ticket hiển thị đã đóng", priority: "P0", category: "close" },
      { id: "cl-05", label: "Lọc ticket theo trạng thái → ticket nằm đúng nhóm", priority: "P1", category: "close" },
      { id: "cl-06", label: "Ghi chú nội bộ (internal note) → khách không thấy", priority: "P1", category: "close" }
    ]
  },
  {
    title: "Phân quyền xem ticket",
    icon: "🛡️",
    description: "Owner/admin xem ticket cả tổ chức — staff chỉ xem ticket mình tạo.",
    items: [
      { id: "pr-01", label: "Owner tạo ticket → admin cùng org thấy ticket đó trên portal", priority: "P0", category: "permission" },
      { id: "pr-02", label: "Admin tạo ticket → owner cùng org thấy ticket đó", priority: "P0", category: "permission" },
      { id: "pr-03", label: "Staff tạo ticket → chỉ staff đó thấy, không thấy ticket người khác", priority: "P0", category: "permission" },
      { id: "pr-04", label: "Agent nội bộ chỉ thấy ticket team mình (User Permission theo HD Team)", priority: "P1", category: "permission" },
      { id: "pr-05", label: "Manager thấy ticket tất cả team trong department", priority: "P1", category: "permission" },
      { id: "pr-06", label: "Admin hệ thống thấy tất cả ticket", priority: "P0", category: "permission" }
    ]
  },
  {
    title: "Tích hợp Bitrix, GitLab, AI",
    icon: "🔌",
    description: "Các hệ thống bên ngoài hoạt động đúng và bảo mật.",
    items: [
      { id: "in-01", label: "Agent bấm 'Xem hồ sơ khách hàng' → popup hiển thị dữ liệu Bitrix (công ty, segment, shopplan)", priority: "P1", category: "integration" },
      { id: "in-02", label: "Popup Bitrix: bấm refresh → trạng thái rõ (cached / not_found / matched)", priority: "P2", category: "integration" },
      { id: "in-03", label: "Popup Bitrix: bấm đồng bộ → customer/ticket cập nhật đúng", priority: "P1", category: "integration" },
      { id: "in-04", label: "GitLab: tạo issue từ ticket → label, assignee prefill đúng theo Product Suggestion", priority: "P2", category: "integration" },
      { id: "in-05", label: "AI phân tích (nếu bật): trả kết quả hữu ích, không mất nội dung ticket gốc", priority: "P2", category: "integration" },
      { id: "in-06", label: "AI lỗi cấu hình → báo lỗi rõ ràng, không ảnh hưởng các tính năng khác", priority: "P2", category: "integration" }
    ]
  },
  {
    title: "Bàn giao quyền truy cập",
    icon: "📋",
    description: "Chuyển giao tài khoản, quyền quản trị cho đội Haravan.",
    items: [
      { id: "ho-01", label: "Chuyển quyền Frappe Cloud site admin → Haravan", priority: "P0", category: "handover" },
      { id: "ho-02", label: "Chuyển quyền Frappe Desk admin (cấu hình Helpdesk, template, user)", priority: "P0", category: "handover" },
      { id: "ho-03", label: "Chuyển quyền Haravan Partner Dashboard (quản lý OAuth app)", priority: "P0", category: "handover" },
      { id: "ho-04", label: "Chuyển quyền GitHub repo (hoặc fork)", priority: "P1", category: "handover" },
      { id: "ho-05", label: "Chuyển quyền Bitrix webhook owner", priority: "P1", category: "handover" },
      { id: "ho-06", label: "Chuyển quyền GitLab project (nếu dùng)", priority: "P2", category: "handover" },
      { id: "ho-07", label: "Tạo tài khoản Helpdesk agent cho từng nhân viên CS", priority: "P0", category: "handover" }
    ]
  },
  {
    title: "Bàn giao vận hành & tài liệu",
    icon: "📖",
    description: "Đội Haravan nắm được cách cấu hình, test lại, và khi nào gọi kỹ thuật.",
    items: [
      { id: "cfg-01", label: "Hướng dẫn mở HD Ticket Template - Default để chỉnh form ticket", priority: "P0", category: "docs" },
      { id: "cfg-02", label: "Hướng dẫn thêm/sửa HD Ticket Product Suggestion", priority: "P1", category: "docs" },
      { id: "cfg-03", label: "Hướng dẫn thêm agent mới, gán Role Profile, User Permission", priority: "P0", category: "docs" },
      { id: "cfg-04", label: "Hướng dẫn chạy smoke test 8 bước sau khi đổi cấu hình", priority: "P0", category: "docs" },
      { id: "cfg-05", label: "Team đã đọc tài liệu Tổng quan dự án", priority: "P1", category: "docs" },
      { id: "cfg-06", label: "Team đã đọc tài liệu Enrichment Routing (luồng phân tuyến)", priority: "P1", category: "docs" },
      { id: "cfg-07", label: "Team biết danh sách 9 tình huống cần gọi đội kỹ thuật", priority: "P0", category: "docs" },
      { id: "cfg-08", label: "Knowledge Base cho khách hàng đã publish (hướng dẫn đăng nhập, tạo ticket...)", priority: "P1", category: "docs" },
      { id: "cfg-09", label: "Giao diện tiếng Việt đã override đúng (bản dịch CSV importable)", priority: "P1", category: "docs" },
      { id: "cfg-10", label: "SOP bàn giao vận hành đã được review và ký nhận", priority: "P0", category: "docs" }
    ]
  },
  {
    title: "Bảo mật & biên bản",
    icon: "🔒",
    description: "Kiểm tra bảo mật cuối cùng và ký biên bản nghiệm thu.",
    items: [
      { id: "sec-01", label: "Không lộ client secret trên trình duyệt, tài liệu, hoặc ticket", priority: "P0", category: "security" },
      { id: "sec-02", label: "Không lộ Bitrix webhook URL/token trên trình duyệt", priority: "P0", category: "security" },
      { id: "sec-03", label: "Ticket test đều có tiền tố [UAT] để dễ dọn dẹp", priority: "P2", category: "security" },
      { id: "sec-04", label: "Biên bản nghiệm thu đã ký (đại diện Haravan + kỹ thuật + PM)", priority: "P0", category: "security" },
      { id: "sec-05", label: "Danh sách lỗi còn mở và ngoại lệ đã thống nhất bằng văn bản", priority: "P0", category: "security" }
    ]
  }
]
</script>

<UatChecklist :groups="uatGroups" storage-key="haravan-helpdesk-uat-v2" />

## Tài liệu tham chiếu

| Tài liệu | Dùng khi nào |
|---|---|
| [Bản đồ User Story](/uat-handoff/01-ban-do-user-story) | Xem chi tiết câu chuyện người dùng |
| [Checklist UAT chi tiết](/uat-handoff/02-checklist-uat) | Kịch bản test từng bước |
| [Checklist bàn giao chi tiết](/uat-handoff/03-checklist-ban-giao) | Bàn giao quyền, cấu hình, tích hợp |
| [SOP vận hành](/handover/handoff-sop) | Quy trình hàng ngày, xử lý sự cố |
| [Cấu hình Site Config](/getting-started/site-config) | Chi tiết các key cấu hình token/secret |
| [Luồng phân tuyến](/integrations/bitrix-routing) | Assignment rules, routing logic chi tiết |
| [Phân quyền RBAC](/access-control/rbac) | Role profile, user permission |
