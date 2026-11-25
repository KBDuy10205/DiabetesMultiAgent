# Cấu hình và kiểm thử Gemini

Ngày thực hiện: 25/11/2026. Kiểm thử sử dụng câu hỏi kiến thức chung, không dùng dữ liệu bệnh nhân. Người dùng đã cho phép gửi các đoạn KB của dự án tới Google Gemini cho lượt kiểm thử RAG.

## Cấu hình

- `src/agents/settings.py` đọc khóa từ `.env` hoặc biến môi trường, hỗ trợ `RAG_LLM_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`; biến môi trường cùng tên ưu tiên hơn file. Không in khóa. `.env` được Git bỏ qua.
- Mặc định endpoint Chat Completions tương thích là `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`, model `gemini-4-hydrogen`, theo [tài liệu Google](https://ai.google.dev/gemini-api/docs/openai). Có thể ghi đè bằng `RAG_LLM_ENDPOINT` và `RAG_LLM_MODEL`.
- `ReasoningAgent` lấy cấu hình thông qua module này. Với model và endpoint Gemini đã chọn, `rag.core.answer` yêu cầu `reasoning_effort=low`; HTTP timeout 80 giây, Supervisor timeout 90 giây. Không thêm thư viện LLM hoặc tự đổi model.

## Kết quả

- Kiểm thử kết nối bằng lời chào không chứa KB: HTTP 200, phản hồi có `choices`. Đây chỉ xác nhận kết nối/định dạng phản hồi, không đánh giá chất lượng câu trả lời.
- Kiểm thử Supervisor với câu hỏi kiến thức chung: Retrieval và Knowledge thành công, trả 5 đoạn bằng chứng; Reasoning lỗi, Supervisor trả `reasoning_unavailable` và không trả câu trả lời không được kiểm chứng.
- Kiểm tra riêng Reasoning với một đoạn KB sau đó: một lần HTTP 503, một lần chờ hết 60 giây. Sau khi cấu hình mức suy luận thấp và tăng HTTP timeout lên 80 giây, thử lại nhận HTTP 503. Do đó **chưa hoàn tất kiểm thử RAG/LLM đầu-cuối thành công** và chưa đánh giá được citation hoặc chất lượng trả lời thật.
- Các kiểm thử `test_gemini_settings.py`, `test_agents.py`, `test_agent_workflow.py`, `test_supervisor.py`, `test_rag.py`: 32/32 đạt; một cảnh báo deprecation từ plugin anyio. Các test Gemini dùng mock, không thay thế kiểm thử dịch vụ thật.

## Cách chạy

Tạo `RAG_LLM_API_KEY=...` trong `.env` mà không commit khóa. Sau khi Neo4j, index và embedding đã sẵn sàng, từ thư mục gốc trong môi trường `start_ml`:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
'{"intent":"knowledge","question":"Tiểu đường có những dấu hiệu nào?","generate_answer":true}' | python -m agents.supervisor
python -m pytest tests/test_gemini_settings.py tests/test_agents.py tests/test_agent_workflow.py tests/test_supervisor.py tests/test_rag.py -q
```

Khi `generate_answer=true`, câu hỏi và các đoạn được truy xuất được gửi tới Gemini; nếu có kết quả ML/rule thì bản tóm tắt các kết quả đó cũng được gửi. Không gửi dữ liệu sức khỏe thật nếu endpoint chưa được chấp thuận để xử lý chúng. Kiểm tra `agents.reasoning.status`, `answer.draft_status`, `answer.valid`, `answer.issues` và nguồn; `valid` chỉ là kiểm tra hình thức có giới hạn, không xác minh tính đúng y khoa. Có thể chạy lại khi Gemini ổn định; không tự khẳng định nguyên nhân HTTP 503.
