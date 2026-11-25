# Giai đoạn 7 — Các Agent Python

Ngày thực hiện: 25/11/2026. Hệ thống là sản phẩm học tập, không thay thế chẩn đoán hoặc tư vấn của bác sĩ.

## Cấu trúc và hợp đồng

Mỗi Agent có `run()` và được kiểm thử độc lập trước khi tích hợp. Không cần framework agent; chỉ Reasoning Agent sử dụng LLM, khi được yêu cầu và có cấu hình.

| File / Agent | Đầu vào `run()` | Đầu ra / nhiệm vụ |
| --- | --- | --- |
| `src/agents/coordinator.py` — Coordinator | dict yêu cầu | Chọn tác vụ bằng trường dữ liệu hoặc `tasks` tường minh; không tự đoán ý định từ văn bản tự do |
| `src/agents/prediction.py` — Prediction | dict đủ 8 đặc trưng Pima | Gọi pipeline Joblib đã lưu, trả nhãn, xác suất và giới hạn mô hình |
| `src/agents/knowledge.py` — Knowledge | câu hỏi, giới hạn | Nhận diện alias, truy vấn `MENTIONS` và assertion được duyệt có nguồn; không coi quan hệ demo là assertion đã duyệt |
| `src/agents/retrieval.py` — Retrieval | câu hỏi, giới hạn | Tìm vector trong Neo4j, trả chunk và nguồn |
| `src/agents/rule.py` — Rule | dict kết quả xét nghiệm | Gọi Rule Engine, giữ nguyên `results`, `issues`, `alerts` |
| `src/agents/reasoning.py` — Reasoning | câu hỏi, evidence và kết quả ML/rule tùy chọn | Nếu bật, gọi LLM với ngữ cảnh có nguồn và kết quả cấu trúc; nếu thiếu evidence hoặc cấu hình trả lời không đủ bằng chứng |
| `src/agents/validation.py` — Validation | bản nháp, evidence và kết quả ML/rule tùy chọn | Kiểm tra nguồn/citation, một số mẫu khẳng định quá mức, cảnh báo bị bỏ/thay đổi và nêu khả năng kết quả ML khác ngưỡng xét nghiệm |
| `src/agents/workflow.py` | dict yêu cầu | Chạy các Agent, kết hợp vector/KG bằng RRF, trả trạng thái từng Agent và kết quả cấu trúc |
| `src/agents/__main__.py` | JSON từ stdin | Giao diện dòng lệnh JSON |

## Điều phối và an toàn

Mặc định, `features` chọn Prediction, `measurement` chọn Rule, `question` chọn Retrieval và Knowledge. Có thể chỉ định `tasks` là danh sách con của `prediction`, `rule`, `retrieval`, `knowledge`. `generate_answer: true` yêu cầu có `question` và tác vụ `retrieval`.

Rule được chạy trước và trả riêng: `alerts` vẫn hiển thị kể cả khi `issues` không rỗng hoặc Agent khác thất bại. Lỗi Agent được ghi dưới dạng loại lỗi, không in dữ liệu đầu vào. Khi dự đoán nhãn 0 nhưng xét nghiệm đạt ngưỡng cao, Validation nêu cảnh báo về sự khác biệt, không tự kết luận chẩn đoán. Nếu LLM bỏ hoặc thay nguyên văn cảnh báo, bản nháp bị từ chối; cảnh báo cấu trúc vẫn được giữ.

Validation chỉ là kiểm tra xác định giới hạn: citation có tồn tại và nguồn có trường bắt buộc, vài mẫu câu rủi ro, cảnh báo có được giữ nguyên, và một trường hợp khác biệt ML/xét nghiệm. `valid: true` chỉ có nghĩa là qua các kiểm tra này, **không** chứng minh trích dẫn hỗ trợ từng nhận định, mọi mâu thuẫn đã được phát hiện hay câu trả lời an toàn. Khi không có LLM, bản trả lời từ chối có thể qua kiểm tra hình thức; xem thêm `draft_status: llm_not_configured`. Cần chuyên gia thẩm định và đánh giá đầy đủ trước khi sử dụng thực tế.

## Cách chạy

Dùng môi trường `start_ml`, từ thư mục gốc dự án:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
'{"measurement":{"test_type":"fpg","value":53,"unit":"mg/dL"}}' | python -m agents
python -m pytest tests/test_agents.py tests/test_agent_workflow.py -q
```

Ví dụ `53` chỉ là đầu vào kiểm thử, không phải dữ liệu bệnh nhân. Đầu ra có thể đồng thời có cảnh báo glucose thấp và các trường bắt buộc còn thiếu. Gọi từ Python: `from agents.workflow import AgentWorkflow` rồi `AgentWorkflow().run(request)`.

Với Prediction, `features` phải có đúng `Pregnancies`, `Glucose`, `BloodPressure`, `SkinThickness`, `Insulin`, `BMI`, `DiabetesPedigreeFunction`, `Age`; dùng `output/model/diabetes_pipeline.joblib` tin cậy và phiên bản scikit-learn tương thích. Các giá trị đầu vào không âm chưa chắc có ý nghĩa y khoa; mô hình Pima chưa xác nhận lâm sàng.

Với truy xuất cần Neo4j đang chạy, `.env` đã cấu hình, model embedding và vector index theo `05_rag.md`. LLM tùy chọn dùng `RAG_LLM_ENDPOINT`, `RAG_LLM_MODEL` và nếu cần `RAG_LLM_API_KEY`; chỉ khi `generate_answer: true` mới gửi câu hỏi, tài liệu truy xuất, kết quả dự đoán và rule tới endpoint. Chúng có thể chứa thông tin sức khỏe nhạy cảm; chỉ dùng endpoint được phép xử lý dữ liệu đó. Endpoint chưa cấu hình sẽ trả trạng thái `llm_not_configured`, không giả lập câu trả lời.

## Kiểm thử

- Trước tích hợp: `tests/test_agents.py` đạt 7/7, kiểm tra riêng cả bảy Agent bằng mock tại ranh giới dịch vụ; sửa lỗi cú pháp Coordinator phát hiện ở lượt chạy đầu trước khi chạy lại.
- Sau tích hợp: `test_agents.py`, `test_agent_workflow.py`, `test_rule_engine.py`, `test_rag.py`: 52/52 đạt; một cảnh báo deprecation từ plugin anyio. Kiểm tra kết hợp, lỗi một phần, giữ cảnh báo và phát hiện cảnh báo bị thiếu.
- Chạy thật Prediction với một dòng dataset Pima có sẵn và Rule với đầu vào kiểm thử: cả hai thành công; cảnh báo được giữ cùng thông tin thiếu.
- Chạy thật Retrieval và Knowledge trên Neo4j/vector index: cả hai thành công, tìm thấy thực thể `disease_diabetes` và 5 đoạn đã hợp nhất. Model embedding lấy từ cache. Neo4j cảnh báo thủ tục vector deprecated và các quan hệ assertion chưa tồn tại.
- Chưa có endpoint LLM thực: chỉ kiểm thử Reasoning bằng mock và trạng thái `llm_not_configured`; chưa kiểm thử chất lượng, tính đúng nguồn hay độ an toàn của câu trả lời thực. Việc truy xuất đoạn liên quan và các giới hạn nguồn vẫn như `05_rag.md`.
