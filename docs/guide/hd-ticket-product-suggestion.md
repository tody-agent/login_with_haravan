---
title: Cấu hình HD Ticket Product Suggestion
description: Hướng dẫn vận hành cho nhân viên Haravan khi cập nhật luật gợi ý sản phẩm và mặc định GitLab issue.
keywords: hd ticket product suggestion, gitlab, import, helpdesk, haravan
robots: index, follow
---

# Cấu hình HD Ticket Product Suggestion

Tài liệu này dùng cho nhân viên Haravan khi cần cập nhật DocType `HD Ticket Product Suggestion` trên Frappe Helpdesk.

Trang thao tác:

```text
https://haravan.help/desk/hd-ticket-product-suggestion
```

DocType này là bảng cấu hình nghiệp vụ. Mỗi dòng nên đại diện cho một nhóm vấn đề hoặc một luật gợi ý sản phẩm. Khi agent tạo GitLab issue từ ticket, popup GitLab có thể lấy thêm `GitLab Labels` và `Assign to` từ dòng cấu hình này.

## Khi Nào Cần Cập Nhật

Cập nhật DocType này khi:

- Có sản phẩm, module, feature mới cần phân loại ticket.
- Agent hay chọn sai product/module vì thiếu luật gợi ý.
- Cần GitLab issue tạo từ nhóm ticket đó tự có label đúng.
- Cần GitLab issue mặc định assign cho một hoặc nhiều người phụ trách.

Nếu chỉ đổi token GitLab, không cập nhật DocType này. Token nằm trong Site Config hoặc `Helpdesk Integrations Settings`.

## Ý Nghĩa Các Trường

Tên field có thể hiển thị hơi khác theo giao diện tiếng Việt. Khi import, dùng fieldname kỹ thuật nếu site yêu cầu.

| Label trên form | Fieldname thường dùng | Bắt buộc | Nhập gì | Kiểu dữ liệu | Lấy từ đâu | Ví dụ |
| --- | --- | --- | --- | --- | --- | --- |
| Product Suggestion | `product_suggestion` hoặc `name` | Có | Tên luật gợi ý, ngắn gọn, dễ hiểu | Text | Haravan tự đặt theo nghiệp vụ | `Omni - Đồng bộ đơn hàng` |
| Product Line | `product_line` | Không | Dòng sản phẩm lớn | Text | Danh mục sản phẩm nội bộ | `Omni`, `POS`, `Marketing`, `Web` |
| Product Module | `product_module` | Không | Module hoặc phân hệ | Text | Team product/support thống nhất | `Đơn hàng`, `Thanh toán`, `Vận chuyển` |
| Product Feature | `product_feature` | Không | Feature cụ thể | Text | Team product/support thống nhất | `Đồng bộ đơn`, `In vận đơn` |
| Product Function | `product_function` | Không | Chức năng chi tiết hơn feature | Text | Team product/support thống nhất | `Tạo đơn`, `Cập nhật trạng thái` |
| Gitlab Labels | `gitlab_labels` | Không | Label GitLab sẽ prefill khi tạo issue | Text, phân cách bằng dấu phẩy | GitLab project > Manage > Labels | `helpdesk,customer-report,omni,order-sync` |
| Assign to | `assign_to` | Không | GitLab user ID của người nhận issue | Số hoặc nhiều số, phân cách bằng dấu phẩy | GitLab profile/API/member list | `12345678` hoặc `12345678,87654321` |
| Default Gitlab ProjectID | `default_gitlab_projectid` | Không | Để trống, chỉ dùng khi team kỹ thuật yêu cầu | Số | Team kỹ thuật cung cấp | Để trống |

Thông thường Haravan chỉ dùng một GitLab project mặc định đã cấu hình trong hệ thống. Nhân viên vận hành không cần nhập `Default Gitlab ProjectID`.

## Quy Tắc Nhập Dữ Liệu

`Gitlab Labels` là text label, không phải ID. Nhập đúng tên label trong GitLab, phân cách bằng dấu phẩy. Không cần thêm dấu `#`.

`Assign to` là GitLab user ID, không phải email, không phải username, không phải tên nhân viên. Nếu nhập email như `a@haravan.com`, GitLab API sẽ không assign được.

`Default Gitlab ProjectID` để trống trong vận hành hằng ngày. Chỉ nhập khi team kỹ thuật xác nhận cần tạo issue sang project khác.

Nên dùng chữ thường, không dấu cho GitLab label để dễ lọc, ví dụ `omni`, `order-sync`, `bug`, `customer-report`.

Không xóa record cũ nếu chưa chắc chắn. Ưu tiên bỏ nội dung không còn dùng hoặc đổi trạng thái disable nếu form có field enabled/disabled.

## Cách Lấy GitLab User ID

Cách nhanh nhất:

1. Mở GitLab.
2. Bấm avatar người cần assign.
3. Mở trang profile của người đó.
4. Tìm phần user ID trên profile hoặc trong URL/API nếu GitLab đang hiển thị.
5. Copy số ID vào field `Assign to`.

Nếu không thấy user ID trên giao diện:

1. Mở project GitLab liên quan.
2. Vào `Project information` > `Members`.
3. Tìm nhân viên theo tên/email.
4. Nhờ admin GitLab hoặc team kỹ thuật tra user ID bằng GitLab API.

Định dạng nhập:

```text
12345678
```

Hoặc nhiều người:

```text
12345678,87654321
```

Không nhập:

```text
nguyen.van.a@haravan.com
@username
Nguyễn Văn A
```

## Cập Nhật Thủ Công Từng Dòng

1. Mở `HD Ticket Product Suggestion`.
2. Tìm record hiện có trước khi tạo mới để tránh trùng.
3. Mở record cần sửa hoặc bấm `New`.
4. Điền các trường sản phẩm/module/feature theo nghiệp vụ.
5. Điền `Gitlab Labels` nếu muốn popup GitLab tự có label.
6. Điền `Assign to` nếu muốn issue tự assign người phụ trách.
7. Để trống `Default Gitlab ProjectID`.
8. Lưu record.
9. Mở một ticket test có chọn product suggestion đó.
10. Bấm GitLab > `Tạo mới` và kiểm tra popup đã prefill label/assignee chưa.

Không cần deploy code sau khi sửa record. Đây là cấu hình dữ liệu trên site.

## Import Nhiều Dòng Bằng Data Import

Dùng Data Import khi cần thêm hoặc cập nhật nhiều luật cùng lúc.

1. Vào Desk, tìm `Data Import`.
2. Bấm `New`.
3. Chọn `Reference DocType` là `HD Ticket Product Suggestion`.
4. Chọn `Import Type`:
   - `Insert New Records` nếu toàn bộ là record mới.
   - `Update Existing Records` nếu sửa record đã có.
5. Tải template từ Frappe nếu cần.
6. Chuẩn bị file CSV hoặc XLSX.
7. Upload file.
8. Bấm `Start Import`.
9. Nếu có lỗi, tải file lỗi về, sửa đúng dòng lỗi rồi import lại.

Khi update record cũ, file import phải có cột định danh record. Thường là `ID` hoặc `Name` tùy template Frappe xuất ra. Không tự đoán cột này; hãy tải template từ chính site trước.

## Mẫu CSV

Mẫu này dùng để trao đổi nội bộ. Khi import thật, nên tải template từ Frappe rồi copy dữ liệu sang đúng cột.

```csv
Product Suggestion,Product Line,Product Module,Product Feature,Product Function,Gitlab Labels,Assign to
Omni - Đồng bộ đơn hàng,Omni,Đơn hàng,Đồng bộ đơn,Tạo/Cập nhật đơn,"helpdesk,customer-report,omni,order-sync","12345678"
POS - Thanh toán lỗi,POS,Thanh toán,Thanh toán tại quầy,Thu tiền,"helpdesk,customer-report,pos,payment","87654321"
Web - Giao diện storefront,Web,Theme,Storefront,Hiển thị giao diện,"helpdesk,customer-report,web,theme",""
```

Lưu ý:

- Giữ nguyên số GitLab trong dạng text khi làm bằng Excel để không bị đổi định dạng.
- Nếu một ô có nhiều label hoặc nhiều assignee, đặt trong dấu nháy kép.
- Không thêm khoảng trắng thừa quanh GitLab label nếu không cần.
- Nếu không có assignee riêng, để trống ô.

## Checklist Trước Khi Import

- Mỗi dòng có tên gợi ý rõ nghĩa, không trùng dòng cũ.
- `Gitlab Labels` là label text có thật trong GitLab.
- `Assign to` chỉ chứa số GitLab user ID và dấu phẩy.
- Không nhập `Default Gitlab ProjectID` nếu không có yêu cầu từ team kỹ thuật.
- Đã xác định import là insert hay update.
- Đã tải template từ Frappe để đối chiếu cột bắt buộc.
- Đã thử trước với 1-2 dòng nếu đây là lần import lớn.

## Kiểm Tra Sau Khi Import

1. Mở lại `HD Ticket Product Suggestion`.
2. Search một record vừa import.
3. Kiểm tra các trường GitLab không bị mất dấu phẩy hoặc đổi định dạng.
4. Mở một ticket test và chọn product suggestion tương ứng.
5. Bấm GitLab > `Tạo mới`.
6. Xác nhận:
   - Labels được prefill đúng.
   - Assignee IDs được prefill đúng nếu có.
7. Không bấm tạo issue thật nếu chỉ kiểm tra UI. Nếu cần test end-to-end, tạo issue test rồi đóng/xóa theo quy trình GitLab của team.

## Lỗi Thường Gặp

| Hiện tượng | Nguyên nhân thường gặp | Cách xử lý |
| --- | --- | --- |
| Popup GitLab không có assignee | Field `Assign to` trống hoặc nhập email/username | Đổi sang GitLab user ID dạng số |
| Issue tạo sai project | Cấu hình project mặc định của hệ thống sai | Báo team kỹ thuật kiểm tra `Helpdesk Integrations Settings` |
| Label không hiện đúng | Label nhập sai tên hoặc có khoảng trắng thừa | Kiểm tra lại label trong GitLab project |
| Import báo thiếu cột bắt buộc | File không theo template site | Tải template mới từ Data Import rồi copy dữ liệu sang |
| Update tạo record mới ngoài ý muốn | Thiếu cột `Name`/ID của record cũ | Export/template record hiện tại rồi import update lại đúng ID |

## Khi Cần Gọi Team Kỹ Thuật

Liên hệ team kỹ thuật nếu:

- Không biết GitLab user ID của người cần assign.
- Data Import báo lỗi quyền hoặc lỗi server.
- Popup GitLab không hiển thị giá trị dù record đã nhập đúng.
- Cần thêm field mới ngoài các field hiện có.
- Cần tạo issue GitLab theo logic phức tạp hơn, ví dụ theo nhóm khách hàng, SLA hoặc Bitrix segment.
