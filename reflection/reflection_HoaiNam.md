# Báo Cáo Thu Hoạch Cá Nhân (Reflection) - Hackathon K3

**Họ và tên:** Đinh Hoài Nam  
**MSSV:** 2A202601889  
**Nhóm:** ChickenGuy (Phòng E403)

## 1. Vai trò và nhiệm vụ trong dự án
Trong dự án MatchSkill AI, tôi đảm nhận vai trò Kỹ sư phần mềm toàn năng (Full-stack Developer), chịu trách nhiệm chính trong việc xây dựng nền tảng kỹ thuật cho cả hai phân hệ Backend và Frontend:
- **Backend (Django):** Thiết kế cấu trúc cơ sở dữ liệu, xây dựng các API cốt lõi và tích hợp hệ thống đánh giá đa tiêu chí (MCDA Engine). Đồng thời, tôi phụ trách luồng kết nối an toàn với các API của hệ thống LLM (như Gemini) để phân tích khoảng trống kỹ năng và sinh lộ trình học tập.
- **Frontend (React/Vite):** Triển khai giao diện người dùng (UI) tương tác trực quan, kết nối các API từ Backend để xử lý dữ liệu thời gian thực. Tập trung vào việc làm nổi bật trải nghiệm người dùng (UX) thông qua việc vẽ các biểu đồ hiển thị kỹ năng (Risk Matrix, Score Breakdown).

## 2. Ứng dụng AI trong quá trình làm việc
Với khối lượng công việc lập trình cực kỳ lớn trong thời gian hackathon rất ngắn, việc ứng dụng AI (Cursor / Claude) là yếu tố sống còn giúp tôi hoàn thành tiến độ:
- **Sinh mã nguồn (Scaffolding) siêu tốc:** Tôi sử dụng AI để tự động tạo bộ khung (boilerplate) cho các React Components phức tạp cũng như định tuyến (routing) API chuẩn RESTful bên Django. 
- **Chuyển đổi và xử lý dữ liệu:** Khi gặp khó khăn trong việc đồng bộ định dạng dữ liệu giữa Python (Backend) và JavaScript (Frontend), tôi đã dùng AI để sinh các đoạn mã tự động bóc tách (parse) các khối JSON phức tạp do LLM trả về, tiết kiệm được hàng giờ đồng hồ rà soát lỗi thủ công.

## 3. Bài học rút ra từ các trường hợp lỗi (Case Fail)
Trong quá trình tích hợp Backend và Frontend với bộ não LLM, tôi đã đối mặt với một sự cố nghiêm trọng (edge case): *"Dữ liệu JSON định dạng từ LLM trả về thỉnh thoảng bị lỗi cấu trúc (thiếu dấu ngoặc, cụt chuỗi) do vượt quá giới hạn độ dài ký tự (max_tokens)"*.

- **Kết quả mong đợi:** Frontend nhận chuỗi JSON chuẩn để vẽ đồ thị rủi ro (Risk Matrix).
- **Hành vi thực tế:** Vì Backend trả thẳng nguyên văn chuỗi lỗi của LLM xuống mà không qua bộ lọc, ứng dụng React ở Frontend bị lỗi `JSON.parse()` và sập (crash) toàn bộ giao diện trắng xóa ngay trước giờ chạy thử nghiệm.

**Bài học kinh nghiệm:** Không bao giờ được tin tưởng tuyệt đối vào định dạng dữ liệu đầu ra của LLM dù prompt có chặt chẽ đến đâu. Mọi kết nối giao tiếp với AI đều phải có cơ chế **Phòng vệ và Xử lý lỗi (Fallback & Error Handling)** vững chắc ngay tại tầng Backend. 
Hệ thống bắt buộc phải kiểm tra tính hợp lệ của chuỗi JSON trước, nếu lỗi thì tự động yêu cầu AI xử lý lại (retry) hoặc trả về một giá trị mặc định an toàn (safe default) để bảo vệ trải nghiệm người dùng, tuyệt đối không để lỗi từ LLM đánh sập Frontend.
