# Giai đoạn 6 — Rule Engine xét nghiệm đái tháo đường

Ngày thực hiện: 25/11/2026. Công cụ phục vụ học tập, hỗ trợ tham khảo, không chẩn đoán hoặc thay thế bác sĩ. Các quy tắc chưa được chuyên gia lâm sàng thẩm định cho việc sử dụng với bệnh nhân.

## Cấu trúc và công việc

- `config/medical_rules.json`: 11 quy tắc IF–THEN, mỗi quy tắc có mã, loại, khoảng ngưỡng, thông điệp và nguồn.
- `src/rule_engine/engine.py`: đọc JSON, kiểm tra dữ liệu và điều kiện áp dụng, thực thi bằng so sánh số xác định, trả kết quả có nguồn.
- `src/rule_engine/__main__.py`: nhận một đối tượng JSON từ stdin, in kết quả JSON ra stdout.
- `tests/test_rule_engine.py`: kiểm tra tất cả quy tắc, các giá trị tại và sát ngưỡng, dữ liệu thiếu/sai và cảnh báo an toàn.

Không dùng LLM, không thay đổi KB/KG và không biến các mục demo thành tri thức đã duyệt. Engine xử lý từng kết quả độc lập, không đưa ra chẩn đoán tổng hợp hoặc quyết định điều trị.

## Quy tắc và nguồn

Các ngưỡng xét nghiệm áp dụng cho người không mang thai dựa trên [NIDDK — Diabetes Tests & Diagnosis](https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis). Giá trị dưới ngưỡng không loại trừ bệnh. Chẩn đoán cần bác sĩ xem xét; việc xác nhận thường cần xét nghiệm bổ sung tùy bối cảnh.

| Xét nghiệm | Dưới khoảng tiền đái tháo đường | Khoảng tiền đái tháo đường | Đạt ngưỡng xét nghiệm đái tháo đường |
| --- | ---: | ---: | ---: |
| HbA1c | < 5,7% | ≥ 5,7% và < 6,5% | ≥ 6,5% |
| Glucose huyết tương lúc đói (FPG) | < 100 mg/dL | ≥ 100 và < 126 mg/dL | ≥ 126 mg/dL |
| Glucose huyết tương OGTT 2 giờ | < 140 mg/dL | ≥ 140 và < 200 mg/dL | ≥ 200 mg/dL |

Hai quy tắc cảnh báo glucose theo [CDC — Low Blood Sugar](https://www.cdc.gov/diabetes/about/low-blood-sugar-hypoglycemia.html): dưới 54 mg/dL là cảnh báo rất thấp; từ 54 đến dưới 70 mg/dL là cảnh báo thấp. Các cảnh báo này được đánh giá độc lập với điều kiện diễn giải xét nghiệm, miễn loại glucose, giá trị và đơn vị hợp lệ.

## Hợp đồng đầu vào

Mỗi lời gọi xử lý một object JSON với `test_type`, `value`, `unit`. `value` là số hữu hạn lớn hơn 0; chuỗi số, boolean, số âm, 0, NaN và vô cực bị từ chối. Đơn vị được chấp nhận đúng theo chữ hoa/thường: HbA1c `%`, glucose `mg/dL`. Chưa hỗ trợ tự chuyển mmol/L.

| `test_type` | Các trường thêm bắt buộc để diễn giải ngưỡng |
| --- | --- |
| `hba1c` | `pregnant: false`, `lab_certified: true`, `a1c_interference: false` |
| `fpg` | `pregnant: false`, `sample: "plasma"`, `fasting_hours` là số ≥ 8 |
| `ogtt_2h` | `pregnant: false`, `sample: "plasma"`, `glucose_load_g: 75`, `elapsed_minutes: 120` |
| `glucose_random`, `glucose_meter` | Chỉ áp dụng quy tắc cảnh báo glucose thấp; không diễn giải ngưỡng chẩn đoán |

Nếu trường cần thiết bị thiếu, sai kiểu hoặc điều kiện không áp dụng, kết quả có `issues` và không diễn giải ngưỡng xét nghiệm. Glucose hợp lệ vẫn có thể tạo `alerts`; các thành phần tích hợp phải đọc **cả** `alerts` lẫn `issues`, không dừng xử lý cảnh báo chỉ vì có lỗi khác. `pregnant` không được suy đoán từ thông tin thiếu. Chưa xử lý đái tháo đường thai kỳ, glucose ngẫu nhiên với triệu chứng, các loại đơn vị khác, hay mọi yếu tố gây sai lệch HbA1c. `lab_certified` và `a1c_interference` là thông tin người gọi khai báo, không tự xác minh được. Các trường hợp ngoài phạm vi cần chuyên gia xử lý.

Output gồm `rule_version`, `disclaimer`, `issues`, `results`, `alerts`; mỗi kết quả/cảnh báo có `rule_id`, thông điệp và nguồn. CLI trả mã 0 nếu không có `issues`, 1 nếu có `issues` (vẫn có thể có `alerts`), 2 nếu input JSON sai hoặc không phải object.

## Cách chạy

Từ thư mục gốc dự án, với Python trong `start_ml`:

```powershell
$env:PYTHONPATH='src'
'{"test_type":"fpg","value":126,"unit":"mg/dL","pregnant":false,"sample":"plasma","fasting_hours":8}' | python -m rule_engine
python -m pytest tests/test_rule_engine.py -q
```

Trong Python: `from rule_engine import evaluate`, sau đó gọi `evaluate(measurement)` với dict như hợp đồng trên. Ví dụ 126 là dữ liệu đầu vào kiểm thử ngưỡng, không phải dữ liệu bệnh nhân hay kết quả thực nghiệm.

## Kết quả kiểm thử

- `tests/test_rule_engine.py`: 36/36 đạt, bao phủ 11 ID quy tắc và biên 5,7; 6,5; 100; 126; 140; 200; 54; 70, cùng các giá trị lân cận.
- Kiểm thử missing/invalid, sai điều kiện áp dụng, mẫu và đơn vị, và cảnh báo an toàn khi thiếu điều kiện diễn giải: đạt.
- Kiểm thử CLI JSON với FPG 126 mg/dL và điều kiện hợp lệ: trả `fpg_at_least_126` kèm nguồn, exit code 0.
- Kiểm thử hồi quy `test_common.py`, `test_demo_graph.py`, `test_rag.py`, `test_rule_engine.py`: 45/45 đạt; một cảnh báo deprecation từ plugin anyio. Không chạy `test_validation.py` trong lượt này.

Việc đạt unit test chứng minh logic hoạt động với trường hợp đã kiểm tra, không chứng minh tính đầy đủ hoặc an toàn lâm sàng. Cần rà soát y khoa, xác nhận đầu vào và kiểm thử bổ sung trước mọi ứng dụng thực tế.
