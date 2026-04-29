import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(defineConfig({
  title: "Login With Haravan",
  description: "Tài liệu tích hợp đăng nhập Haravan cho Frappe Helpdesk",
  lang: 'vi-VN',
  themeConfig: {
    nav: [
      { text: 'Trang chủ', link: '/' },
      { text: 'Hướng dẫn', link: '/guide/configuration' },
      { text: 'Kiến trúc', link: '/architecture/overview' },
      { text: 'API', link: '/api/oauth' }
    ],
    sidebar: [
      {
        text: 'Tổng quan',
        items: [
          { text: 'Giới thiệu', link: '/' },
          { text: 'Kế hoạch & Bàn giao', link: '/about/plan' }
        ]
      },
      {
        text: 'Hướng dẫn (Guide)',
        items: [
          { text: 'Cấu hình Haravan', link: '/guide/configuration' },
          { text: 'Khắc phục sự cố', link: '/guide/troubleshooting' },
          { text: 'Triển khai (Deployment)', link: '/guide/deployment' }
        ]
      },
      {
        text: 'Kiến trúc & Hệ thống',
        items: [
          { text: 'Tổng quan Kiến trúc', link: '/architecture/overview' },
          { text: 'Cơ sở dữ liệu', link: '/architecture/database' },
          { text: 'Luồng dữ liệu (Data Flow)', link: '/architecture/data-flow' },
          { text: 'Luồng OAuth (OAuth Flow)', link: '/architecture/oauth-flow' },
          { text: 'Luồng đăng nhập (UX)', link: '/architecture/login-flow' }
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
