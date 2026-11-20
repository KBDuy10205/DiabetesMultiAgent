# DiabetesMultiAgent — HTML → Knowledge Base → Knowledge Graph

Pipeline offline chuyển HTML có sẵn thành Knowledge Base (KB) có thể đối chiếu và Knowledge Graph (KG) import Neo4j. Không crawl, không train model, không dùng LLM/vector DB/APOC và không sửa/xóa HTML gốc.

## Kết quả build hiện tại

- Inventory: 19 HTML, gồm 4 bài nguồn và 15 HTML asset phụ trong các thư mục `_files`.
- KB: 4 sources và 48 chunks; KG structural: 10 entities và 593 mentions.
- Có 341 assertion candidates `pending`, chưa assertion nào được reviewer duyệt nên graph không xuất `Assertion`.
- Kiểm tra offline không có lỗi; Neo4j import chưa được kiểm chứng trong môi trường build. Xem `reports/`.

## Cây dự án

```text
DiabetesMultiAgent/
├── config/                 # Cấu hình selector, chunking, entity dictionary
├── data/                   # Input, intermediate data, KB và KG
├── output/cypher/          # Cypher Neo4j tự chứa
├── reports/                # Báo cáo và manifest tái lập
├── src/kb_pipeline/        # Mã nguồn pipeline Python
├── tests/                  # Test và fixture HTML minh họa
├── Huong_dan_Neo4j_tu_dau.md
├── Huong_dan_va_prompt_HTML_den_KB_KG_Cypher.md
├── pyproject.toml
├── README.md
└── .gitignore
```

`data/raw_html/` là input gốc, không bị pipeline sửa/xóa. `data/interim/`, `data/kb/`, `data/kg/`, `output/`, `reports/` là output tái tạo được. `.git/` là lịch sử Git; `.pytest_cache/` chỉ là cache test cục bộ.

## File gốc ở root

| File | Vai trò |
| --- | --- |
| `Huong_dan_Neo4j_tu_dau.md` | Schema graph, Neo4j/Cypher Shell, kiểm tra/import thủ công. |
| `Huong_dan_va_prompt_HTML_den_KB_KG_Cypher.md` | Đặc tả bắt buộc HTML → KB → KG → Cypher. |
| `pyproject.toml` | Khai báo package Python, dependencies và cấu hình pytest. |
| `.gitignore` | Quy tắc loại trừ file/cache local khỏi Git. |
| `README.md` | Tài liệu cấu trúc và cách vận hành này. |

## `config/`

| File | Vai trò |
| --- | --- |
| `pipeline.json` | Phiên bản pipeline/extractor/chunking, giới hạn chunk và batch Cypher. |
| `site_rules.json` | Selector đã khảo sát cho Tâm Anh, Vinmec, Long Châu; quy tắc bỏ boilerplate. |
| `entity_dictionary.json` | Entity chuẩn, label, type và aliases; type 1/type 2/thai kỳ là entity riêng. |
| `source_overrides.csv` | Bổ sung metadata được người dùng xác minh; hiện chỉ header, không tự bịa metadata. |

## `data/`

| Đường dẫn | Vai trò |
| --- | --- |
| `data/diabetes.csv` | Dataset tabular từ phần khác của dự án; KB/KG pipeline không đọc/sửa file này. |
| `data/raw_html/` | HTML nguồn thật. Bốn file `.html` cấp đầu là bài nguồn; `*_files/` là asset tải kèm (ảnh/CSS/JS/HTML phụ). |
| `data/interim/html_inventory.jsonl` | Danh mục mọi HTML/HTM: path, size, SHA-256, metadata, page type. HTML asset là `supporting_asset_html`. |
| `data/interim/documents.jsonl` | Bài trích có block, clean text, selector, extractor, metadata và quality flags. |
| `data/interim/extraction_errors.jsonl` | Lỗi/cờ theo từng file trích; rỗng ở build hiện tại. |
| `data/kb/sources.jsonl` | Source records: title, canonical URL nếu được HTML khai báo, publisher/path/hash/ngày metadata. |
| `data/kb/chunks.jsonl` | Chunk text, hash, section, offsets `[start,end)`, locator và `source_id`. |
| `data/kb/documents/*.md` | Markdown sạch để đối chiếu trực tiếp với HTML nguồn. |
| `data/kg/entities.jsonl` | Entity graph chuẩn với label `Disease` hoặc `Concept`. |
| `data/kg/mentions.jsonl` | Alias thực sự khớp với chunk cùng offsets; `MENTIONS` không phải quan hệ y khoa. |
| `data/kg/assertions_candidates.jsonl` | Candidates có quote/chunk/context, mặc định `pending`; chưa là tri thức được duyệt. |
| `data/kg/assertions_review.csv` | Phiếu review. Cần decision/reason/reviewer/reviewed_at thật. |
| `data/kg/assertions_approved.jsonl` | Chỉ assertion có `accepted_for_demo`; hiện rỗng. |
| `data/kg/nodes.jsonl` | Nodes chuẩn hóa cho Cypher exporter. |
| `data/kg/relationships.jsonl` | Quan hệ nguồn: `FROM_SOURCE`, `MENTIONS` và relationship assertion đã duyệt. |

## `src/kb_pipeline/`

| File | Trách nhiệm |
| --- | --- |
| `__init__.py` | Package metadata/version. |
| `io.py` | JSON/JSONL UTF-8, SHA-256 và ID ổn định. |
| `inventory.py` | Kiểm kê HTML/HTM và metadata mà không sửa input. |
| `extract.py` | BeautifulSoup/lxml, selector body, heading/list/table, lỗi từng file. |
| `clean.py` | Unicode NFC/khoảng trắng có kiểm soát; không bỏ phủ định/đơn vị. |
| `chunk.py` | Source, Markdown, chunk offsets/hash tái lập. |
| `entities.py` | Alias matching theo ranh giới; chỉ tạo mentions. |
| `assertions.py` | Tạo candidate theo dictionary và áp review CSV, không tự duyệt. |
| `validate.py` | Kiểm tra ID, reference, type, quote, hash, offsets và provenance. |
| `cypher_export.py` | Serialize Cypher an toàn, allowlist schema, batch/export. |
| `cli.py` | CLI từng bước, `run-all`, report và manifest. |

## `output/cypher/`

| File | Vai trò |
| --- | --- |
| `schema.cypher` | Constraint unique ID và index cho `Concept.name_normalized`. |
| `data.cypher` | Node trước quan hệ; `MERGE` theo ID, batch nhỏ. |
| `knowledge.cypher` | File tự chứa để import: schema + data, UTF-8, không APOC/parameter/file ngoài. |
| `verify.cypher` | Query đếm/kiểm tra provenance sau import; không import file này. |

## `reports/`

| File | Vai trò |
| --- | --- |
| `quality_report.md` | Counts, pending/approved, validation và trạng thái Neo4j import. |
| `build_manifest.json` | Input/config/code hashes, counts, output checksums, error files và run timestamp. Timestamp chỉ ở manifest để Cypher tái lập. |

## `tests/`

| File | Vai trò |
| --- | --- |
| `fixtures/article_with_table.html` | HTML demo riêng, chứa heading, phủ định, bảng và list; không lẫn dữ liệu thật. |
| `test_extract.py` | Kiểm tra heading/bảng/phủ định được giữ. |
| `test_entities.py` | Kiểm tra alias boundary, tránh match trong từ dài hơn. |
| `test_cypher_export.py` | Kiểm tra tiếng Việt, nháy đơn/đôi, backslash, newline, semicolon và chuỗi giống Cypher. |

## Chạy pipeline (`start_ml`)

```powershell
$env:PYTHONPATH = 'src'
& 'C:\Users\kduy7\miniconda3\envs\start_ml\python.exe' -m kb_pipeline.cli run-all --input data/raw_html
& 'C:\Users\kduy7\miniconda3\envs\start_ml\python.exe' -m pytest -q
```

Các bước riêng: `inventory`, `extract`, `build-kb`, `extract-entities`, `propose-assertions --mode dictionary`, `apply-review`, `validate`, `export-cypher`.

## Import Neo4j Desktop (không Docker)

```powershell
& "C:\Users\kduy7\.Neo4jDesktop2\Data\dbmss\dbms-90e4d248-44f6-4311-bb82-240edbd5629e\bin\cypher-shell.bat" `
  -a bolt://127.0.0.1:7687 -u neo4j -d neo4j `
  -f "D:\AI\DiabetesMultiAgent\output\cypher\knowledge.cypher"
```

Sau import, chạy nội dung `output/cypher/verify.cypher` trong Neo4j Browser. Import lần hai phải không tạo duplicate vì exporter dùng `MERGE` theo ID.
