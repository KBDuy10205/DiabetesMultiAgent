# Giai đoạn 1 — Khảo sát hệ thống hiện có

Ngày khảo sát: 25/11/2026 (GMT+7)

## Phạm vi và nguyên tắc

- Đã đọc cấu trúc repository, toàn bộ mã Python, kiểm thử, cấu hình, tài liệu, báo cáo và các tệp đầu ra KB/KG.
- Đã thống kê toàn bộ dữ liệu thô: 3 PDF, 7 trang HTML chính và các tệp HTML/tài nguyên đi kèm.
- Không sửa mã nguồn, dữ liệu KB/KG, cấu hình, tệp Cypher, hoặc thông tin kết nối.
- Hệ thống phải chỉ hỗ trợ đánh giá nguy cơ; không thay thế chẩn đoán hoặc chỉ định của bác sĩ.

## Cấu trúc hiện có

```text
config/                 Cấu hình pipeline, từ điển thực thể và metadata nguồn
data/
  raw/                  3 PDF, 7 HTML chính và tệp tài nguyên đã lưu
  interim/              Inventory, văn bản trích xuất và cờ chất lượng
  kb/                   Nguồn, 153 chunks và Markdown văn bản sạch
  kg/                   Entity, mention, assertion ứng viên/review/được duyệt
docs/                   Tài liệu kiến trúc, KG/RAG, Neo4j và báo cáo giai đoạn
output/cypher/          schema, dữ liệu và truy vấn kiểm tra Neo4j
reports/                Kết quả validation, manifest và báo cáo import
src/kb_pipeline/        Pipeline KB/KG bằng Python
tests/                  Kiểm thử đơn vị hiện có
```

## Thành phần đã hoàn thành

`src/kb_pipeline/` là một pipeline có khả năng tái lập và ưu tiên bằng chứng:

1. `inventory.py`: liệt kê PDF/HTML, đọc metadata và tính checksum.
2. `extract.py`: trích văn bản từ HTML bằng BeautifulSoup và PDF bằng PyMuPDF; gắn cờ chất lượng.
3. `build_kb.py`: tạo tài liệu sạch, nguồn và chunks có ID xác định.
4. `entities.py`: nhận diện 6 thực thể từ từ điển kiểm soát.
5. `assertions.py`: chỉ tạo ứng viên để chuyên gia review; chỉ xuất assertion có quyết định `accepted_for_demo`.
6. `validate.py`: kiểm tra ID, tham chiếu, offsets và evidence.
7. `cypher_export.py`: sinh Cypher idempotent bằng `MERGE` và truy vấn kiểm tra integrity.
8. `neo4j_connection.py`: đọc cấu hình Neo4j cục bộ từ `.env`, không ghi mật khẩu ra log.
9. `cli.py`: cung cấp các lệnh chạy từng bước và lệnh `all`.

Repository chưa có các mô-đun cần thiết cho mục tiêu mới: mô hình Machine Learning đánh giá nguy cơ, RAG truy hồi/xếp hạng nguồn, API hoặc UI đánh giá, điều phối Multi-Agent, guardrail y khoa và bộ kiểm thử end-to-end cho luồng đánh giá nguy cơ.

## Hiện trạng KB/KG

Kết quả được lấy từ `reports/validation_report.json` và `reports/build_manifest.json`:

| Hạng mục | Số lượng | Trạng thái |
| --- | ---: | --- |
| Nguồn | 33 | 8 `accepted`, 25 `pending` |
| Chunks | 153 | Đã sinh |
| Thực thể | 6 | Từ dictionary kiểm soát |
| Mentions | 1.785 | Chỉ là lượt xuất hiện từ khóa |
| Assertion đã duyệt | 0 | Chưa có dữ kiện y khoa được export |

Validation hiện tại đạt, không có lỗi ID hoặc tham chiếu. Cảnh báo duy nhất: graph chưa có assertion y khoa đã review; do đó không được suy diễn quan hệ lâm sàng từ các `MENTIONS`.

## Chất lượng dữ liệu và rủi ro cần xử lý trước khi dùng cho RAG/KG

- Có 24 tệp bị cờ `too_little_extracted_text`, chủ yếu là HTML nhúng/tài nguyên đi kèm trang chính.
- Có 2 PDF bị cờ `possible_scanned_pages`; cần đối chiếu thủ công hoặc nguồn PDF có text layer trước khi trích dẫn nội dung.
- Metadata PDF còn thiếu URL, đơn vị phát hành và ngày xuất bản đối với một số nguồn.
- Các artifact văn bản trong repository được lưu UTF-8; việc đọc/ghi các artifact mới ở các giai đoạn sau phải tiếp tục giữ UTF-8 để bảo toàn tiếng Việt.
- `config/entity_dictionary.json` hiện chỉ có 6 thực thể và chưa đủ để biểu diễn các đặc trưng/ràng buộc cho đánh giá nguy cơ.
- Không có assertion được chuyên gia duyệt, vì vậy KG hiện không được dùng làm nguồn cho khuyến nghị hoặc kết luận y khoa.

## Cách chạy hiện có

Sau khi có Python 3.10+ và các dependency theo `pyproject.toml`:

```powershell
python -m pip install -e .[dev]
python -m kb_pipeline.cli all
python -m pytest
```

Để kiểm tra Neo4j cục bộ, cần tạo `.env` từ `.env.example`, điền thông tin kết nối riêng và chạy:

```powershell
python -m kb_pipeline.cli check-neo4j
```

Không đưa khóa API, mật khẩu hoặc chuỗi kết nối thật vào mã nguồn hay tài liệu phiên bản hóa.

## Kết quả kiểm thử

- Kết quả lịch sử ghi trong repository: `pytest` đã đạt 4/4 trong lần chạy gần nhất; validation KB/KG đạt.
- Môi trường khảo sát hiện tại không có lệnh thực thi Python (`python`, `py` hoặc `python3`) trên `PATH`, nên không thể chạy lại test mà không cài đặt/thay đổi môi trường.
- Không cài đặt thêm dependency ở giai đoạn khảo sát để giữ đúng phạm vi không thay đổi hệ thống.

## Điểm dừng giai đoạn

Giai đoạn khảo sát đã hoàn tất. Trước khi triển khai phần tiếp theo, cần chốt phạm vi cho mô hình đánh giá nguy cơ (dataset, biến đầu vào, metric, chiến lược chia dữ liệu) và quy tắc an toàn cho câu trả lời. Không nên dùng KB/KG hiện tại để tạo kết luận y khoa cho đến khi hoàn tất rà soát nguồn và review assertion.
