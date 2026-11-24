# Tiến trình thực hiện dự án

Cập nhật: 25/11/2026 (GMT+7)

## Mục tiêu hiện tại

Xây dựng pipeline Knowledge Base / Knowledge Graph cho tài liệu đái tháo đường cục bộ, xuất được Cypher để nạp Neo4j. Ưu tiên tính truy vết nguồn và review y khoa; chưa tích hợp ML, LLM, RAG, API hoặc giao diện.

## Tiến độ theo hạng mục

| Hạng mục | Trạng thái | Kết quả |
| --- | --- | --- |
| Khảo sát cấu trúc repo và dữ liệu | Hoàn thành | Giữ cấu trúc sẵn có `data/`, `src/`, `config/`, `output/`, `reports/`, `docs/`; phát hiện 3 PDF và 7 HTML trong `data/raw/`. |
| Thiết kế pipeline | Hoàn thành | Chọn kiến trúc KB/KG evidence-first theo tài liệu tham khảo: inventory → extract → chunks → entities/mentions → review assertion → validate → Cypher. |
| Cấu hình và đóng gói Python | Hoàn thành | Thêm `pyproject.toml`, `config/pipeline.json`, `config/site_rules.json`, `config/entity_dictionary.json`, `config/source_overrides.csv`. |
| Kiểm kê và trích xuất tài liệu | Hoàn thành | Đã kiểm kê 33 tệp (3 PDF, 7 HTML bài viết chính, 23 HTML nhúng/tài nguyên); trích xuất, hash, metadata, block, trang PDF và cờ chất lượng được lưu JSONL. |
| Tạo KB | Hoàn thành | Sinh Markdown sạch, 153 `Chunk`, offset, hash nội dung và section path tại `data/kb/`. |
| KG và review y khoa | Hoàn thành bản cấu trúc | Tạo 6 thực thể từ từ điển và 1.785 `MENTIONS`; chưa export assertion y khoa vì chưa có mục nào được review `accepted_for_demo`. |
| Validate và export Cypher | Hoàn thành | Validation đạt (không lỗi ID/tham chiếu); đã sinh `schema.cypher`, `data.cypher`, `knowledge.cypher`, `verify.cypher`, manifest và quality report. |
| Tài liệu vận hành | Hoàn thành | Bổ sung README, schema, hướng dẫn Neo4j và báo cáo khảo sát dữ liệu. |
| Kiểm tra tĩnh | Hoàn thành | Đã kiểm tra JSON cấu hình hợp lệ và `git diff --check` không báo lỗi whitespace. |
| Kiểm thử và import Neo4j | Hoàn thành | Đã chạy `pytest`: 4/4 test đạt. Đã nạp `knowledge.cypher` vào Neo4j Desktop cục bộ và chạy truy vấn integrity. |
| Kết nối Neo4j Desktop | Hoàn thành | Đã tạo `.env` cục bộ (bị Git bỏ qua), `.env.example` và lệnh `check-neo4j`; kết nối trực tiếp qua `bolt://127.0.0.1:7687`, database `neo4j`, đã xác thực thành công. |
| Kết quả import Neo4j | Hoàn thành | Database tăng từ 62 node/134 relationship lên 249 node/2.072 relationship; không có `Chunk` mồ côi hoặc `Assertion` thiếu evidence. Tổng số bao gồm dữ liệu tồn tại trước import. |
| Chạy lại pipeline và đồng bộ Neo4j | Hoàn thành | Ngày 25/11/2026: chạy `kb_pipeline.cli all`, nạp lại `output/cypher/knowledge.cypher` bằng `MERGE` và chạy kiểm tra integrity. Kết quả: 249 node, 2.072 relationship, 0 `Chunk` mồ côi, 0 `Assertion` thiếu evidence; `pytest` 4/4 đạt. |

## Các tệp chính đã thêm

- `src/kb_pipeline/`: mã pipeline và CLI.
- `tests/`: kiểm thử cơ bản cho ID, chuẩn hóa text và validation.
- `data/kg/assertions_review.csv`: mẫu hàng đợi review.
- `docs/schema.md`, `docs/neo4j_guide.md`, `docs/report.md`: mô hình, hướng dẫn và kết quả khảo sát.

## Cách tiếp tục

1. Đọc `reports/quality_report.md`, nhất là 23 HTML nhúng/tài nguyên và các PDF có cờ `possible_scanned_pages`.
2. Duyệt `data/kg/assertions_review.csv` trước khi đưa mệnh đề y khoa vào graph.
3. Nạp `output/cypher/knowledge.cypher` vào database Neo4j thử nghiệm và chạy `verify.cypher`.

## Nguyên tắc đang áp dụng

- Không tự tạo hoặc hợp nhất kiến thức y khoa không có bằng chứng từ nguồn.
- Không xem việc từ khóa xuất hiện trong đoạn là một quan hệ lâm sàng.
- Không hard-code mật khẩu Neo4j, không xóa graph hiện hữu, không sửa dữ liệu thô.
- Metadata không có căn cứ được để trống (`null`), không suy đoán URL hoặc ngày công bố.
