---
layout: home

hero:
  name: "Haravan Helpdesk"
  text: "Tài liệu bàn giao & vận hành"
  tagline: Hệ thống hỗ trợ khách hàng đa kênh trên nền tảng Frappe Helpdesk
  actions:
    - theme: brand
      text: Bắt đầu cài đặt
      link: /getting-started/installation
    - theme: alt
      text: Hướng dẫn người dùng
      link: /customer-guide/

features:
  - title: 🧑‍💻 Developer
    details: Cài đặt, kiến trúc hệ thống, data model và safe_exec.
    link: /architecture/overview
  - title: 👨‍💼 Admin / IT
    details: Cấu hình OAuth, phân quyền RBAC và quản trị Site Config.
    link: /getting-started/site-config
  - title: 🎧 Agent / CS
    details: Kịch bản vận hành, xử lý ticket, script catalog và routing.
    link: /operations/script-catalog
  - title: 🏪 Khách hàng
    details: Hướng dẫn sử dụng portal hỗ trợ, tạo và theo dõi ticket.
    link: /customer-guide/
  - title: 📋 PM / QA
    details: Quy trình bàn giao, UAT checklist và Script review.
    link: /handover/handoff-sop
  - title: 🔌 Tích hợp
    details: Luồng đồng bộ Bitrix, GitLab và các tính năng AI.
    link: /integrations/bitrix-routing
---

<style>
.info-box {
  background: var(--vp-c-bg-soft);
  border-radius: 12px;
  padding: 24px;
  margin: 48px auto;
  max-width: 800px;
}
.info-grid {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 12px 24px;
  font-size: 0.95em;
  margin-bottom: 0;
}
.info-grid dt { font-weight: 600; color: var(--vp-c-text-1); display: flex; align-items: center; gap: 8px;}
.info-grid dd { margin: 0; color: var(--vp-c-text-2); }
</style>

<div class="info-box">
  <dl class="info-grid">
    <dt>🌐 Production</dt>
    <dd><a href="https://haravan.help" target="_blank">haravan.help</a></dd>
    <dt>☁️ Frappe Cloud</dt>
    <dd><code>haravandesk.s.frappe.cloud</code></dd>
    <dt>📦 Custom App</dt>
    <dd><code>login_with_haravan</code></dd>
    <dt>🔗 GitHub</dt>
    <dd><a href="https://github.com/tody-agent/login_with_haravan" target="_blank">tody-agent/login_with_haravan</a></dd>
  </dl>
</div>

<div style="max-width: 800px; margin: 0 auto;">

## ⚠️ Quy tắc bảo mật

::: danger TUYỆT ĐỐI KHÔNG
- Lưu secret (API key, client secret, webhook URL) trong code, docs, hoặc Git
- Expose config nhạy cảm qua client-side script
- Dùng `ignore_permissions=True` mà không có permission gate
:::

::: tip AN TOÀN
- Mọi secret lưu trong **[Frappe Cloud Site Config](/getting-started/site-config)**
- Kiểm tra trạng thái qua **Diagnostics API** (tự mask secret)
- Backup script trước khi sửa, test trên staging trước
:::

</div>
