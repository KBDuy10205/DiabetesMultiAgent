# Báo cáo chất lượng Knowledge Base / Knowledge Graph

## Trạng thái

- Validation: đạt.
- Neo4j import: chưa kiểm chứng trong môi trường này.

## Số lượng

- sources: 33
- chunks: 153
- entities: 6
- mentions: 1785
- approved_assertions: 0
- knowledge_cypher_sha256: 3d69f6733cf88f82abde1ffc58d09369dc2b0e7164e891001dbaa93f42199645

## Cần kiểm tra thủ công

- `data/raw/html/10 dấu hiệu tiểu đường thường gặp và cách nhận biết sớm_files/sitecontext.min.html`: too_little_extracted_text
- `data/raw/html/Chỉ số tiểu đường bao nhiêu thì nguy hiểm__files/sitecontext.min.html`: too_little_extracted_text
- `data/raw/html/Dấu Hiệu Bệnh Tiểu Đường Sớm Cần Biết _ Vinmec _ Vinmec_files/149.html`: too_little_extracted_text
- `data/raw/html/Dấu Hiệu Bệnh Tiểu Đường Sớm Cần Biết _ Vinmec _ Vinmec_files/anchor.html`: too_little_extracted_text
- `data/raw/html/Dấu Hiệu Bệnh Tiểu Đường Sớm Cần Biết _ Vinmec _ Vinmec_files/null(1).html`: too_little_extracted_text
- `data/raw/html/Dấu Hiệu Bệnh Tiểu Đường Sớm Cần Biết _ Vinmec _ Vinmec_files/null.html`: too_little_extracted_text
- `data/raw/html/Dấu Hiệu Bệnh Tiểu Đường Sớm Cần Biết _ Vinmec _ Vinmec_files/saved_resource(1).html`: too_little_extracted_text
- `data/raw/html/Dấu Hiệu Bệnh Tiểu Đường Sớm Cần Biết _ Vinmec _ Vinmec_files/saved_resource(2).html`: too_little_extracted_text
- `data/raw/html/Dấu Hiệu Bệnh Tiểu Đường Sớm Cần Biết _ Vinmec _ Vinmec_files/saved_resource(3).html`: too_little_extracted_text
- `data/raw/html/Dấu Hiệu Bệnh Tiểu Đường Sớm Cần Biết _ Vinmec _ Vinmec_files/saved_resource(4).html`: too_little_extracted_text
- `data/raw/html/Dấu Hiệu Bệnh Tiểu Đường Sớm Cần Biết _ Vinmec _ Vinmec_files/saved_resource.html`: too_little_extracted_text
- `data/raw/html/Phân biệt chi tiết tiểu đường type 1 và type 2 theo hướng dẫn của Bộ Y tế _ Vinmec_files/146.html`: too_little_extracted_text
- `data/raw/html/Phân biệt chi tiết tiểu đường type 1 và type 2 theo hướng dẫn của Bộ Y tế _ Vinmec_files/null(1).html`: too_little_extracted_text
- `data/raw/html/Phân biệt chi tiết tiểu đường type 1 và type 2 theo hướng dẫn của Bộ Y tế _ Vinmec_files/null.html`: too_little_extracted_text
- `data/raw/html/Đái tháo đường (tiểu đường)_ Nguyên nhân, chẩn đoán, điều trị_files/sitecontext.min.html`: too_little_extracted_text
- `data/raw/html/Đái tháo đường thai kỳ và chế độ dinh dưỡng cho đái tháo đường thai kỳ _ Vinmec_files/84.html`: too_little_extracted_text
- `data/raw/html/Đái tháo đường thai kỳ và chế độ dinh dưỡng cho đái tháo đường thai kỳ _ Vinmec_files/null(1).html`: too_little_extracted_text
- `data/raw/html/Đái tháo đường thai kỳ và chế độ dinh dưỡng cho đái tháo đường thai kỳ _ Vinmec_files/null.html`: too_little_extracted_text
- `data/raw/html/Đái tháo đường thai kỳ và chế độ dinh dưỡng cho đái tháo đường thai kỳ _ Vinmec_files/saved_resource.html`: too_little_extracted_text
- `data/raw/html/Đái tháo đường_ Triệu chứng, nguyên nhân, chẩn đoán và điều trị_files/saved_resource(1).html`: too_little_extracted_text
- `data/raw/html/Đái tháo đường_ Triệu chứng, nguyên nhân, chẩn đoán và điều trị_files/saved_resource(2).html`: too_little_extracted_text
- `data/raw/html/Đái tháo đường_ Triệu chứng, nguyên nhân, chẩn đoán và điều trị_files/saved_resource(3).html`: too_little_extracted_text
- `data/raw/html/Đái tháo đường_ Triệu chứng, nguyên nhân, chẩn đoán và điều trị_files/saved_resource.html`: too_little_extracted_text
- `data/raw/pdf/Phac-do-Bo-Y-Te-dieu-tri-benh-than-kinh-dai-thao-duong.pdf`: too_little_extracted_text, possible_scanned_pages
- `data/raw/pdf/Phac-do-Bo-Y-Te-dieu-tri-dai-thao-duong-type-2.pdf`: possible_scanned_pages

## Giới hạn

- Mệnh đề y khoa chỉ được xuất sau khi có quyết định `accepted_for_demo` trong `data/kg/assertions_review.csv`.
- Pipeline không thay thế việc thẩm định của chuyên gia y tế, không tự hợp nhất nguồn mâu thuẫn.
