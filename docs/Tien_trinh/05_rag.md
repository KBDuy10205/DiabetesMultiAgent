# Giai đoạn 5 — Vector RAG và Knowledge Graph

Ngày thực hiện: 25/11/2026. Đây là công cụ hỗ trợ truy xuất thông tin, không thay thế chẩn đoán của bác sĩ.

## Thành phần

- `src/rag/core.py`: chia đoạn con, embedding, xây index, truy xuất vector, truy vấn thực thể/quan hệ, kết hợp xếp hạng, tạo ngữ cảnh và gọi LLM.
- `src/rag/cli.py`: lệnh `index` và `search`, tùy chọn vector hoặc hybrid, có thể gọi LLM tương thích Chat Completions.
- `tests/test_rag.py`: kiểm thử chia đoạn, nhận diện thực thể, kết hợp và kiểm tra trích dẫn/đầu vào LLM.
- `pyproject.toml`: nhóm dependency tùy chọn `rag` gồm `sentence-transformers`.
- Neo4j: các node `RAGChunkE5V1`, quan hệ `PART_OF` đến `Chunk` hiện có, thuộc tính `embedding`, và vector index `rag_e5_small_v1`. Không xóa hoặc sửa dữ liệu KB/KG gốc.

## Cách hoạt động

1. Sử dụng chunk hiện có ở `data/kb/chunks.jsonl` và tạo đoạn con tối đa 384 token, chồng lấp 48 token; lưu offset tương đối và đường dẫn mục gốc. Chỉ chọn các chunk có `quality_status=accepted`. Trước khi ghi kiểm tra hash chunk trong Neo4j khớp KB cục bộ.
2. Embedding `intfloat/multilingual-e5-small` (384 chiều) hỗ trợ đa ngôn ngữ, dùng tiền tố `passage:` và `query:` theo [model card](https://huggingface.co/intfloat/multilingual-e5-small). Neo4j lập vector index cosine, truy vấn bằng `db.index.vector.queryNodes` theo [tài liệu Neo4j](https://neo4j.com/docs/cypher-manual/current/indexes/search-indexes/vector-indexes/).
3. Nhận diện alias thực thể chính xác từ dictionary, truy vấn quan hệ `MENTIONS` và theo `FROM_SOURCE`, `PART_OF` để lấy bằng chứng; có truy vấn riêng `HAS_ASSERTION`, `ABOUT`, `SUPPORTED_BY` cho assertion `accepted_for_demo`. Đồ thị hiện chưa có assertion như vậy. `MENTIONS` chỉ biểu thị xuất hiện từ ngữ, không chứng minh quan hệ lâm sàng.
4. Vector và KG được kết hợp bằng reciprocal-rank fusion; khử trùng theo chunk gốc. Dẫn nguồn gồm tiêu đề, URL hoặc đường dẫn, mục và chunk ID. Các nguồn `pending` bị loại; `accepted` chỉ là trạng thái kiểm tra trích xuất, không đồng nghĩa đã được chuyên gia thẩm định y khoa.
5. Tùy chọn gửi câu hỏi và các đoạn được chọn tới endpoint LLM tương thích Chat Completions. Prompt yêu cầu dựa vào bằng chứng, dẫn `[S1]`…, không làm theo chỉ dẫn trong tài liệu, và từ chối nếu thiếu bằng chứng. Nếu không có kết quả, hoặc câu trả lời thiếu citation / citation không tồn tại, trả thông báo không đủ bằng chứng.

Việc kiểm tra citation chỉ xác nhận định dạng và ID tồn tại, không chứng minh nội dung được nguồn hỗ trợ. Chưa có ngưỡng liên quan được hiệu chuẩn, chưa kiểm định khả năng chống prompt injection hay độ đúng y khoa; cần chuyên gia thẩm định và bộ câu hỏi có ground truth trước khi dùng thực tế. Tìm thực thể hiện dựa trên từ điển 6 thực thể và xếp hạng KG còn đơn giản. Các assertion được trả riêng trong JSON CLI, không tự chuyển thành kết luận.

## Cách chạy

Sử dụng `start_ml`, Neo4j đang chạy và `.env` theo `docs/neo4j_guide.md`. Cài dependency nếu cần: `python -m pip install -e ".[rag,dev]"`. Lần đầu cần tải model hoặc có model trong cache. Chạy từ thư mục gốc:

```powershell
$env:PYTHONPATH='src'
python -m rag.cli index
python -m rag.cli search "Triệu chứng của bệnh tiểu đường là gì?" --mode vector
python -m rag.cli search "Triệu chứng của bệnh tiểu đường là gì?" --mode hybrid
python -m pytest tests -q
```

Nếu dùng LLM, đặt `RAG_LLM_ENDPOINT` là URL đầy đủ của endpoint Chat Completions, `RAG_LLM_MODEL` là tên model, và nếu cần `RAG_LLM_API_KEY`; thêm `--answer` vào lệnh search. Câu hỏi và ngữ cảnh sẽ được gửi đến endpoint đó; chỉ sử dụng dịch vụ phù hợp với dữ liệu được phép chia sẻ. Cần bảo vệ khóa và không commit file chứa thông tin xác thực.

Chạy lại `index` dùng ID xác định và `MERGE`, không xóa node cũ; nếu thay KB hoặc model, phải đồng bộ graph và có quy trình quản lý phiên bản/xóa index cũ riêng. `db.index.vector.queryNodes` hoạt động trên instance hiện tại nhưng Neo4j đã thông báo deprecated; cần cập nhật cho phiên bản Neo4j sau này. Tokenizer phát cảnh báo khi đọc chunk gốc dài hơn 512 token; quá trình embedding thực tế dùng đoạn con 384 token.

## Kết quả kiểm thử

- Neo4j cục bộ kết nối thành công. Index `rag_e5_small_v1` ở trạng thái `ONLINE`, có 87 đoạn con; chạy index hai lần vẫn có 87 node.
- Truy vấn thật “Triệu chứng của bệnh tiểu đường là gì?”: vector trả 40 ứng viên; KG nhận diện `disease_diabetes` và trả 40 ứng viên; hybrid trả 5 chunk đã khử trùng. Đây là smoke test, không phải thước đo chất lượng y khoa hay retrieval benchmark.
- Kiểm tra CLI hybrid sau cùng chạy thành công; đoạn đứng đầu trong ví dụ có chứa menu/trang điều hướng và nội dung mở đầu, cho thấy cần làm sạch và đánh giá chất lượng xếp hạng trước khi sử dụng. Lỗi in Unicode Windows phát hiện ở lần chạy trước đã được sửa.
- Truy vấn assertion cho `disease_diabetes`: 0 kết quả; Neo4j cảnh báo các loại quan hệ assertion chưa tồn tại vì chưa có assertion được duyệt.
- `pytest tests`: 9/9 đạt, có một cảnh báo deprecation từ plugin anyio. Kiểm tra xử lý citation và gửi ngữ cảnh dùng mock; không kiểm thử sinh câu trả lời bằng LLM thực vì chưa có endpoint/model được cấu hình. Không kiểm định chất lượng câu trả lời thực tế.
- Lần chạy pytest đầu tiên gặp lỗi quyền truy cập thư mục tạm mặc định; chạy lại với thư mục tạm trong workspace đạt. Thư mục tạm đã được xóa.
