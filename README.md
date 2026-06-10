# Day 10: Data Pipeline & Data Observability

Repository này chứa hệ thống Data Pipeline và Data Observability (Quan sát Dữ liệu) hoàn chỉnh từ đầu đến cuối. Hệ thống được thiết kế để thu thập các bài báo nghiên cứu, xử lý dữ liệu, xây dựng vector index cho hệ thống Retrieval-Augmented Generation (RAG), đánh giá hiệu suất và giám sát chất lượng dữ liệu.

## Các Tính Năng Chính Đã Triển Khai

### 1. Thu Thập Dữ Liệu & Tính Kháng Lỗi (src/ingestion/crossref.py)
- Tích hợp với Crossref API để lấy siêu dữ liệu (metadata) của các bài báo học thuật.
- Triển khai cơ chế gọi API với tính năng tự động thử lại (exponential backoff) để xử lý các lỗi giới hạn lượt gọi (rate limits - 429) và lỗi máy chủ (503).
- Định dạng cấu trúc chuỗi JSON trả về thành các dataclass PaperRecord.

### 2. Làm Sạch & Chuẩn Hóa Dữ Liệu (src/ingestion/cleaning.py)
- Làm sạch và chuẩn hóa các trường văn bản (loại bỏ các thẻ HTML, thu gọn khoảng trắng).
- Chuyển đổi chuỗi thời gian xuất bản có chứa múi giờ (timezone-aware) và tính toán độ mới của dữ liệu (cột age_days).
- Tạo các cột phụ trợ (authors_joined, text_for_embedding) để tối ưu hóa dữ liệu cho hệ thống RAG phía sau.
- Loại bỏ các dòng trùng lặp và các dòng dữ liệu kém chất lượng (ví dụ: thiếu tiêu đề hoặc tóm tắt).

### 3. Lưu Trữ Vector (src/retrieval/embeddings.py, src/retrieval/index.py)
- Sử dụng mô hình sentence-transformers/all-MiniLM-L6-v2 để tạo embedding cho văn bản.
- Lưu trữ các vector cục bộ thông qua ChromaDB.
- Điều chỉnh wrapper embedding để tương thích với các bước xác thực dữ liệu của thư viện đánh giá Ragas.

### 4. Tự Động Sinh Dữ Liệu Đánh Giá (src/evaluation/testset.py)
- Tự động tạo bộ dữ liệu đánh giá bao gồm 4 loại câu hỏi cho mỗi bài báo:
  - Tóm tắt (Summary): "Bài báo này nói về cái gì?"
  - Tác giả (Authors): "Tác giả là những ai?"
  - Thời gian (Date): "Bài báo được xuất bản khi nào?"
  - Phân loại (Categories): "Bài báo thuộc danh mục nào?"
- Giải quyết triệt để lỗi đánh giá giá trị logic của pandas liên quan đến các thành phần có cấu trúc mảng (array-like elements).

### 5. Chỉ Số Đánh Giá RAG (src/evaluation/metrics.py)
- Điểm Token F1: Đo lường độ trùng lặp token giữa đáp án thực tế (ground truth) và câu trả lời dự đoán.
- Chấm điểm bằng LLM (LLM-as-a-Judge): Đánh giá tính chính xác và cho điểm từ 1 đến 5 kèm theo giải thích.
- Tỷ lệ truy xuất thành công (Retrieval Hit Rate): Đánh giá xem mã DOI của bài báo chính xác có nằm trong top kết quả trả về hay không.
- Tích hợp Ragas: Tích hợp mạnh mẽ với Ragas để tính toán context_precision, context_recall và faithfulness. Đã xử lý thành công giới hạn của nhà cung cấp LLM (DeepSeek chỉ hỗ trợ n=1) bằng cách loại bỏ metric answer_relevancy.

### 6. Quan Sát Dữ Liệu & Kiểm Tra Chất Lượng (src/observability/quality.py, src/observability/reporting.py)
- Triển khai một bộ kiểm tra chất lượng dữ liệu thiết yếu:
  - Số lượng dòng dữ liệu tối thiểu.
  - paper_id không được Null và phải là duy nhất.
  - title không được rỗng.
  - summary phải đáp ứng độ dài ký tự tối thiểu.
  - freshness: Đảm bảo dữ liệu không cũ hơn 180 ngày.
- Xuất các báo cáo độ mới (freshness) dạng JSON và báo cáo tổng hợp dạng Markdown nhằm so sánh hiệu suất của hệ thống.

### 7. Mô Phỏng Dữ Liệu Lỗi (src/ingestion/corruption.py, src/pipelines/corruption_flow.py)
- Xây dựng luồng mô phỏng để cố ý tạo ra các lỗi dữ liệu thực tế:
  - Xóa bớt dữ liệu.
  - Xóa tóm tắt (abstract).
  - Thêm chuỗi ký tự rác vào văn bản.
  - Cắt bớt tiêu đề.
  - Đẩy lùi ngày xuất bản để kích hoạt cảnh báo dữ liệu cũ.
  - Nhân bản một số dòng dữ liệu.
- Xây dựng luồng đánh giá so sánh (corruption_flow.py) để đo lường các chỉ số của RAG pipeline và các công cụ Kiểm Tra Chất Lượng ở ba trạng thái: Baseline (Gốc), Corrupted (Lỗi), và Repaired (Đã sửa).

## Hướng Dẫn Chạy

1. Chạy Luồng Dữ Liệu Gốc (Phase 1):
```powershell
$env:PYTHONPATH="src"
python script\run_phase1.py
```
(Tùy chọn: thiết lập $env:RUN_RAGAS="1" trước khi chạy để tính toán thêm các chỉ số từ Ragas)

2. Chạy Luồng Dữ Liệu Lỗi & Khôi Phục (Phase 2):
```powershell
$env:PYTHONPATH="src"
python script\run_corruption_flow.py
```

## Kết Quả & Đầu Ra
Tất cả các tài nguyên sinh ra được lưu vào thư mục data/:
- data/clean/: Các file dữ liệu đã được làm sạch (CSV & JSON).
- data/eval/: Bộ dữ liệu câu hỏi đánh giá.
- data/quality/: Các file JSON chứa kết quả kiểm tra chất lượng dữ liệu và độ mới.
- data/reports/: Báo cáo định dạng Markdown (phase1_report.md và corruption_report.md).
