import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(defineConfig({
  title: "Frappe x Haravan",
  description: "Tài liệu Frappe x Haravan cho Frappe Helpdesk",
  lang: 'vi-VN',
  themeConfig: {
    nav: [
      { text: 'Trang chủ', link: '/' },
      { text: 'Bắt đầu', link: '/guide/getting-started' },
      { text: 'Kiến trúc', link: '/architecture/overview' },
      { text: 'API', link: '/api/oauth-callback' }
    ],
    sidebar: [
      {
        text: 'Giới thiệu',
        items: [
          { text: 'Tổng quan dự án', link: '/' },
          { text: 'Bàn giao & Lộ trình', link: '/about/handoff-roadmap' }
        ]
      },
      {
        text: 'Hướng dẫn vận hành',
        items: [
          { text: 'Bắt đầu & Cấu hình', link: '/guide/getting-started' },
          { text: 'Triển khai lên Production', link: '/guide/deployment' },
          { text: 'Khắc phục sự cố', link: '/guide/troubleshooting' }
        ]
      },
      {
        text: 'Kiến trúc hệ thống',
        items: [
          { text: 'Tổng quan kiến trúc', link: '/architecture/overview' },
          { text: 'Luồng OAuth & Đăng nhập', link: '/architecture/oauth-flow' },
          { text: 'Luồng dữ liệu & Đồng bộ', link: '/architecture/data-flow' },
          { text: 'Cơ sở dữ liệu', link: '/architecture/database' }
        ]
      },
      {
        text: 'Tham chiếu API',
        items: [
          { text: 'OAuth Callback', link: '/api/oauth-callback' },
          { text: 'Danh tính & Tổ chức', link: '/api/identity-sync' },
          { text: 'Hồ sơ khách hàng', link: '/api/customer-profile' }
        ]
      },
      {
        text: 'Vận hành nâng cao',
        items: [
          { text: 'Sổ đăng ký Script', link: '/operations/script-registry' },
          { text: 'Ghi đè giao diện tiếng Việt', link: '/operations/vietnamese-ui-override' }
        ]
      }
    ]
  }
}))
