# Knowledge Graph (KG) và Retrieval-Augmented Generation (RAG)

Tài liệu này giải thích KG và RAG từ số 0, theo hướng thực hành cho một người có nền tảng IT. Mục tiêu là hiểu **khi nào cần dùng**, **hệ thống gồm những phần nào**, và **xây như thế nào để có thể kiểm tra được câu trả lời**.

## 1. Bức tranh lớn

Một mô hình ngôn ngữ lớn (LLM) như một người rất giỏi diễn đạt: nó có thể tóm tắt, giải thích, viết mã và đối thoại. Tuy nhiên, nó không tự biết toàn bộ tài liệu riêng của công ty, có thể thiếu dữ liệu mới, và đôi khi tạo ra câu trả lời nghe hợp lý nhưng không đúng (hallucination).

RAG giúp LLM **được mở sách trước khi trả lời**. KG giúp biến các sự thật và mối quan hệ quan trọng thành một **bản đồ tri thức** có cấu trúc. Hai kỹ thuật thường bổ sung cho nhau.

```text
Câu hỏi của người dùng
          |
          v
  Tìm bằng chứng phù hợp  <--- RAG: tài liệu/chunk/vector search
          |
          +----> KG: thực thể và quan hệ liên quan
          |
          v
 LLM tổng hợp câu trả lời kèm nguồn
          |
          v
 Câu trả lời có thể kiểm chứng
```

Ví dụ trong y tế: thay vì hỏi LLM "tiểu đường thai kỳ là gì?" từ trí nhớ chung, hệ thống tìm đoạn văn đã được phê duyệt trong tài liệu nội bộ/chuyên môn, có thể đi theo quan hệ trong KG như `Tiểu đường thai kỳ —có_yếu_tố_nguy_cơ→ Thừa cân`, rồi yêu cầu LLM chỉ trả lời dựa trên các đoạn đó. Đây là hỗ trợ thông tin, không thay thế bác sĩ.

## 2. Các khái niệm nền tảng

| Thuật ngữ | Hiểu đơn giản | Ví dụ |
| --- | --- | --- |
| Dữ liệu phi cấu trúc | Văn bản không có cột cố định, khó truy vấn chính xác | PDF, HTML bài viết, email |
| Chunk | Một đoạn văn bản nhỏ, đủ ngữ cảnh để tìm và đưa cho LLM | 1–3 đoạn về triệu chứng |
| Embedding | Dãy số biểu diễn gần đúng ý nghĩa của văn bản | “đường huyết cao” gần “tăng glucose máu” |
| Vector database | Nơi lưu embedding để tìm các đoạn có nghĩa gần câu hỏi | Chroma, Qdrant, pgvector |
| Retrieval | Bước lấy bằng chứng liên quan trước khi sinh câu trả lời | Tìm 5 chunk phù hợp nhất |
| Grounding | Ràng buộc câu trả lời vào nguồn đã lấy được | “Chỉ dùng thông tin trong ngữ cảnh” |
| Entity/thực thể | Một đối tượng có tên/định danh | Bệnh đái tháo đường típ 2 |
| Relation/quan hệ | Liên kết có ý nghĩa giữa các thực thể | `có_triệu_chứng`, `điều_trị_bằng` |
| Provenance/nguồn gốc | Dấu vết cho biết thông tin đến từ đâu | URL, trang, chunk, thời điểm |

## 3. Knowledge Graph (KG)

### 3.1. KG là gì?

Knowledge Graph là cách lưu tri thức dưới dạng các **nút** (node) và **cạnh** (edge). Mỗi cạnh diễn đạt một mệnh đề có hướng: `chủ thể — quan hệ → đối tượng`.

```text
[Đái tháo đường típ 2] --có_yếu_tố_nguy_cơ--> [Thừa cân/béo phì]
             |
             +--có_biến_chứng--> [Bệnh thận mạn]
```

Không phải mọi liên kết đều là tri thức y khoa. Ví dụ, `chunk —MENTIONS→ thực thể` chỉ nói rằng đoạn văn có nhắc tới thuật ngữ. Một quan hệ y khoa như `gây_ra`, `điều_trị_bằng`, `chống_chỉ_định` phải có bằng chứng, định nghĩa rõ và thường cần chuyên gia duyệt.

### 3.2. Thành phần của KG

1. **Schema/ontology nhẹ**: quy tắc về loại nút và loại quan hệ được phép. Không cần bắt đầu bằng một ontology khổng lồ.
2. **Entity**: thực thể chuẩn hoá, có ID ổn định, tên hiển thị, tên chuẩn và các từ đồng nghĩa.
3. **Relation**: quan hệ có tên rõ, hướng rõ, có miền/đích hợp lệ. Ví dụ `Disease -[HAS_SYMPTOM]-> Symptom`.
4. **Thuộc tính**: dữ liệu mô tả như ngày cập nhật, độ tin cậy, mã chuẩn.
5. **Bằng chứng và provenance**: nguồn, trích dẫn ngắn, vị trí và người/qui trình duyệt.

Trong Neo4j, một biểu diễn đơn giản có thể là:

```cypher
(:Disease {id: 'dmt2', name: 'Đái tháo đường típ 2'})
  -[:HAS_RISK_FACTOR {evidence_id: 'ev_123'}]->
(:Concept {id: 'obesity', name: 'Béo phì'})
```

Nếu quan hệ là nhạy cảm hoặc còn chờ xác minh, đừng đưa thẳng nó vào "sự thật" của graph. Hãy lưu nó như một **candidate** có trạng thái `pending`, bằng chứng và quyết định review.

### 3.3. Đặc điểm, ưu và giới hạn

**Điểm mạnh**

- Truy vấn quan hệ nhiều bước tốt: “biến chứng nào liên quan đến bệnh X và có yếu tố nguy cơ Y?”.
- Dễ giải thích đường suy luận: có thể xem các nút/cạnh đã đi qua.
- Hợp nhất được nhiều nguồn và từ đồng nghĩa vào cùng một thực thể chuẩn.
- Phù hợp với luật, kiểm soát quyền truy cập và phân tích mạng lưới.

**Điểm cần đánh đổi**

- Tốn công thiết kế schema, làm sạch tên gọi, gộp trùng và duyệt quan hệ.
- KG không thay thế toàn văn: các ngoại lệ, câu phủ định và sắc thái thường nằm trong tài liệu gốc.
- Tri thức thay đổi nhanh sẽ cần version, ngày hiệu lực và quy trình cập nhật.
- Nếu schema quá cứng hoặc quá chi tiết từ đầu, chi phí bảo trì tăng mạnh.

### 3.4. Ứng dụng tiêu biểu

- Hỏi đáp có giải thích và truy vết nguồn.
- Tìm kiếm theo ngữ nghĩa và quan hệ (drug discovery, fraud, knowledge management).
- Customer 360: nối khách hàng, sản phẩm, giao dịch và tương tác.
- Recommendation: gợi ý qua thuộc tính/quan hệ, không chỉ qua hành vi giống nhau.
- Data lineage và impact analysis: biết báo cáo nào bị ảnh hưởng nếu một bảng thay đổi.

## 4. RAG

### 4.1. RAG là gì?

RAG (Retrieval-Augmented Generation) là kiến trúc gồm hai việc:

1. **Retrieval**: tìm phần tài liệu phù hợp với câu hỏi.
2. **Generation**: đưa câu hỏi và phần tài liệu đó cho LLM để soạn câu trả lời.

Điểm cốt lõi: LLM không tự suy đoán ngoài bằng chứng có sẵn. Khi thiếu bằng chứng, nó phải nói không tìm thấy hoặc đề nghị làm rõ.

### 4.2. Luồng RAG cơ bản

```text
Tài liệu nguồn
  -> trích xuất/làm sạch -> chia chunk -> tạo embedding -> index

Câu hỏi
  -> embedding/keyword -> truy hồi top-k chunk -> (rerank, lọc quyền)
  -> prompt gồm câu hỏi + bằng chứng -> LLM trả lời + trích nguồn
```

**Ingestion/indexing** xảy ra trước và định kỳ. **Query serving** xảy ra mỗi khi người dùng hỏi. Tách hai luồng giúp dễ kiểm tra, cập nhật và tối ưu chi phí.

### 4.3. Những quyết định kỹ thuật quan trọng

| Quyết định | Gợi ý ban đầu | Rủi ro nếu làm kém |
| --- | --- | --- |
| Chia chunk | Chia theo tiêu đề/đoạn, có thể overlap nhỏ; giữ metadata | Chunk quá dài gây nhiễu, quá ngắn mất ngữ cảnh |
| Metadata | Lưu nguồn, tiêu đề, section, ngày, quyền, ngôn ngữ | Không thể lọc theo quyền hay trích dẫn |
| Retrieval | Kết hợp keyword (BM25) và vector là điểm khởi đầu tốt | Chỉ vector có thể bỏ sót tên/mã chính xác |
| Reranking | Dùng mô hình/rule đánh lại top kết quả trước khi gửi LLM | Kết quả đầu vào kém làm câu trả lời kém |
| Prompt | Nêu rõ phạm vi nguồn, cách trích dẫn, hành vi khi thiếu dữ kiện | LLM bịa, lẫn nguồn, trả lời quá tự tin |
| Citation | Hiện tên tài liệu + section/URL/chunk có thể mở | Người dùng không kiểm chứng được |

### 4.4. RAG không phải phép màu

RAG giảm nhưng không xoá hoàn toàn hallucination. Câu trả lời vẫn có thể sai nếu tài liệu nguồn sai/cũ, truy hồi nhầm, prompt yếu, hoặc mô hình suy luận quá đà. Vì vậy cần quan sát cả chuỗi: chất lượng tài liệu, retrieval, câu trả lời và phản hồi người dùng.

Không nên dùng RAG để né các yêu cầu an toàn: dữ liệu nhạy cảm vẫn phải phân quyền, mã hoá, ghi audit log và tuân thủ quy định. Với y tế/pháp lý/tài chính, cần tuyên bố phạm vi, đánh giá bởi chuyên gia và cơ chế chuyển sang con người.

## 5. KG và RAG: khác nhau và kết hợp ra sao?

| Khía cạnh | KG | RAG trên tài liệu | GraphRAG/KG-RAG |
| --- | --- | --- | --- |
| Đơn vị chính | Entity và quan hệ | Đoạn văn/chunk | Cả graph lẫn chunk |
| Giỏi nhất | Câu hỏi quan hệ, truy vết | Câu hỏi cần chi tiết nguyên văn | Câu hỏi cần cả liên kết và ngữ cảnh |
| Cập nhật | Cần chuẩn hoá/review | Có thể index nhanh | Có hai luồng cần đồng bộ |
| Rủi ro chính | Quan hệ sai, schema nặng | Lấy nhầm/thiếu chunk | Phức tạp, chi phí/vận hành cao |
| Dùng khi | Quan hệ là tài sản cốt lõi | Có kho tài liệu tốt, muốn ra MVP | Bài toán thực sự cần liên kết đa bước |

**GraphRAG** không phải một sản phẩm cố định; đó là họ kiến trúc dùng graph để mở rộng hoặc định hướng retrieval. Một cách đơn giản và hữu ích là: tìm chunk liên quan → nhận diện thực thể → mở rộng 1–2 hop có kiểm soát trong KG → lấy bằng chứng của các quan hệ → đưa cả văn bản và graph facts đã duyệt vào LLM.

Đừng chọn GraphRAG chỉ vì nó "mới". Hãy bắt đầu bằng search/RAG tối giản nếu vấn đề chủ yếu là hỏi đáp tài liệu; thêm KG khi cần hợp nhất định danh, truy vấn quan hệ, giải thích đường đi hoặc có domain ontology giá trị.

## 6. Quy trình xây dựng theo từng giai đoạn

### Giai đoạn A — Xác định bài toán và thước đo

- Viết 20–50 câu hỏi thật của người dùng, không chỉ câu hỏi dễ.
- Xác định người dùng, dữ liệu được phép dùng, câu trả lời nào bị cấm/rủi ro cao.
- Chọn chỉ số: retrieval recall@k, citation correctness, faithfulness (bám nguồn), độ hữu ích, latency, chi phí và tỷ lệ chuyển người thật.
- Đặt "đường thoát": không đủ bằng chứng thì nói gì, và ai tiếp nhận.

### Giai đoạn B — Chuẩn bị tri thức

- Lập inventory nguồn; phân loại nguồn đáng tin, chủ sở hữu, phiên bản, ngày cập nhật và quyền truy cập.
- Trích xuất có cấu trúc từ HTML/PDF/DOCX; giữ bản gốc bất biến.
- Làm sạch có kiểm soát, đặc biệt không làm mất câu phủ định, đơn vị, bảng, tiêu đề và nguồn.
- Chunk theo cấu trúc tài liệu, gắn ID ổn định, offset/locator và hash để tái lập.

### Giai đoạn C — Xây RAG tối thiểu

- Tạo embedding và index; dùng hybrid retrieval khi dữ liệu có thuật ngữ/mã chuyên ngành.
- Hiển thị nguồn của từng câu trả lời.
- Tạo bộ test câu hỏi có đáp án/bằng chứng mong đợi; đo trước khi tối ưu.
- Ghi log câu hỏi đã ẩn danh phù hợp, chunk truy hồi, phiên bản index/model và phản hồi.

### Giai đoạn D — Bổ sung KG khi có lý do rõ ràng

- Chọn ít loại entity/relation có ích nhất; viết định nghĩa và ví dụ/phản ví dụ.
- Chuẩn hoá aliases, deduplicate và gắn ID. Tách **mention** khỏi **assertion**.
- Trích xuất candidate có evidence; người/chính sách duyệt các quan hệ quan trọng.
- Validate schema, nguồn gốc, loại thực thể, quan hệ, thời gian hiệu lực và sự mâu thuẫn.

### Giai đoạn E — Kết hợp, triển khai và cải tiến

- Chỉ mở rộng graph với quan hệ đã được duyệt và giới hạn số hop/kết quả.
- Phân quyền trước retrieval, không phải chỉ che kết quả sau khi sinh.
- Dùng feature flags/canary khi đổi index, prompt, embedding hoặc schema.
- Review các câu trả lời sai theo nguyên nhân: nguồn, parsing, chunking, retrieval, graph, prompt hay mô hình.

## 7. Kiểm thử và đánh giá

Một hệ RAG/KG đáng tin không chỉ có demo đẹp. Nó cần các tập test lặp lại được.

| Lớp kiểm thử | Câu hỏi cần trả lời |
| --- | --- |
| Data | Có mất bảng, phủ định, đơn vị, metadata hay quyền truy cập không? |
| Retrieval | Bằng chứng đúng có xuất hiện trong top-k không? |
| Graph | Nút/cạnh có đúng schema, đúng nguồn, không trùng và có trạng thái review không? |
| Generation | Mỗi mệnh đề quan trọng có được nguồn hỗ trợ không? Có bịa thêm không? |
| Safety | Có lộ dữ liệu, trả lời vượt phạm vi, xử lý prompt injection trong tài liệu không? |
| Operations | Có quan sát được phiên bản, lỗi, latency, chi phí và rollback không? |

Hai khái niệm hay bị nhầm:

- **Correctness**: câu trả lời có đúng với thực tế không? Thường cần chuyên gia domain.
- **Faithfulness**: câu trả lời có bám bằng chứng đã lấy hay không? Có thể đo bằng review/LLM-as-judge nhưng nên audit mẫu.

## 8. Liên hệ với dự án này

Pipeline hiện tại đã có nhiều nền móng tốt cho KG/RAG có trách nhiệm: giữ HTML nguồn, trích xuất tài liệu, tạo chunk có offsets/hash, entity matching, `MENTIONS`, assertion candidates, review CSV, validation và xuất Cypher Neo4j. Đây là cách tách rõ **dữ liệu đọc được** khỏi **khẳng định chuyên môn đã duyệt**.

Để tiến tới RAG, có thể bổ sung một lớp index cho `data/kb/chunks.jsonl`, lưu embedding cùng `chunk_id` và metadata nguồn; sau đó xây API truy hồi/citation. Không nên biến các assertion `pending` thành dữ kiện cho chatbot. Với nội dung sức khoẻ, chỉ dùng quan hệ đã duyệt, giữ cảnh báo phù hợp và thiết kế luồng khuyến khích người dùng trao đổi với chuyên gia khi cần.

## 9. Checklist trước khi đưa vào sử dụng

- [ ] Có câu hỏi thật, chỉ số đo và tiêu chí không trả lời.
- [ ] Mỗi chunk/fact truy ngược được đến nguồn và phiên bản.
- [ ] Kiểm soát quyền dữ liệu trước retrieval.
- [ ] Có citation người dùng có thể mở/kiểm tra.
- [ ] Quan hệ quan trọng có định nghĩa, evidence và review.
- [ ] Có test regressions cho retrieval, graph và câu trả lời.
- [ ] Log/audit không ghi dữ liệu nhạy cảm quá mức; có retention policy.
- [ ] Có owner, lịch cập nhật, theo dõi chi phí/latency và phương án rollback.

