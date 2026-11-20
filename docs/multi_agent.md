# Kiến trúc Multi-Agent

Multi-agent là hệ thống trong đó nhiều agent có vai trò khác nhau cùng phối hợp để đạt một mục tiêu. Có thể xem nó như một nhóm nhỏ: người điều phối nhận việc, chuyên gia tra cứu, người thực thi và người kiểm tra. Mỗi thành viên vẫn là chương trình có giới hạn quyền và công cụ riêng.

## 1. Vì sao không phải lúc nào cũng dùng nhiều agent?

Chia nhỏ công việc có thể tăng tính rõ ràng, chuyên môn hoá và khả năng kiểm tra; nhưng cũng tăng số lời gọi model, độ trễ, chi phí và rủi ro truyền sai bối cảnh. Nhiều agent **không tự động** thông minh hơn một agent hay một workflow tốt.

Hãy bắt đầu bằng một workflow hoặc một agent nếu tác vụ đơn giản. Cân nhắc multi-agent khi ít nhất một điều đúng:

- Có các mảng chuyên môn/công cụ tách biệt rõ (ví dụ tra cứu chính sách, truy vấn dữ liệu, kiểm tra tuân thủ).
- Có thể chạy các nhánh độc lập song song.
- Cần tách quyền hạn để giảm rủi ro (người lập kế hoạch không có quyền ghi dữ liệu).
- Cần bước review độc lập cho đầu ra quan trọng.

## 2. Các vai trò thường gặp

| Vai trò | Trách nhiệm | Quyền gợi ý |
| --- | --- | --- |
| Orchestrator/router | Hiểu mục tiêu, chọn luồng/agent, tổng hợp trạng thái | Điều phối, không nên có quyền nhạy cảm mặc định |
| Planner | Chia mục tiêu thành các bước kiểm tra được | Đọc context và tạo plan |
| Researcher/retriever | Tìm bằng chứng trong KB, web hoặc database được phép | Chỉ đọc |
| Domain specialist | Áp dụng quy tắc/kiến thức ngành vào evidence | Chỉ đọc, đề xuất |
| Executor | Thực hiện thao tác qua tool/API | Quyền ghi tối thiểu cần thiết |
| Critic/verifier | Kiểm tra logic, nguồn, policy, schema | Chỉ đọc và chặn/đề nghị sửa |
| Human approver | Chịu trách nhiệm ở điểm rủi ro cao | Quyền phê duyệt rõ ràng |

Đặt tên theo **trách nhiệm**, không theo phong cách mơ hồ như “super agent”. Một agent chỉ nên có một mục đích chính và input/output rõ.

## 3. Bốn kiểu phối hợp cơ bản

### A. Supervisor/worker (người điều phối và chuyên gia)

```text
Yêu cầu -> Supervisor -> Researcher
                       -> Data agent
                       -> Policy checker
                 -> tổng hợp -> trả lời/đề nghị duyệt
```

Supervisor quyết định gọi worker nào và gom kết quả. Mẫu này dễ khởi đầu, nhưng supervisor có thể thành điểm nghẽn và cần giới hạn quyền.

### B. Pipeline/hand-off tuần tự

```text
Trích xuất -> Chuẩn hoá -> Phân tích -> Kiểm tra -> Xuất kết quả
```

Mỗi agent nhận một artifact có schema. Đây là mẫu dễ debug, phù hợp khi thứ tự cố định. Nhiều trường hợp nên viết thành workflow quyết định thay vì để LLM tự hand-off.

### C. Parallel + aggregator

```text
                   -> Nguồn A --\
Câu hỏi -> router -> Nguồn B ----> aggregator -> verifier -> kết quả
                   -> Nguồn C --/
```

Các nhánh độc lập chạy song song để giảm thời gian. Aggregator phải biết cách xử lý trùng lặp, xung đột và nguồn yếu; không chỉ nối văn bản lại.

### D. Debate/critic loop có giới hạn

Một agent tạo phương án, agent khác phản biện bằng rubric/evidence, rồi agent đầu sửa. Chỉ dùng số vòng hữu hạn và tiêu chí dừng rõ. Tranh luận tự do dài thường tốn kém và không chứng minh được kết quả đúng.

## 4. Nguyên tắc kiến trúc quan trọng

### Hợp đồng (contract) trước prompt

Mỗi agent nên trao đổi qua dữ liệu có cấu trúc: `task_id`, `status`, `evidence_ids`, `result`, `confidence`, `next_action`, `error`. Validate schema ở code. Điều này đáng tin hơn việc một agent viết đoạn văn mơ hồ cho agent sau.

Ví dụ artifact:

```json
{
  "task_id": "case_42",
  "status": "needs_review",
  "answer_draft": "...",
  "evidence": [{"chunk_id": "c_12", "claim": "..."}],
  "risks": ["Nguồn chưa đủ cho khuyến nghị"],
  "requested_action": "human_approval"
}
```

### State dùng chung nhưng có quyền sở hữu

Lưu state trong database/queue thay vì chỉ trong history chat. Xác định agent nào được ghi trường nào, version/optimistic locking, TTL và idempotency key. Nếu nhiều agent cùng cập nhật một ticket mà không có quy tắc, dễ xảy ra race condition hoặc ghi đè.

### Quyền tối thiểu và trust boundary

Agent tra cứu không cần quyền gửi email. Agent điều phối không nhất thiết giữ secret của mọi integration. Thực thi hành động nhạy cảm qua service/backend kiểm tra quyền, chứ không tin agent nói “tôi đã được phép”. Nội dung từ agent khác vẫn nên coi là dữ liệu cần kiểm tra, không phải lệnh cấp hệ thống.

### Bằng chứng hơn là “độ tự tin”

Điểm confidence do LLM tự nói không đủ để quyết định. Hãy ưu tiên evidence, nguồn, validator xác định được, quy tắc nghiệp vụ và human review khi hậu quả cao.

### Giới hạn và khả năng phục hồi

Mọi đồ thị điều phối cần giới hạn depth, số tool call, ngân sách, timeout và retry. Dùng queue cho tác vụ dài; nhận diện task trùng; ghi checkpoint để tiếp tục an toàn. Thiết kế dead-letter queue hoặc hàng chờ review cho lỗi không tự xử lý được.

## 5. Quy trình xây dựng multi-agent

### 1. Chứng minh cần phân chia

Lập danh sách tác vụ, công cụ, quyền và độ phụ thuộc. Nếu một agent/workflow làm tốt, giữ đơn giản. Chỉ tách khi có domain khác nhau, có thể chạy song song, hoặc có boundary quyền/rủi ro rõ.

### 2. Vẽ luồng và điểm quyết định

Viết states và transitions: `received → retrieved → drafted → verified → approved → executed → closed`. Nêu điều kiện chuyển, retry, fail và escalation. Đây là một state machine có kiểm soát, không phải cuộc hội thoại agent vô tận.

### 3. Định nghĩa agent và contract

Mỗi agent cần mục tiêu, input/output schema, tool allowlist, dữ liệu được đọc, hành động được ghi, timeout, budget, tiêu chí thành công và cách báo lỗi. Tránh để hai agent sở hữu cùng một quyết định.

### 4. Xây một vertical slice

Làm luồng nhỏ từ đầu đến cuối với dữ liệu giả/an toàn: router → retriever → draft → verifier → phê duyệt giả lập. Đo trace, lỗi, chi phí trước khi nhân số agent/tool.

### 5. Thêm guardrail và observability

Validation cả trước lẫn sau agent, rate limit, policy engine, phân quyền, secret manager, audit log. Mỗi task có correlation ID xuyên suốt các agent và tool call để có thể replay/debug.

### 6. Đánh giá theo hệ thống, không chỉ từng agent

Test kịch bản end-to-end gồm trạng thái thiếu, nguồn xung đột, công cụ chậm/lỗi, thông điệp độc hại, message trùng, agent không phản hồi và hành động phải được duyệt. Theo dõi completion rate, factuality/grounding, policy violation, p50/p95 latency, chi phí/task, retry và số escalation.

## 6. Ví dụ: trợ lý tri thức về tiểu đường

Đây là ví dụ kiến trúc **tham khảo**, không phải hệ thống chẩn đoán/điều trị tự động.

```text
Người dùng hỏi
    |
Safety/router: phân loại câu hỏi, nhận diện tình huống khẩn cấp
    |
    +--> Retriever: lấy chunk từ KB đã phân quyền
    +--> KG query: tìm entity/quan hệ đã được duyệt
    |
Evidence assembler: gộp nguồn, phát hiện thiếu/xung đột
    |
Answer agent: soạn giải thích phổ thông, trích nguồn
    |
Safety verifier: kiểm tra phạm vi, cảnh báo, citation, không chẩn đoán
    |
Kết quả hoặc chuyển sang chuyên gia/khuyến nghị liên hệ cơ sở y tế
```

Các agent "retriever", "KG query" và "verifier" có thể chỉ là các service deterministic cộng với một ít LLM, không bắt buộc phải là chatbot độc lập. Các quan hệ `pending` trong graph của dự án không nên được đưa vào evidence cho câu trả lời.

## 7. Các anti-pattern thường gặp

- Tạo 5–10 agent vì sơ đồ trông ấn tượng, dù chỉ có một bước cần AI.
- Để agent chat tự do với nhau, không có schema, state machine hoặc giới hạn vòng lặp.
- Một "manager" có toàn bộ secret và quyền ghi mọi hệ thống.
- Tin lời agent trước thay vì xác minh ở API/backend.
- Truyền toàn bộ lịch sử cho mọi agent: vừa tốn, vừa lộ dữ liệu, vừa gây nhiễu.
- Dùng confidence tự báo cáo để tự động duyệt hành động nhạy cảm.
- Không có correlation ID nên không biết câu trả lời được tạo bởi chuỗi nào.

## 8. Checklist quyết định và release

- [ ] Có lý do đo được để dùng nhiều agent thay vì workflow/agent đơn.
- [ ] Vai trò không chồng chéo; mỗi agent có contract và owner.
- [ ] State, concurrency, retry, timeout, idempotency và failure path được thiết kế.
- [ ] Tool/data access theo least privilege và xác thực ở backend.
- [ ] Nguồn/evidence đi cùng artifact; output quan trọng được verifier kiểm tra.
- [ ] Có gate người duyệt cho hành động đối ngoại, dữ liệu nhạy cảm hoặc hậu quả cao.
- [ ] Có end-to-end eval, trace theo task ID, dashboard chi phí/latency/lỗi.
- [ ] Có kill switch, rollback và cách xử lý task đang dở.

