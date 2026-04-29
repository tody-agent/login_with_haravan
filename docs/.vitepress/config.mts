import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(defineConfig({
  title: "Login With Haravan",
  description: "Tài liệu tích hợp đăng nhập Haravan cho Frappe Helpdesk",
  lang: 'vi-VN',
  themeConfig: {
    nav: [
      { text: 'Trang chủ', link: '/' },
      { text: 'Kiến trúc', link: '/architecture' },
      { text: 'Cấu hình', link: '/CONFIGURATION' },
      { text: 'API', link: '/api/oauth' }
    ],
    sidebar: [
      {
        text: 'Tổng quan',
        items: [
          { text: 'Giới thiệu', link: '/' },
          { text: 'Kế hoạch Helpdesk', link: '/frappe-helpdesk-plan' },
          { text: 'Kiến trúc hệ thống', link: '/architecture' },
          { text: 'Cơ sở dữ liệu', link: '/database' },
          { text: 'Luồng dữ liệu (Data Flow)', link: '/data-flow' },
          { text: 'Triển khai (Deployment)', link: '/deployment' }
        ]
      },
      {
        text: 'Hướng dẫn',
        items: [
          { text: 'Cấu hình Haravan', link: '/CONFIGURATION' },
          { text: 'Khắc phục sự cố', link: '/TROUBLESHOOTING' }
        ]
      },
      {
        text: 'API Reference',
        items: [
          { text: 'OAuth Callback', link: '/api/oauth' },
          { text: 'Identity Sync', link: '/api/identity' }
        ]
      }
    ]
  }
}))
