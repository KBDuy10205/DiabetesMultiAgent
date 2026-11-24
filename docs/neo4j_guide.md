# Hướng dẫn Neo4j

1. Cài Neo4j Community hoặc khởi tạo một database thử nghiệm riêng.
2. Chạy pipeline để tạo `output/cypher/knowledge.cypher`.
3. Trong Cypher Shell, nạp schema và dữ liệu từ tệp hoàn chỉnh. Không dùng database có dữ liệu quan trọng để thử nghiệm.

```powershell
python -m pip install -e .[dev]
python -m kb_pipeline.cli all
docker compose exec neo4j cypher-shell -u neo4j -d neo4j
```

Trong Cypher Shell, sao chép tệp vào thư mục import của Neo4j rồi chạy:

```text
:source /var/lib/neo4j/import/knowledge.cypher
```

Sau đó dùng `output/cypher/verify.cypher` để đếm node/relationship và tìm chunk/assertion thiếu evidence. Nạp lần hai phải không tạo ID trùng vì exporter dùng `MERGE` theo `id`.

Không có mật khẩu hoặc chuỗi kết nối Neo4j trong mã nguồn. Lần import thử nghiệm ngày 25/11/2026 đã hoàn thành trên Neo4j Desktop cục bộ; mọi lần import sau vẫn cần chạy `verify.cypher` để đối chiếu kết quả.

## Cấu hình local

Tạo `.env` từ `.env.example`, đặt `NEO4J_URI`, `NEO4J_DATABASE`, `NEO4J_USERNAME` và `NEO4J_PASSWORD`. Tệp `.env` bị Git bỏ qua. Kiểm tra kết nối bằng `python -m kb_pipeline.cli check-neo4j`; lệnh chỉ in URI, database và số lượng graph, không in mật khẩu.
