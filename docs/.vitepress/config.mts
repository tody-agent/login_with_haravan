import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(defineConfig({
  title: "Haravan Helpdesk",
  description: "Tài liệu bàn giao Haravan Helpdesk cho Frappe Helpdesk",
  lang: 'vi-VN',
  themeConfig: {
    nav: [
      { text: 'Trang chủ', link: '/' },
      { text: 'Bàn giao', link: '/about/handoff-roadmap' },
      { text: 'Vận hành', link: '/guide/getting-started' },
      { text: 'Kiến trúc', link: '/architecture/overview' },
      { text: 'API', link: '/api/oauth-callback' }
    ],
    sidebar: [
      {
        text: '1. Bắt đầu bàn giao',
        items: [
          { text: 'Tổng quan & luồng đọc', link: '/' },
          { text: 'Hiện trạng & lộ trình', link: '/about/handoff-roadmap' },
          { text: 'Bắt đầu & cấu hình OAuth', link: '/guide/getting-started' },
          { text: 'Triển khai production', link: '/guide/deployment' },
          { text: 'Khắc phục sự cố', link: '/guide/troubleshooting' }
        ]
      },
      {
        text: '2. Login, User & quyền',
        items: [
          { text: 'User, email & multi-org', link: '/guide/haravan-user-account-cases' },
          { text: 'Cấp quyền Portal/Desk', link: '/guide/haravan-employee-helpdesk-access' },
          { text: 'Luồng OAuth & đăng nhập', link: '/architecture/oauth-flow' },
          { text: 'API OAuth Callback', link: '/api/oauth-callback' },
          { text: 'API danh tính & tổ chức', link: '/api/identity-sync' }
        ]
      },
      {
        text: '3. Helpdesk data & agent workflow',
        items: [
          { text: 'Data model haravan.help', link: '/haravan-helpdesk-data-model' },
          { text: 'Customer Profile API', link: '/api/customer-profile' },
          { text: 'Metajson, Bitrix & Customer Profit', link: '/operations/metajson-bitrix-customer-profit-flow' },
          { text: 'HD Ticket Product Suggestion', link: '/guide/hd-ticket-product-suggestion' },
          { text: 'Sổ đăng ký Script', link: '/operations/script-registry' },
          { text: 'Ghi đè giao diện tiếng Việt', link: '/operations/vietnamese-ui-override' }
        ]
      },
      {
        text: '4. Kiến trúc hệ thống',
        items: [
          { text: 'Tổng quan kiến trúc', link: '/architecture/overview' },
          { text: 'Luồng dữ liệu & đồng bộ', link: '/architecture/data-flow' },
          { text: 'Cơ sở dữ liệu', link: '/architecture/database' }
        ]
      },
      {
        text: '5. Phụ lục kỹ thuật',
        items: [
          { text: 'Bitrix integration reference', link: '/bitrix_integration' },
          { text: 'Bitrix field mapping', link: '/bitrix_mapping' },
          { text: 'Bitrix MCP setup', link: '/bitrix_mcp_setup' }
        ]
      }
    ]
  }
}))
