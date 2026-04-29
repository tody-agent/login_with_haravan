import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "Login With Haravan",
  description: "Tài liệu tích hợp đăng nhập Haravan cho Frappe Helpdesk",
  srcDir: '../docs',
  lang: 'vi-VN',
  themeConfig: {
    nav: [
      { text: 'Trang chủ', link: '/' },
      { text: 'Kiến trúc', link: '/architecture' },
      { text: 'SOPs', link: '/sop/installation' },
      { text: 'API', link: '/api/oauth' }
    ],
    sidebar: [
      {
        text: 'Tổng quan',
        items: [
          { text: 'Giới thiệu', link: '/' },
          { text: 'Kiến trúc hệ thống', link: '/architecture' },
          { text: 'Cơ sở dữ liệu', link: '/database' },
          { text: 'Luồng dữ liệu (Data Flow)', link: '/data-flow' },
          { text: 'Triển khai (Deployment)', link: '/deployment' }
        ]
      },
      {
        text: 'SOP & Hướng dẫn',
        items: [
          { text: 'Cài đặt', link: '/sop/installation' },
          { text: 'Cấu hình Haravan', link: '/CONFIGURATION' },
          { text: 'Khắc phục sự cố', link: '/TROUBLESHOOTING' }
        ]
      },
      {
        text: 'Nghiên cứu UX',
        items: [
          { text: 'Personas', link: '/personas/buyer-user' },
          { text: 'Jobs To Be Done', link: '/jtbd/main' },
          { text: 'User Flows', link: '/flows/login-flow' }
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
})
