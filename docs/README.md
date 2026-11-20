# Lộ trình nhập môn KG, RAG, Agent và Multi-Agent

Đây là bộ tài liệu tiếng Việt dành cho người biết căn bản về phần mềm/IT nhưng chưa học AI. Nó tập trung vào cách xây hệ thống có thể kiểm tra và vận hành, thay vì chỉ học thuật ngữ.

## Đọc theo thứ tự này

1. [KG_RAG.md](KG_RAG.md) — hiểu dữ liệu, tìm bằng chứng, Knowledge Graph và RAG.
2. [agent.md](agent.md) — hiểu agent là gì, tool, state, guardrail và quy trình xây dựng agent đơn.
3. [multi_agent.md](multi_agent.md) — chỉ dùng nhiều agent khi thực sự có lợi; học cách điều phối, phân quyền và kiểm thử toàn hệ thống.

## Bản đồ khái niệm

```text
Tài liệu/DB/API
     |
     +--> RAG: tìm các đoạn bằng chứng phù hợp ---------+
     |                                                  |
     +--> KG: mô hình hoá entity và quan hệ đã kiểm chứng +--> Agent dùng tool/tri thức để làm việc
                                                               |
                                                               +--> Multi-agent điều phối nhiều vai trò khi cần
```

- **RAG** trả lời câu hỏi dựa vào các đoạn tài liệu truy hồi được.
- **KG** biểu diễn đối tượng và quan hệ để truy vấn/giải thích tốt hơn.
- **Agent** là lớp điều phối LLM, tri thức và tool để hoàn thành một mục tiêu.
- **Multi-agent** là cách phối hợp nhiều vai trò chuyên biệt; nó là lựa chọn kiến trúc, không phải mặc định.

## Ba nguyên tắc xuyên suốt

1. **Bằng chứng trước, câu trả lời sau.** Gắn nguồn cho chunk, fact và kết luận; không coi nội dung mô hình sinh ra là nguồn.
2. **Quyền tối thiểu.** Kiểm tra quyền trong backend/tool, không chỉ dựa vào prompt.
3. **Bắt đầu nhỏ, đo rồi mới mở rộng.** Một RAG/agent đơn có test tốt thường giá trị hơn một hệ multi-agent phức tạp không quan sát được.

## Gợi ý thực hành với repository này

Repository đã có pipeline HTML → Knowledge Base → Knowledge Graph. Sau khi nắm phần `KG_RAG.md`, hãy xem `README.md` ở thư mục gốc và các artifact trong `data/kb/`, `data/kg/`, `output/cypher/` để liên hệ lý thuyết với pipeline. Đặc biệt, phân biệt `MENTIONS` (đoạn văn nhắc đến thuật ngữ) với assertion y khoa đã được review.

Vì đây là miền sức khoẻ, mọi chatbot/agent triển khai từ dữ liệu này cần giới hạn phạm vi, trích nguồn, bảo vệ dữ liệu cá nhân, không chẩn đoán/ra quyết định lâm sàng tự động và có cơ chế chuyển cho chuyên gia.
