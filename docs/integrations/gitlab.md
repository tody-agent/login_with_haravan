# Tích hợp GitLab

## Tổng quan

Haravan Helpdesk tích hợp với GitLab để:
- Tạo **GitLab Issue** trực tiếp từ HD Ticket
- Link issue URL vào ticket để tracking
- Phân công assignee dựa trên labels

## Cách sử dụng

### Tạo GitLab Issue từ ticket

1. Mở HD Ticket cần tạo issue
2. Nhấn nút **"GitLab Issue"** trên toolbar (HD Form Script)
3. Popup hiển thị:
   - Title (tự fill từ ticket subject)
   - Labels (chọn từ danh sách)
   - Assignee preview (tự resolve từ labels)
4. Nhấn **"Tạo Issue"**
5. Issue URL được ghi vào `custom_gitlab_issue_url`

### Scripts liên quan

| Script | Type | Chức năng |
|---|---|---|
| `GitLab - Ticket Issue API` | Server Script (API) | Resolve assignee, tạo và link issue |
| `GitLab - Ticket Issue Button` | HD Form Script | Popup tạo issue trên toolbar |

### Custom fields

| Field | Mô tả |
|---|---|
| `custom_gitlab_issue_url` | URL GitLab issue đã tạo |
| `custom_gitlab_issue_id` | Internal GitLab issue ID |
| `custom_gitlab_issue_iid` | Project-scoped issue IID |

## Cấu hình

Trong Site Config:

```json
{
  "gitlab_token": "YOUR_GITLAB_TOKEN",
  "gitlab_project_id": "PROJECT_ID",
  "gitlab_base_url": "https://gitlab.com"
}
```

## Tham chiếu

- [Script Catalog](/operations/script-catalog) — Registry đầy đủ
- [Site Config](/getting-started/site-config) — Cấu hình keys
