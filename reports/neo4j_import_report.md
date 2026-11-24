# Báo cáo import Neo4j

Ngày import: 25/11/2026 (GMT+7)

## Kết nối

- Instance Neo4j Desktop cục bộ.
- URI sử dụng: `bolt://127.0.0.1:7687`.
- Database: `neo4j`.
- Thông tin xác thực được giữ trong `.env`, tệp này đã bị Git bỏ qua.

## Kết quả

| Chỉ số | Trước import | Sau import |
| --- | ---: | ---: |
| Node | 62 | 249 |
| Relationship | 134 | 2.072 |

Phân bố graph sau import:

- `Source`: 37
- `Chunk`: 201
- `Disease`: 5
- `Concept`: 6
- `FROM_SOURCE`: 201
- `MENTIONS`: 1.871

## Kiểm tra integrity

- Chunk không có `FROM_SOURCE`: 0.
- Assertion không có evidence: 0.
- Không có assertion y khoa được export, vì chưa có mục review `accepted_for_demo`.

Lưu ý: database đã có dữ liệu trước import. Exporter dùng `MERGE` theo ID và không có lệnh xóa graph.
