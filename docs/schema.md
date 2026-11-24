# Schema Knowledge Graph

Đồ thị ưu tiên khả năng truy vết. `Source` và `Chunk` là dữ liệu thực trích từ tệp cục bộ; `Assertion` chỉ tồn tại khi đã được review.

```mermaid
flowchart LR
  S[Source] <-- FROM_SOURCE -- CH[Chunk]
  CH -->|MENTIONS| D[Disease]
  CH -->|MENTIONS| C[Concept]
  D -->|HAS_ASSERTION| A[Assertion]
  A -->|ABOUT| C
  A -->|SUPPORTED_BY| CH
```

- `Source`: bản lưu nguồn; có đường dẫn tương đối, checksum và metadata có căn cứ.
- `Chunk`: đoạn văn sạch, offsets và trạng thái chất lượng.
- `Disease`, `Concept`: thực thể từ từ điển kiểm soát; aliases phục vụ nhận diện, không tự tạo từ mỗi tên gọi.
- `Assertion`: nhận định đã được duyệt; có bằng chứng `Chunk` và trạng thái review.

`MENTIONS` biểu thị sự xuất hiện của alias trong đoạn, không đồng nghĩa với quan hệ lâm sàng. Chi tiết evidence và review được lưu trong JSONL để kiểm tra lại.
