# Giai đoạn 2 — Machine Learning với Pima Indians Diabetes

Ngày thực hiện: 25/11/2026. Mục đích là nghiên cứu hỗ trợ đánh giá nguy cơ, không chẩn đoán hoặc thay thế bác sĩ.

## Công việc và cấu trúc

- `data/diabetes.csv`: đầu vào có sẵn, 768 dòng, 8 đặc trưng và nhãn `Outcome`; không chỉnh sửa.
- `src/notebook/diabetes_prediction.ipynb`: toàn bộ mã phân tích, đồ thị, huấn luyện, đánh giá, SHAP, lưu mô hình và hàm `predict()`; đã lưu cả output khi chạy.
- `output/model/diabetes_pipeline.joblib`: pipeline tiền xử lý và mô hình đã fit, dùng cho đầu vào thô.
- `output/model/diabetes_model.joblib`: estimator đã fit, chỉ dùng với dữ liệu đã qua đúng tiền xử lý của pipeline.

## Phương pháp

Kiểm tra thống kê, giá trị thiếu, trùng lặp, phân bố nhãn, histogram và tương quan. Tập dữ liệu có 500 nhãn 0, 268 nhãn 1, không có dòng trùng toàn bộ; không có ô null. Quy ước xử lý 0 là thiếu với Glucose (5), BloodPressure (35), SkinThickness (227), Insulin (374), BMI (11); Pregnancies bằng 0 vẫn hợp lệ.

Chia phân tầng train/test 80/20, seed 42: 614/154 dòng. Median imputation và StandardScaler nằm trong pipeline và được fit lại riêng ở từng fold. So sánh 5 mô hình với Stratified 5-fold CV trên train, chọn theo F1 trung bình, nếu hòa xét ROC-AUC; test chỉ dùng đánh giá mô hình đã chọn. Đây là một lần chia, không phải đánh giá bên ngoài hoặc xác nhận lâm sàng.

## So sánh cross-validation trên train

Các chỉ số là trung bình 5 fold, không phải kết quả test.

| Mô hình | Accuracy | Precision | Recall | F1 | ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0,7882 | 0,7638 | 0,5748 | 0,6545 | 0,8434 |
| SVM | 0,7801 | 0,7415 | 0,5842 | 0,6485 | 0,8333 |
| Random Forest | 0,7622 | 0,6930 | 0,5843 | 0,6308 | 0,8155 |
| KNN | 0,7296 | 0,6367 | 0,5654 | 0,5939 | 0,7843 |
| Decision Tree | 0,6808 | 0,5417 | 0,5514 | 0,5457 | 0,6507 |

Logistic Regression được chọn theo quy tắc F1 đã định trước, không phải vì khẳng định tối ưu cho lâm sàng.

## Đánh giá test và giải thích

Logistic Regression trên test: Accuracy **0,7078**, Precision **0,6000**, Recall **0,5000**, F1 **0,5455**, ROC-AUC **0,8130**. Confusion matrix `[[82, 18], [27, 27]]` theo thứ tự hàng thực tế 0/1, cột dự đoán 0/1. Có 27 trường hợp dương tính bị dự đoán âm tính; ngưỡng 0,5 chưa được hiệu chỉnh hoặc xác nhận lâm sàng.

Notebook dùng Kernel SHAP trên xác suất lớp 1, mẫu nền 50 dòng train và 20 dòng test minh họa. SHAP giải thích đầu ra mô hình tương đối với mẫu nền, không chứng minh quan hệ nhân quả. Dataset Pima không đại diện cho mọi nhóm dân cư; chưa có kiểm định ngoài, hiệu chuẩn xác suất hay đánh giá lâm sàng. Không áp dụng kết quả để chẩn đoán cá nhân.

## Cách chạy

Môi trường `start_ml`: Python 3.11.15, scikit-learn 1.9.0, SHAP 0.51.0. SHAP và các dependency cần thiết đã được cài vào môi trường này. Mở notebook trong Jupyter với kernel `start_ml`, chạy lần lượt từ đầu; yêu cầu các thư viện pandas, numpy, matplotlib, seaborn, scikit-learn, joblib, shap và Jupyter. Notebook tìm thư mục gốc qua `data/diabetes.csv`. Chạy lại sẽ ghi đè hai file joblib trong `output/model/`.

Sau khi chạy cell định nghĩa hàm, `predict(record)` nhận dict hoặc danh sách dict với đúng tám tên cột đầu vào và trả danh sách nhãn cùng xác suất lớp 1. Tích hợp component khác cần chuyển hàm này cùng danh sách trường vào module riêng và nạp pipeline; dùng cùng phiên bản scikit-learn, chỉ nạp joblib từ nguồn tin cậy. Đầu vào hợp lệ về kiểu và không âm chưa đồng nghĩa hợp lệ về y khoa.

## Kiểm thử

- Chạy thành công toàn bộ notebook bằng kernel Jupyter của `start_ml`, bao gồm 5 mô hình, đồ thị và SHAP.
- Đã nạp pipeline từ joblib và so sánh xác suất dự đoán trên 3 dòng test với pipeline trong bộ nhớ: khớp.
- Đầu vào thiếu trường được `predict()` từ chối. Các kiểm tra này không xác nhận tính đúng đắn lâm sàng.
