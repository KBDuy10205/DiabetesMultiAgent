# Báo cáo khảo sát dữ liệu đầu vào

## Phạm vi

Khảo sát ban đầu được thực hiện trên dữ liệu có trong `data/raw/`; dữ liệu thô được giữ nguyên. Pipeline được cấu hình ưu tiên đái tháo đường típ 2 và tiền đái tháo đường, nhưng không tự giới hạn các nguồn còn lại để tránh mất thông tin cần đối chiếu.

## Danh mục đã phát hiện

| Loại | Số lượng | Nội dung chính |
| --- | ---: | --- |
| PDF | 3 | Hướng dẫn nội tiết năm 2020; phác đồ điều trị đái tháo đường típ 2; phác đồ điều trị bệnh thần kinh đái tháo đường |
| HTML | 7 | Dấu hiệu, nguy cơ, chẩn đoán, điều trị, đái tháo đường thai kỳ và bài phân biệt típ 1/típ 2 |

Các tệp HTML có thư mục tài nguyên kèm theo (ảnh, CSS, JavaScript). Pipeline chỉ chọn `.html`, `.htm` và `.pdf`; không xóa hoặc coi tài nguyên đi kèm là nguồn kiến thức.

## Nguồn và bằng chứng

- URL, cơ quan phát hành, ngày xuất bản và ngày truy cập chỉ được lấy từ metadata HTML hoặc `config/source_overrides.csv`; trường không có căn cứ được để `null`.
- Với PDF, pipeline giữ số trang trong block trích xuất; trang quá ít văn bản được đánh dấu `possible_scanned_pages` để kiểm tra thủ công.
- Chưa tạo khẳng định y khoa nào từ nội dung thô. Các `Assertion` chỉ được export sau review rõ ràng trong `data/kg/assertions_review.csv`.

## Kết quả chạy pipeline

- Đã chạy thành công trong môi trường `start_ml` (Python 3.11.15) sau khi cài PyMuPDF.
- Pipeline kiểm kê 33 tệp phù hợp phần mở rộng: 3 PDF, 7 HTML bài viết chính và 23 HTML nhúng/tài nguyên đi kèm. Các tệp HTML nhúng không bị âm thầm bỏ qua mà được gắn cờ chất lượng để review.
- Đã tạo 153 chunks, 6 thực thể từ từ điển và 1.785 mentions. Validation đạt; không có ID/tham chiếu lỗi.
- Chưa có assertion nào được duyệt nên graph chỉ chứa nguồn, chunks, thực thể và mentions; không tạo khẳng định y khoa tự động.
- `pytest`: 3/3 test đạt. Neo4j import chưa kiểm chứng vì repository không có cấu hình/kết nối instance.

## Việc cần kiểm tra thủ công trước khi dùng dữ liệu

1. Đối chiếu phần đầu, giữa, cuối của Markdown sạch với từng nguồn gốc; đặc biệt kiểm tra phủ định, đơn vị, dấu so sánh và bảng.
2. Rà soát các trang PDF bị gắn `possible_scanned_pages`; thay bằng nguồn PDF có text layer nếu các trang scan chứa nội dung cần dùng.
3. Duyệt từng mệnh đề ứng viên, evidence quote, đối tượng áp dụng và điều kiện trước khi đổi thành `accepted_for_demo`.
4. Import vào database Neo4j thử nghiệm và chạy `output/cypher/verify.cypher`.
