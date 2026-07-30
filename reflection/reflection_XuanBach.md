# Reflection cá nhân — Trần Xuân Bách

**Học viên:** Trần Xuân Bách  
**Mã HV:** 2A202601093  
**Vai trò:** Leader  
**Dự án:** AI Evaluator — Trợ lý AI Đánh giá & Định hướng Đề tài cho Chương Trình AI Thực Chiến

---

## 1. Vai trò & Đóng góp thực tế trong Dự án
Với vai trò **Leader**, tôi chịu trách nhiệm xuyên suốt từ tư tưởng sản phẩm, thiết kế kiến trúc AI cho đến quá trình nghiệm thu chất lượng:
- **Lead AI Spec (`spec.md`):** Chủ trì nghiên cứu JTBD, xác định lát cắt trải nghiệm cốt lõi (Core User Journey), xây dựng ma trận lỗi (4 lớp chỗ khó) và thiết kế ranh giới trải nghiệm (Happy Path, Edge Cases, Out-of-scope Refusal).
- **Thiết kế Thuật toán & MCDA Framework:** Trực tiếp thiết kế thuật toán đánh giá đa tiêu chí MCDA (Multi-Criteria Decision Analysis) kết hợp Ma trận Rủi ro kỹ năng (Risk Matrix), giúp quy đổi khoảng trống năng lực nhóm thành chi phí tự học định lượng (số giờ/tuần).
- **Prompt Engineering & System Architecture:** Xây dựng System Prompt chuẩn hóa cho Gemini API (`gemini-1.5-flash`), thiết lập cơ chế **Structured JSON Output**, kiểm soát ranh giới dữ liệu (Strict Boundary Rules) để triệt tiêu tình trạng AI hallucinate/tự suy đoán ngoài mô tả chính thức.
- **Quản lý & Chạy Golden Set Evaluation:** Xây dựng và duy trì bộ kiểm thử 35 test cases (`eval/test_questions.json`) phân rõ 20 câu tiêu chuẩn và 15 câu thực tế quan sát, đạt chỉ số **100% Pass Rate**.

---

## 2. Bài học lớn nhất rút ra (Lessons Learned)

### 🎯 Về Tư duy Sản phẩm AI (AI Product Mindset)
- **Cơ chế Augment thay vì Automate mù quáng:** AI không nên đóng vai trò "thay thế hoàn toàn" quyết định chọn đề tài của học viên, mà là **công cụ minh bạch hóa thông tin (Augment)** — đưa ra bằng chứng số liệu về khoảng trống kỹ năng, dự báo số giờ tự học để học viên tự đưa ra quyết định sáng suốt.
- **Ranh giới dữ liệu là sự sống còn (Strict Scope Control):** AI Agent hữu ích nhất khi biết nói *"Tôi không có đủ căn cứ để trả lời"* đối với những thông tin không nằm trong mô tả chính thức, thay vì cố gắng suy đoán vội vàng.

### 🧪 Về Đánh giá & Kiểm thử (Eval & Quality Bar)
- **Đo lường bằng dữ liệu thay vì cảm tính:** Bài học lớn nhất của tôi là tầm quan trọng của `Golden Set`. Việc chạy lại 35 test cases tự động bằng script benchmark giúp phát hiện ngay lập tức khi một chỉnh sửa nhỏ trong System Prompt làm vỡ cấu trúc JSON hoặc làm AI trả lời sai quy tắc từ chối.

---

## 3. Thách thức lớn nhất & Cách vượt qua
- **Thách thức:** Cân bằng giữa tính linh hoạt của LLM và tính chính xác tuyệt đối của mô hình đánh giá kỹ thuật. Đôi khi LLM trả về định dạng text không chuẩn hoặc bỏ sót trường dữ liệu lộ trình.
- **Giải pháp:** Tôi đã kết hợp kiến trúc **Hybrid**: Sử dụng MCDA Rule-Engine làm lớp tính toán cố định và Fallback Safety Net, đồng thời dùng LLM làm lớp tổng hợp ngôn ngữ tự nhiên và lập lộ trình cá nhân hóa. Nếu LLM gặp sự cố, hệ thống vẫn tự động trả về kết quả đánh giá định lượng chính xác 100%.

---

## 4. Đúc kết & Hướng phát triển nếu có thêm thời gian
- Nếu có thêm 1 tuần, tôi sẽ mở rộng cơ chế **Agentic Self-Correction** (cho phép AI tự rà soát câu trả lời của chính nó trước khi xuất ra UI) và tích hợp thêm tính năng gợi ý tài liệu học tập tự động cho các kỹ năng còn thiếu (`toLearn`).
- Hackathon 1.5 ngày này đã giúp tôi nâng cao toàn bộ tư duy từ một người viết code thuần túy thành một **AI Product Creator** có tư duy sản phẩm, biết cách kiểm soát rủi ro và lấy người dùng làm trung tâm.
