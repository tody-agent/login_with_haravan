import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(defineConfig({
  title: "Haravan Helpdesk",
  description: "Tài liệu bàn giao Haravan Helpdesk — Cấu hình, vận hành, và hướng dẫn sử dụng",
  lang: 'vi-VN',
  lastUpdated: true,
  themeConfig: {
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: 'Tìm kiếm', buttonAriaLabel: 'Tìm kiếm' },
          modal: {
            noResultsText: 'Không tìm thấy kết quả',
            resetButtonTitle: 'Xóa tìm kiếm',
            footer: { selectText: 'Chọn', navigateText: 'Di chuyển', closeText: 'Đóng' }
          }
        }
      }
    },
    nav: [
      { text: 'Trang chủ', link: '/' },
      { text: 'Bắt đầu', link: '/getting-started/installation' },
      { text: 'Hướng dẫn KH', link: '/customer-guide/' },
      { text: 'Vận hành', link: '/operations/script-catalog' },
      { text: 'Kiến trúc', link: '/architecture/overview' },
      { text: 'Bàn giao', link: '/handover/handoff-sop' }
    ],
    sidebar: [
      {
        text: '📋 Tổng quan',
        collapsed: false,
        items: [
          { text: 'Trang chủ & Luồng đọc', link: '/' },
          { text: 'Tổng quan dự án', link: '/overview/project' },
          { text: 'Hiện trạng & Lộ trình', link: '/overview/roadmap' }
        ]
      },
      {
        text: '🚀 Bắt đầu',
        collapsed: false,
        items: [
          { text: 'Cài đặt & Thiết lập', link: '/getting-started/installation' },
          { text: 'Cấu hình OAuth Haravan', link: '/getting-started/oauth-setup' },
          { text: 'Cấu hình Site Config', link: '/getting-started/site-config' },
          { text: 'Triển khai production', link: '/getting-started/deployment' },
          { text: 'Khắc phục sự cố', link: '/getting-started/troubleshooting' }
        ]
      },
      {
        text: '👥 Hướng dẫn khách hàng',
        collapsed: true,
        items: [
          { text: 'Tổng quan KB', link: '/customer-guide/' },
          { text: '1. Đăng nhập portal', link: '/customer-guide/login' },
          { text: '2. Tổng quan portal', link: '/customer-guide/portal-overview' },
          { text: '3. Tạo yêu cầu hỗ trợ', link: '/customer-guide/create-ticket' },
          { text: '4. Viết yêu cầu hiệu quả', link: '/customer-guide/write-good-ticket' },
          { text: '5. Theo dõi yêu cầu', link: '/customer-guide/track-ticket' },
          { text: '6. Lịch sử yêu cầu', link: '/customer-guide/ticket-history' },
          { text: '7. Đánh giá & Mở lại', link: '/customer-guide/feedback-reopen' },
          { text: '8. Tạo bộ lọc riêng', link: '/customer-guide/custom-views' }
        ]
      },
      {
        text: '🔐 Phân quyền & User',
        collapsed: true,
        items: [
          { text: 'RBAC & Phân quyền', link: '/access-control/rbac' },
          { text: 'User, email & multi-org', link: '/access-control/user-cases' },
          { text: 'Cấp quyền nhân viên', link: '/access-control/employee-access' },
          { text: 'Phân quyền khách hàng', link: '/access-control/customer-permissions' }
        ]
      },
      {
        text: '⚙️ Vận hành Helpdesk',
        collapsed: false,
        items: [
          { text: 'Sổ đăng ký Script', link: '/operations/script-catalog' },
          { text: 'Audit Custom Fields', link: '/operations/custom-fields' },
          { text: 'HD Ticket Product Suggestion', link: '/operations/product-suggestion' },
          { text: 'Ghi đè giao diện tiếng Việt', link: '/operations/vietnamese-ui' }
        ]
      },
      {
        text: '🏗️ Kiến trúc & Data',
        collapsed: true,
        items: [
          { text: 'Tổng quan kiến trúc', link: '/architecture/overview' },
          { text: 'Luồng OAuth & Đăng nhập', link: '/architecture/oauth-flow' },
          { text: 'Data Model', link: '/architecture/data-model' },
          { text: 'Luồng dữ liệu & Đồng bộ', link: '/architecture/data-flow' },
          { text: 'Cơ sở dữ liệu', link: '/architecture/database' },
          { text: 'Lưu ý safe_exec', link: '/architecture/safe-exec' }
        ]
      },
      {
        text: '🔌 Tích hợp',
        collapsed: true,
        items: [
          { text: 'Bitrix Enrichment tổng quan', link: '/integrations/bitrix-overview' },
          { text: 'Customer Profile API', link: '/integrations/bitrix-customer-profile' },
          { text: 'Enrichment, Routing & Assignment', link: '/integrations/bitrix-routing' },
          { text: 'GitLab Integration', link: '/integrations/gitlab' },
          { text: 'AI Features', link: '/integrations/ai-features' }
        ]
      },
      {
        text: '📖 API Tham chiếu',
        collapsed: true,
        items: [
          { text: 'Import dữ liệu qua API', link: '/api/frappe-api-migration' },
          { text: 'Đồng bộ Khách hàng', link: '/api/customer-sync' },
          { text: 'Customer Profile API', link: '/api/customer-profile' },
          { text: 'Identity Sync API', link: '/api/identity-sync' },
          { text: 'OAuth Callback API', link: '/api/oauth-callback' }
        ]
      },
      {
        text: '📦 Bàn giao & Tham chiếu',
        collapsed: false,
        items: [
          { text: '✅ UAT & Bàn giao Interactive', link: '/handover/uat-interactive' },
          { text: 'SOP Bàn giao vận hành', link: '/handover/handoff-sop' },
          { text: 'Scripts Review Checklist', link: '/handover/scripts-review' },
          { text: 'Bản đồ User Story', link: '/handover/uat-user-story' },
          { text: 'Checklist UAT', link: '/handover/uat-checklist' },
          { text: 'Checklist bàn giao', link: '/handover/uat-ban-giao' }
        ]
      }
    ],
    outline: {
      level: [2, 3],
      label: 'Mục lục'
    },
    docFooter: {
      prev: 'Trang trước',
      next: 'Trang tiếp'
    },
    lastUpdated: {
      text: 'Cập nhật lần cuối'
    },
    returnToTopLabel: 'Về đầu trang'
  }
}))
