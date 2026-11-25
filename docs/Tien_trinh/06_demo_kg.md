# Quan hệ ngữ nghĩa demo trong Knowledge Graph

Ngày thực hiện: 25/11/2026. Mục đích là thực hành CNTT; đây không phải dữ liệu y khoa đã thẩm định và không dùng để chẩn đoán.

## Công việc

- Tạo `data/kg/demo_relations.jsonl` với ba quan hệ ví dụ: bệnh đái tháo đường có thể liên quan tới khát nước nhiều, tiểu nhiều và nhanh đói. Cả ba được trích từ cùng một câu trong chunk `chunk_1483f0277f4d8639ee394f11`, nguồn `source_fb7113e6c29574f7fadf3def`, bài [10 dấu hiệu tiểu đường thường gặp và cách nhận biết sớm](https://tamanhhospital.vn/dau-hieu-tieu-duong/).
- Mỗi bản ghi có `demo: true`, `review_status: demo_unreviewed`, loại quan hệ, thực thể, nguyên văn bằng chứng, ID chunk và nguồn.
- Tạo `src/kb_pipeline/demo_graph.py` để kiểm tra tính nhất quán của dữ liệu cục bộ, nhập theo transaction và truy vấn nguồn. Graph sử dụng node `DemoAssertion`, `DemoConcept` và các quan hệ `HAS_DEMO_ASSERTION`, `DEMO_ABOUT`, `DEMO_SUPPORTED_BY`, nối tới `Disease`, `Chunk`, `Source` đã có.
- Không đánh dấu các mục này là assertion được duyệt; không sửa file `assertions_approved.jsonl`. RAG hiện có không tự đưa các `DemoAssertion` vào truy vấn assertion đã duyệt hay ngữ cảnh LLM.

## Cách chạy

Với môi trường `start_ml`, Neo4j đang chạy và `.env` đã cấu hình, từ thư mục gốc dự án:

```powershell
$env:PYTHONPATH='src'
python -m kb_pipeline.demo_graph import
python -m kb_pipeline.demo_graph query
python -m pytest tests/test_demo_graph.py tests/test_rag.py -q
```

Import dùng `MERGE`, kiểm tra nguyên văn evidence trong chunk cục bộ và trong Neo4j, và từ chối toàn bộ transaction nếu tham chiếu graph không hợp lệ. `query` hiển thị từng quan hệ, trạng thái, đoạn trích và nguồn.

## Kiểm thử và giới hạn

- Import thực tế vào Neo4j thành công; truy vấn trả ba bản ghi có nguồn. Chạy import lần hai vẫn trả ba bản ghi, không nhân đôi.
- Kiểm thử `test_demo_graph.py` và `test_rag.py`: 6/6 đạt; có một cảnh báo deprecation từ plugin anyio.
- Truy vấn assertion đã duyệt hiện có vẫn trả 0 bản ghi. Neo4j cảnh báo một số loại quan hệ assertion chưa tồn tại; đây là trạng thái hiện tại của graph, không phải bằng chứng đã có nội dung được duyệt.
- Ba mục chỉ dựa trên một nguồn và một câu; chưa có chuyên gia thẩm định, chưa đối chiếu các nguồn khác, không dùng làm kiến thức y khoa chính thức hay khuyến nghị cá nhân.
