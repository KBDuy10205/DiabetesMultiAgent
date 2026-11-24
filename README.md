# DiabetesMultiAgent — Knowledge Base / Knowledge Graph

Module này tạo Knowledge Base và Knowledge Graph có thể truy vết từ tài liệu PDF/HTML cục bộ. Dữ liệu thô ở `data/raw/` không bị sửa. Pipeline không gọi LLM, không đưa ra kết luận y khoa mới và không export mệnh đề y khoa chưa được review.

## Cài đặt

Yêu cầu Python 3.10+.

```powershell
python -m pip install -e .[dev]
python -m kb_pipeline.cli all
python -m pytest
```

Nếu máy chưa có Python, cài Python 3.10+ trước rồi chạy lại các lệnh trên.

## Đầu vào và đầu ra

- Đầu vào: `data/raw/pdf`, `data/raw/html`. PDF phải có lớp văn bản có thể chọn/copy; PDF scan không được xử lý trong pipeline này.
- Kiểm kê/trích xuất: `data/interim/`.
- KB: `data/kb/` (nguồn, chunks, Markdown sạch).
- KG: `data/kg/` (thực thể, mentions, ứng viên và quyết định review).
- Cypher: `output/cypher/`.
- Báo cáo: `reports/`.

ID được sinh xác định từ SHA-256 và các giá trị ổn định: source dùng document key + raw hash; chunk dùng source, phiên bản chunking, offset và text hash. Không có UUID ngẫu nhiên.

## Chạy từng bước

```powershell
python -m kb_pipeline.cli inventory --input data/raw
python -m kb_pipeline.cli extract
python -m kb_pipeline.cli build-kb
python -m kb_pipeline.cli extract-entities
python -m kb_pipeline.cli propose-assertions --mode dictionary
python -m kb_pipeline.cli apply-review --review data/kg/assertions_review.csv
python -m kb_pipeline.cli validate
python -m kb_pipeline.cli export-cypher
```

Chỉ dòng có `decision=accepted_for_demo` trong `data/kg/assertions_review.csv` mới được export thành `Assertion`. Dictionary mode chỉ tạo hàng đợi review, không diễn dịch một lần xuất hiện từ khóa thành điều trị, chẩn đoán hoặc quan hệ nhân quả.

Xem [schema](docs/schema.md), [hướng dẫn Neo4j](docs/neo4j_guide.md) và [báo cáo chất lượng](reports/quality_report.md) sau khi chạy pipeline.
