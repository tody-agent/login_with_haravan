# Tính năng AI

## Tổng quan

Haravan Helpdesk có tích hợp AI (Gemini) để hỗ trợ agent:
- Phân tích ticket tự động
- Đề xuất phân loại dịch vụ
- Tạo reply nội bộ (internal comment)

## Cách hoạt động

### AI Ticket Analyze

Script `AI - Ticket Analyze API` phân tích nội dung ticket và đề xuất:
- `custom_service_group` (Ecom, Ads, Design, ...)
- `custom_product_suggestion`
- Ghi đề xuất vào **internal Comment** (không tự động apply)

::: info Nguyên tắc AI
AI chỉ **đề xuất** — agent đọc Comment rồi tự quyết định apply.
AI **không** tự ghi field vào ticket (sau Fix C - 2026-05-10).
:::

### AI Send Reply

Script `AI - Send Reply API` tạo internal comment từ AI suggestion.
Đã có permission gate (requires `write` trên `HD Ticket`).

## Cấu hình

```json
{
  "gemini_api_key": "YOUR_GEMINI_API_KEY"
}
```

## Lưu ý vận hành

- AI **không route ticket** — routing yêu cầu Bitrix evidence ([xem chi tiết](/integrations/bitrix-routing))
- `custom_ai_run_status`, `custom_ai_workflow` là field tracking — không ảnh hưởng routing
- Nếu AI lỗi, ticket vẫn tạo bình thường — AI là non-blocking

## Tham chiếu

- [Enrichment Routing](/integrations/bitrix-routing) — AI không route trực tiếp
- [Site Config](/getting-started/site-config) — API key
