# Báo Cáo Thu Hoạch Cá Nhân (Reflection) - Hackathon K3

**Họ và tên:** Đinh Hoài Nam  
**MSSV:** 2A202601889  
**Nhóm:** ChickenGuy (Phòng E403)

## 1. Vai trò và nhiệm vụ trong dự án
Trong dự án MatchSkill AI (Hackathon K3), tôi đảm nhận vai trò Full-stack Developer và Kiến trúc sư hệ thống. Dựa trên lịch sử đóng góp, các nhiệm vụ chính của tôi bao gồm:
- **Backend (Django):** 
  - Khởi tạo kiến trúc `backend_project` và ứng dụng `evaluator`.
  - Phát triển hệ thống đánh giá đa tiêu chí (MCDA Engine) và cấu hình logic trong `criteria.md`, `skill_taxonomy.json`.
  - Tích hợp API trực tiếp với các LLM Provider (Gemini 3.6 Flash, GPT-4o) để đánh giá năng lực và phân tích kỹ năng người dùng.
  - Cấu hình định tuyến và xử lý luồng phục vụ (serve) giao diện React frontend trực tiếp từ Django backend thông qua `BASE_DIR`.
- **Frontend (React.js/Vite):** 
  - Phát triển giao diện người dùng theo phong cách Swiss UI hiện đại.
  - Xây dựng các components cốt lõi: `DeepEvalQuiz`, `RoadmapView`, `DecisionWorkspace`, và `ApiKeyModal`.
- **Xử lý dữ liệu:** 
  - Viết script `convert_excel.py` để trích xuất dữ liệu từ `DS_K3_Formatted.xlsx` ra định dạng JSON (`topics_data.json`).
  - Kết nối dữ liệu mẫu (`mock_profiles.json`) vào hệ thống để hỗ trợ demo mượt mà.

## 2. Ứng dụng AI trong quá trình làm việc
Xuyên suốt thời gian ngắn ngủi của Hackathon, tôi đã tận dụng tối đa AI (Cursor/Claude) để tăng tốc độ phát triển:
- **Scaffolding toàn bộ kiến trúc Full-stack:** AI giúp tôi tạo khung sườn cho cả Django backend và React/Vite frontend nhanh chóng, tạo ra hàng ngàn dòng code nền tảng (boilerplate) chỉ trong thời gian ngắn.
- **Tích hợp LLM logic:** Hỗ trợ sinh các đoạn mã kết nối với API của Gemini và GPT-4o, đặc biệt là phần parser để đọc hiểu dữ liệu phân tích kỹ năng từ AI.
- **Xử lý dữ liệu thô (Data Wrangling):** Sử dụng AI để sinh mã Python chuyển đổi định dạng dữ liệu từ bảng tính Excel sang JSON chuẩn hóa, sẵn sàng cho việc hiển thị ở frontend.

## 3. Bài học rút ra từ các trường hợp lỗi (Case Fail)
Trong quá trình triển khai, tôi đã gặp một số lỗi và rút ra những bài học thực chiến quan trọng:
- **Lỗi Parse JSON từ LLM:** Khi hệ thống yêu cầu API trả về định dạng JSON, đôi lúc LLM trả về chuỗi văn bản thuần hoặc JSON thiếu ngoặc, thừa ký tự markdown do token limit. Điều này dễ làm crash Frontend. *Bài học:* Luôn phải xây dựng cơ chế Fallback vững chắc và bộ làm sạch dữ liệu (Regex/JSON parser linh hoạt) ở tầng Backend (như tôi đã triển khai trong `llm_provider.py`) để bảo vệ dữ liệu trước khi gửi xuống Frontend.
- **Vấn đề Serve Static Files (React) bằng Django:** Ban đầu, khi đưa bản build của React vào Django, cấu hình `BASE_DIR` sai khiến ứng dụng hiển thị màn hình trắng và gặp lỗi 404 cho các file JS/CSS. Tôi đã phải debug để map chính xác `urls.py` và `views.py` cho `index.html`. *Bài học:* Tích hợp Full-stack đòi hỏi phải quản lý luồng tĩnh (static pipeline) và định tuyến (routing) rất cẩn thận, không thể phó mặc hoàn toàn cho công cụ tự động.
