# AI Agent: từ chatbot biết trả lời đến hệ thống biết làm việc

AI agent là một chương trình dùng AI (thường là LLM) để **nhận mục tiêu, quan sát bối cảnh, chọn bước tiếp theo và dùng công cụ để hoàn thành việc**. Agent không chỉ tạo văn bản; nó có thể tìm thông tin, gọi API, truy vấn cơ sở dữ liệu, chạy một luồng nghiệp vụ hoặc yêu cầu con người phê duyệt.

## 1. Phân biệt các khái niệm thường bị lẫn

| Khái niệm | Nó làm gì? | Ví dụ |
| --- | --- | --- |
| LLM | Sinh/hiểu ngôn ngữ và một số dạng dữ liệu khác | Tóm tắt một email |
| Chatbot | Giao diện trò chuyện dùng LLM hoặc luật | Trả lời FAQ |
| Workflow tự động | Chuỗi bước cố định do người lập trình | Mỗi đêm import file CSV rồi gửi báo cáo |
| AI agent | Quyết định bước kế tiếp trong phạm vi được trao | Đọc yêu cầu, tìm tài liệu, soạn nháp, gửi duyệt |
| Tool/function | Khả năng hành động rõ ràng của agent | `search_kb`, `create_ticket`, `get_order` |

Agent **không phải người thay thế hoàn toàn**. Nó là một thành phần phần mềm có mức tự chủ được giới hạn. Hệ thống tốt phải xác định rõ: nó được đọc gì, làm gì, được phép quyết định đến đâu, và khi nào dừng/chuyển cho người.

## 2. Mô hình tinh thần đơn giản

Hãy hình dung một nhân viên mới có sách hướng dẫn và bộ công cụ. Nhân viên nhận một mục tiêu, xem thông tin hiện có, chọn công cụ, kiểm tra kết quả rồi báo cáo. Agent hoạt động tương tự, nhưng mỗi bước là lời gọi mô hình/công cụ có thể được log và kiểm soát.

```text
Mục tiêu + ràng buộc
        |
        v
Quan sát trạng thái / lấy tri thức (RAG, DB, API)
        |
        v
Suy luận và lập kế hoạch ngắn
        |
        v
Chọn/gọi tool -----> kết quả hoặc lỗi
        ^                 |
        |-----------------+
        |
Hoàn tất / xin người duyệt / dừng an toàn
```

Vòng lặp này thường gọi là **observe → reason/plan → act → verify**. Không phải agent nào cũng cần tự lập kế hoạch dài; với thao tác có rủi ro, workflow rõ ràng thường an toàn hơn.

## 3. Các thành phần kiến trúc

1. **Instructions (system prompt)**: vai trò, mục tiêu, giới hạn, cách xử lý khi thiếu dữ kiện. Prompt là chính sách hỗ trợ, không phải ranh giới bảo mật duy nhất.
2. **Model**: LLM biến ngôn ngữ/bối cảnh thành câu trả lời hoặc tool call có cấu trúc.
3. **Tools**: hàm/API có schema đầu vào-đầu ra rõ, ví dụ tìm KB hoặc tạo ticket.
4. **Knowledge/context**: RAG, KG, database, hồ sơ phiên làm việc. Chỉ nạp đúng phần cần thiết.
5. **State/memory**: trạng thái công việc (bền vững) khác với lịch sử hội thoại (ngắn hạn). Chỉ lưu dữ liệu cần thiết và có TTL/retention policy.
6. **Orchestrator**: quản lý vòng lặp, timeout, retry, giới hạn bước/chi phí và routing.
7. **Guardrails**: xác thực đầu vào, kiểm tra tool arguments, quyền, policy, redaction và human approval.
8. **Observability/evaluation**: trace, log có bảo vệ, metric, replay test và audit.

## 4. Đặc điểm của một agent tốt

- **Goal-oriented**: tối ưu để đạt một mục tiêu cụ thể, không chỉ trò chuyện lan man.
- **Tool-aware**: biết khi nào cần lấy dữ liệu thật thay vì đoán.
- **Stateful khi cần**: nhớ tiến độ công việc bằng dữ liệu có cấu trúc, không phụ thuộc hoàn toàn vào prompt dài.
- **Bounded autonomy**: tự động trong vùng an toàn, xin duyệt ở ngưỡng rủi ro.
- **Verifiable**: kiểm tra kết quả tool và đưa bằng chứng/trace khi phù hợp.
- **Recoverable**: idempotency, retry có kiểm soát, rollback hoặc công việc chờ xử lý khi lỗi.
- **Observable**: biết request nào, model/tool/version nào đã tạo ra kết quả.

## 5. Khi nào nên và không nên dùng agent?

Nên dùng agent khi tác vụ có ngôn ngữ không cấu trúc, cần chọn công cụ/nguồn theo ngữ cảnh, có nhiều biến thể nhưng vẫn có thể kiểm soát. Ví dụ: phân loại và soạn nháp email hỗ trợ, trợ lý tra cứu chính sách có citation, triage ticket, hỗ trợ developer tìm tài liệu và mở issue nháp.

Không nên bắt đầu bằng agent khi quy trình đã hoàn toàn xác định, hậu quả sai lớn và chưa có kiểm soát, hoặc chỉ cần một form/API/cron job đơn giản. "Một workflow tốt có một bước AI" thường đáng tin hơn "một agent tự do" cho việc như thanh toán, xoá dữ liệu, thay đổi quyền hoặc quyết định y tế.

## 6. Quy trình xây dựng một agent

### Bước 1 — Đóng khung nhiệm vụ

Viết một câu mục tiêu có thể đo: “Tạo bản nháp phản hồi cho ticket theo chính sách đã duyệt, không tự gửi.” Xác định đầu vào, đầu ra, ai dùng, công cụ/dữ liệu được phép, rủi ro và điều kiện hoàn tất.

### Bước 2 — Vẽ happy path trước

Mô tả từng bước một người làm giỏi sẽ thực hiện. Tự động hoá những bước chắc chắn bằng code/workflow; chỉ đặt LLM ở nơi cần hiểu ngôn ngữ, phân loại mơ hồ, tóm tắt hoặc chọn trong các phương án.

### Bước 3 — Thiết kế tools nhỏ và an toàn

Một tool nên làm một việc rõ ràng, có input/output JSON rõ, xác thực tham số và quyền server-side. Tách tool đọc (an toàn hơn) với tool ghi/tạo/xoá. Với tool có side effect, dùng idempotency key, preview/dry-run và/hoặc approval token.

Ví dụ schema ý tưởng:

```json
{
  "name": "search_policy",
  "input": {"query": "string", "department": "string?"},
  "output": {"results": [{"id": "string", "text": "string", "source": "string"}]}
}
```

### Bước 4 — Thêm tri thức và trạng thái đúng mức

Đưa quy định/tài liệu vào RAG thay vì nhét toàn bộ vào prompt. Lưu trạng thái theo công việc, ví dụ `ticket_id`, `status`, `evidence_ids`, `approval_id`; không chỉ bảo agent “hãy nhớ”. Phân tách dữ liệu của các người dùng/tenant.

### Bước 5 — Thiết kế safety và human-in-the-loop

Xếp hạng hành động theo rủi ro:

| Mức | Ví dụ | Cách xử lý |
| --- | --- | --- |
| Thấp | Đọc KB, tạo bản nháp | Tự chạy, log |
| Trung bình | Tạo ticket, gửi nội bộ | Xác thực dữ liệu, có thể cần xác nhận |
| Cao | Gửi ra ngoài, đổi dữ liệu quan trọng | Hiển thị preview và yêu cầu phê duyệt rõ ràng |
| Cấm | Lộ bí mật, vượt quyền, hành vi trái policy | Chặn ở backend, không chỉ chặn bằng prompt |

Đề phòng prompt injection: nội dung từ web/email/tài liệu là **dữ liệu không tin cậy**, không phải chỉ thị hệ thống. Không cho nó tự thay đổi tool policy, tiết lộ secret hay gọi thao tác nhạy cảm.

### Bước 6 — Đánh giá trước và sau khi triển khai

Tạo bộ case đại diện: bình thường, thiếu dữ liệu, dữ liệu mâu thuẫn, yêu cầu vượt quyền, tool lỗi, prompt injection và ngôn ngữ mơ hồ. Đo độ hoàn thành, chính xác, tỷ lệ escalation, lỗi tool, latency và chi phí. Giữ test regression cho mọi bug quan trọng.

### Bước 7 — Vận hành

Đặt giới hạn số vòng lặp, ngân sách token/tool, timeout, retry có backoff và circuit breaker. Ghi trace có ID liên kết; che PII/secret; version hoá prompt, tool schema, model và knowledge index. Triển khai nhỏ, quan sát, rồi mới tăng quyền tự chủ.

## 7. Các mẫu thiết kế phổ biến

| Mẫu | Ý tưởng | Dùng khi |
| --- | --- | --- |
| Router | Phân loại yêu cầu rồi chuyển đến workflow/chuyên gia phù hợp | Nhiều loại yêu cầu rõ |
| Retrieval agent | Tìm nguồn, đọc và trả lời kèm citation | Hỏi đáp tài liệu |
| Plan-and-execute | Lập kế hoạch ngắn rồi làm/kiểm tra từng bước | Tác vụ nhiều bước, có thể quan sát |
| ReAct | Xen kẽ suy luận và gọi tool theo kết quả mới | Cần khám phá có kiểm soát |
| Critic/verifier | Một bước riêng kiểm tra output trước khi trả về | Tác vụ cần chất lượng cao |
| Human approval gate | Dừng chờ người duyệt trước side effect | Tác vụ hậu quả đáng kể |

Không cần phơi bày “chuỗi suy nghĩ” nội bộ của mô hình cho người dùng. Thay vào đó, hãy hiển thị kế hoạch ngắn, tool đã dùng, bằng chứng và lý do ở mức phù hợp.

## 8. Các lỗi triển khai phổ biến

- Gọi mọi thứ là agent dù chỉ là chatbot; kết quả là không có tiêu chí thành công.
- Cho mô hình gọi API ghi/xoá dữ liệu trực tiếp mà không kiểm tra backend.
- Nhét toàn bộ tài liệu và history vào context: đắt, nhiễu, dễ quá giới hạn context.
- Tin rằng prompt một mình bảo vệ được dữ liệu/quyền.
- Không xử lý tool error, retry vô hạn hoặc hành động lặp khi timeout.
- Đánh giá bằng vài demo thay vì tập case thực và adversarial.
- Lưu memory quá lâu, không tách user/tenant hoặc lưu cả secret/PII không cần thiết.

## 9. Checklist release

- [ ] Mục tiêu, phạm vi và định nghĩa hoàn tất được viết rõ.
- [ ] Mỗi tool có schema, phân quyền và validation server-side.
- [ ] Hành động có side effect có idempotency, preview/approval phù hợp.
- [ ] Có giới hạn vòng lặp, token, thời gian và chi phí.
- [ ] Dữ liệu/RAG có nguồn, quyền và chính sách retention.
- [ ] Có test lỗi tool, thiếu dữ liệu, injection, vượt quyền và rollback.
- [ ] Có trace/audit, dashboard chỉ số và người chịu trách nhiệm vận hành.
- [ ] Có cách tắt nhanh hoặc chuyển về workflow thủ công.

