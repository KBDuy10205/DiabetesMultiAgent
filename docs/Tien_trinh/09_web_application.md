# Giai đoạn 9 — Ứng dụng Web

Ngày thực hiện: 25/11/2026. Ứng dụng là nguyên mẫu học tập chạy cục bộ, không phải thiết bị y tế và không thay thế bác sĩ.

## Công việc và cấu trúc

- `src/web_app/app.py`: Flask app factory, kiểm tra đầu vào, REST API và lưu lịch sử SQLite.
- `src/web_app/__main__.py`: khởi chạy Flask trên `127.0.0.1:5000`, không bật debug hay reloader.
- `frontend/`: React + Vite, gồm biểu mẫu chỉ số, kết quả và giải thích có nguồn, hỏi đáp, xem/xóa lịch sử; thiết kế responsive.
- `tests/test_web_app.py`: kiểm thử API và cách ly dữ liệu lịch sử.
- `data/private/history.sqlite3`: SQLite cục bộ tạo khi cần, đã được Git bỏ qua; không lưu chỉ số đầu vào hoặc câu hỏi.
- `frontend/dist/`, `frontend/node_modules/`: sản phẩm build/dependency được Git bỏ qua.

Backend gọi `CoordinatorAgent().supervise()` và dùng nguyên các thành phần ML, KG, RAG, Rule Engine và Agent hiện có. `pyproject.toml` bổ sung nhóm dependency `web` cho Flask.

## API

| Phương thức | Đường dẫn | Tác dụng |
| --- | --- | --- |
| POST | `/api/assess` | Kiểm tra 8 đặc trưng Pima và glucose an toàn; gọi Supervisor `risk`. `save_history` phải là boolean và chỉ lưu khi `true`. |
| POST | `/api/chat` | Gửi câu hỏi kiến thức tới luồng `knowledge`, yêu cầu `share_with_llm: true`. |
| POST | `/api/explain` | Gọi luồng `explanation` với đầu vào của lượt đánh giá và yêu cầu `share_with_llm: true`. |
| GET | `/api/history` | Lấy tối đa 100 bản tóm tắt mới nhất của mã trình duyệt hiện tại. |
| DELETE | `/api/history` | Xóa các bản tóm tắt của mã trình duyệt hiện tại sau khi người dùng xác nhận ở giao diện. |

Các API yêu cầu header `X-Session-Token` gồm 64 ký tự hex do trình duyệt sinh. Dữ liệu được scope theo SHA-256 của token. JSON lỗi không chứa exception hoặc khóa. Response có `Cache-Control: no-store`, CSP hạn chế và `X-Content-Type-Options: nosniff`. API giới hạn kích thước payload, kiểm tra host loopback và Origin cục bộ; Flask bind vào loopback.

## Đồng ý và quyền riêng tư

- Đánh giá không tự động lưu. Khi đồng ý, SQLite chỉ lưu timestamp, trạng thái an toàn, nhãn/xác suất dự đoán, cảnh báo và mã vấn đề; **bản tóm tắt vẫn là thông tin nhạy cảm**. Không lưu đặc trưng đầu vào, giá trị xét nghiệm hay câu hỏi chatbot.
- Hỏi đáp và giải thích yêu cầu chọn đồng ý riêng trước khi gửi câu hỏi, đoạn KB và/hoặc kết quả suy ra tới Gemini. Không dùng thông tin bệnh nhân trong các lượt kiểm thử thực tế. Không in API key, key được backend đọc từ `.env`.
- Mã truy cập lịch sử nằm trong `localStorage` của trình duyệt. Xóa dữ liệu trình duyệt có thể khiến lịch sử đã lưu không thể truy cập từ giao diện; người dùng có thể xóa lịch sử trước đó. Người dùng khác dùng chung cùng profile trình duyệt có thể thấy lịch sử.
- SQLite **chưa mã hóa**, không có xác thực người dùng thực sự, quản lý quyền hệ điều hành, HTTPS, chính sách retention hoặc bảo vệ production. Người có quyền đọc máy/DB có thể xem bản tóm tắt. Không đưa ứng dụng ra Internet hoặc dùng thông tin bệnh nhân thật; để triển khai thực tế cần thiết kế xác thực, phân quyền, mã hóa, quản lý khóa, an toàn lâm sàng và vận hành riêng.
- Cổng an toàn Supervisor và kiểm tra nguồn chỉ có phạm vi hạn chế, như mô tả trong `08_multi_agent.md`. Mô hình Pima và nội dung LLM chưa được thẩm định lâm sàng. Gemini đã có lần HTTP 503/timeout như `09_kiem_thu_gemini.md`; giao diện nêu trạng thái chưa có câu trả lời thay vì bịa kết quả.

## Cách chạy cục bộ

Trong môi trường `start_ml`, từ gốc dự án (nếu cần cài dependency Python, chạy `python -m pip install -e ".[web,rag,dev]"`; môi trường cần tương thích pipeline scikit-learn đã lưu):

```powershell
conda activate start_ml
cd frontend
npm ci
npm run build
cd ..
$env:PYTHONPATH='src'
python -m web_app
```

Mở `http://127.0.0.1:5000`. Bản build React được Flask phục vụ cùng origin. Để phát triển frontend, có thể chạy `npm run dev` ở `frontend` (Vite tại `127.0.0.1:5173` proxy API tới Flask); backend vẫn phải chạy riêng. Đánh giá cần `output/model/diabetes_pipeline.joblib`; hỏi đáp/giải thích cần Neo4j, vector index, embedding và cấu hình Gemini như các báo cáo giai đoạn 5 và 9 kiểm thử Gemini.

## Kết quả kiểm thử

- `npm run build`: thành công, React/Vite tạo bundle trong `frontend/dist/`.
- `pytest tests`: **81/81 đạt**, gồm 8 kiểm thử web về host/origin, token, đồng ý, cô lập/xóa lịch sử, dữ liệu không hợp lệ, xử lý lỗi và phục vụ static. Có một cảnh báo deprecation từ plugin anyio.
- HTTP cục bộ: Flask phục vụ trang và JS với HTTP 200 và CSP; đánh giá thật với pipeline ML, dữ liệu Pima có sẵn và glucose kiểm thử trả Prediction `ok`, `passed_limited`, `saved=false`.
- Hỏi đáp/giải thích được kiểm thử API bằng Supervisor mock. Thử HTTP `/api/chat` thật với câu hỏi chung và KB đã được cho phép: truy xuất được 5 nguồn nhưng Reasoning trả lỗi, API trả `unavailable`, `valid=false`, `reasoning_unavailable`. Chưa có câu trả lời Gemini đầu-cuối thành công; dịch vụ từng trả 503/timeout như báo cáo kiểm thử Gemini. Không tạo dữ liệu bệnh nhân.
- Không xác nhận được bố cục hoặc thao tác giao diện trên trình duyệt: công cụ Computer Use không kết nối được native pipe. Cần kiểm thử trực quan trên desktop và mobile trước khi bàn giao cho người dùng cuối.

Đã dùng quy trình Sites ở chế độ dự án cục bộ để giữ kiến trúc React/Flask/SQLite theo yêu cầu; không xuất bản hay triển khai dữ liệu lên dịch vụ hosting.

## Cập nhật: chọn số liệu bằng thanh kéo

- Tám đặc trưng Pima và glucose kiểm tra an toàn được chọn bằng thanh kéo, hiển thị giá trị/đơn vị và có nút `+`/`−` để chỉnh theo bước. Có thể điều khiển bằng bàn phím; mỗi trường bắt đầu ở trạng thái `Chưa chọn` và phải được người dùng thao tác trước khi gửi.
- Phạm vi thanh kéo là giới hạn giao diện, không phải khoảng giá trị y khoa hợp lệ. Nếu số liệu thực tế nằm ngoài phạm vi hiển thị, không chọn giá trị gần nhất. Các bước là 1 cho số lần mang thai và tuổi, 0,001 cho DPF, 0,01 cho các trường còn lại.
- `frontend/src/RangeField.jsx` là thành phần tái sử dụng; `frontend/test-range.cjs` kiểm tra trạng thái chưa chọn, thao tác chuột/bàn phím và nút chỉnh có độ chính xác và giới hạn. `npm run test`: 3/3 đạt; `npm run build`: đạt. Chưa kiểm thử thao tác trực quan trong trình duyệt ở lượt này.
