# AI SPEC — MatchSkill AI (AI Chatbot hỗ trợ chọn đề tài theo năng lực nhóm) · Nhóm [ChickenGuy] · Lớp [E403]
Hướng: [x] C — Làn mở (AI cho quản lý học tập/đội ngũ)
Loại: [x] Tính năng mới

---

## §1. User & Job
- **Job executor + workflow**: Trưởng nhóm / Thành viên nhóm học viên (4-5 người) đang trong giai đoạn chốt đề tài đồ án/hackathon từ kho đề tài `DS_K3_Formatted.xlsx`.
- **Core JTBD**: "Khi cả nhóm cần chọn 1 đề tài trong kho hàng trăm đề tài, nhóm muốn đánh giá chính xác độ tương thích giữa năng lực hiện tại của nhóm và yêu cầu đề tài, để chọn được đề tài vừa sức, đạt điểm cao và hạn chế rủi ro vỡ tiến độ."
- **Problem statement**: Học viên mất nhiều giờ tranh luận chủ quan khi chọn đề tài, chọn nhầm đề tài quá sức hoặc thiếu kỹ năng nòng cốt dẫn tới vỡ tiến độ hoặc bỏ cuộc giữa chừng.
- **Evidence**:
  - Khảo sát thực tế 20+ học viên: 85% học viên thừa nhận từng chọn đề tài dựa trên cảm tính hoặc tên đề tài "kêu" thay vì phân tích skill gap thực tế.
  - Mining data khảo sát: 65% nhóm gặp khủng hoảng ở tuần thứ 2 do thiếu kỹ năng nòng cốt (như Docker, PyTorch, RAG optimization) mà lúc chọn đề tài không lường trước được.

---

## §2. Impact & Quyết định chọn
- **Bảng impact 3 ứng viên**:
  1. **Ứng viên A: Generative Idea Generator** (Gợi ý đề tài tự do từ LLM): Khả thi cao, nhưng đề tài tự do hay xa rời thực tế và không bám sát kho đề tài có sẵn của khóa học.
  2. **Ứng viên B: Automatic Skill Assessment Quiz** (Trắc nghiệm đánh giá trình độ): Tốn nhiều thời gian của học viên, học viên dễ tự đánh giá sai.
  3. **Ứng viên C (CHỌN): Multi-Criteria Skill Matcher & Gap Predictor**: Match profile nhóm với kho 360 đề tài `DS_K3_Formatted.xlsx`, ước lượng độ feasibility, tính toán đường cong học tập (learning curve gap) và giải thích lý do nên/không nên chọn minh bạch.
- **Ứng viên ĐÃ LOẠI**: Ứng viên A & B do không giải quyết tận gốc rễ pain point "chọn đề tài khả thi từ danh sách sẵn có".

---

## §3. Giải pháp tương tự đã nghiên cứu
- **LinkedIn Skill Matching**: Chỉ match từ khóa đơn giản (keyword exact match), không đánh giá được rủi ro vỡ tiến độ và độ khó khi học thêm công nghệ mới.
- **ChatGPT Prompting**: Nhận định chủ quan, hallucinate yêu cầu đề tài, không có bộ khung tiêu chí điểm số cố định (MCDA / Multi-Criteria Decision Analysis).

---

## §4. Thiết kế
- **Lát cắt MỘT CÂU**: 
  > *Một trưởng nhóm nhập/chọn hồ sơ năng lực 4 thành viên -> Hệ thống chatbot MATCH năng lực với danh sách đề tài Excel -> AI đưa ra quyết định xếp hạng Top đề tài phù hợp kèm báo cáo Skill-Gap & Rủi ro khả thi -> Nhóm chốt được 1 đề tài tối ưu trong 5 phút.*
- **Non-goals**:
  - Không thay thế giáo viên/TA duyệt đề tài chính thức.
  - Không tự động phân chia công việc chi tiết từng ngày sau khi chọn đề tài.
  - Không tạo đề tài mới ngoài danh sách `DS_K3_Formatted.xlsx`.
- **Mức prototype**: `Working Prototype` (Web App React/Vite + LLM AI API thật).
- **Automation**: `Conditional` - Hệ thống gợi ý Top đề tài + điểm Matching Score minh bạch, nhóm người dùng giữ quyền chọn quyết định cuối cùng.
- **§4b. Nguyên tắc đã áp dụng (HAX/PAIR)**:
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|
  | Make clear why the system did what it did | Hiển thị rõ bảng phân rã điểm Matching Score (Kỹ năng: 40%, Khả thi: 30%, Rủi ro: 30%) |
  | Support efficient dismissal | Cho phép nhóm loại nhanh các đề tài không thích hoặc thuộc Khối chuyên môn không muốn làm |
  | Show contextually relevant information | Cảnh báo cảnh báo đỏ (Red Flag) nếu nhóm thiếu hoàn toàn Kỹ năng nòng cốt (Prerequisite Skill) |
  | Encourage granular feedback | Cho phép học viên điều chỉnh lại level kỹ năng (1-5) để recalculate kết quả tức thì |

---

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (8 cases)
1. **Lớp ① Nguồn sự thật (Truth/Grounding)**:
   - *Case 1*: AI phán đề tài yêu cầu "KTS Microservices" nhưng file Excel `DS_K3_Formatted.xlsx` không ghi. -> *Xử lý*: Ép Prompt & Schema RAG chỉ trích xuất từ cột `Tech stack gợi ý` và `Yêu cầu đầu ra`.
   - *Case 2*: AI đoán sai thời gian học công nghệ mới. -> *Xử lý*: Dùng benchmark thời gian học cố định cho các skill phổ biến (vd: PyTorch basic: 7 ngày, Docker basic: 3 ngày).
2. **Lớp ② Mơ hồ / Thiếu thông tin**:
   - *Case 3*: Học viên chỉ ghi "biết làm Web" không rõ Frontend hay Backend. -> *Xử lý*: Chatbot hỏi lại hoặc mặc định quy đổi ra mức độ Cơ bản (Level 2/5).
   - *Case 4*: Đề tài không ghi rõ Tech stack. -> *Xử lý*: Chatbot phân tích nội dung từ `Mô Tả Bài Toán` và đánh dấu tag `[SUGGESTED TECH]` kèm cảnh báo.
3. **Lớp ③ Ngoài phạm vi / Thẩm quyền**:
   - *Case 5*: User nhờ Chatbot xin thầy tăng max team lên 6 người. -> *Xử lý*: Từ chối lịch sự, nhắc nhở quy định `Max team / đề tài` ghi trong file Excel.
   - *Case 6*: User nhờ làm hộ bài tập / code hộ đồ án. -> *Xử lý*: Từ chối và định hướng quay lại tư vấn đề tài.
4. **Lớp ④ Đặc thù Domain (AI Thực chiến)**:
   - *Case 7*: Nhóm chọn đề tài RAG/LLM nhưng không ai có nền tảng Python/API. -> *Xử lý*: Cảnh báo rủi ro vỡ tiến độ mức ĐỎ (Critical Alert).
   - *Case 8*: Nhóm chọn đề tài yêu cầu GPU/Hardware đắt tiền nhưng không có kinh phí. -> *Xử lý*: Cảnh báo chi phí & hạ điểm khả thi.

---

## §6. Bốn đường đi của trải nghiệm
- **Happy path**: Nhập team 4 người -> Chọn Khối đề tài quan tâm -> Hệ thống quét Excel -> Trả về Top 3 Đề tài có Matching Score cao nhất (>85%), hiển thị Radar chart so sánh skill gap và kết luận chọn.
- **Low-confidence (②)**: Thông tin kỹ năng thành viên còn mờ nhạt -> Chatbot bật 3 câu hỏi trắc nghiệm nhanh để xác định level.
- **Failure/Không căn cứ (①)**: Đề tài nằm ngoài danh sách Excel -> Chatbot báo không tìm thấy đề tài trong dữ liệu chính thức và đề xuất đề tài tương đương có trong danh sách.
- **Correction (User sửa)**: User bấm "Sửa năng lực thành viên" -> Nhóm tự update level Python từ 2 lên 4 -> Hệ thống re-rank kết quả tức thì.
- **Ngoài phạm vi (③)**: User hỏi ngoài phạm vi -> Trả lời theo kịch bản từ chối chuẩn bị sẵn.
- **Case đặc thù domain (④)**: Phát hiện thiếu skill nòng cốt -> Xuất lộ trình bù đắp nhanh (Learning Roadmap trong X ngày).

---

## §7. Kiểm thử
- **Quality bar**: Đạt khi ≥75% câu thử đạt, và không được trả lời sai deadline lần nào.
- **Golden set**: 20 bộ profile nhóm kiểm thử đại diện cho các tổ hợp skill (Dev nặng, Data nặng, Non-tech nặng, Mixed). Có 15 câu bắt nguồn từ quan sát thực tế.
- **Kết quả các lượt chạy**: Đạt 10/20 câu (Lượt chạy đầu tại CP3).

---

## §8. Phân công & Kế hoạch
- **Đội ngũ (ChickenGuy)**:
  - `Trần Xuân Bách - 2A202601093 (Leader)`: Lead Spec, thiết kế MCDA Framework, Prompt Engineering.
  - `Trịnh Quốc Trọng - 2A202601779`: Build UI Web app (React/Vite), tích hợp Excel Parser & LLM API.
  - `Đinh Hoài Nam - 2A202601889`: Chuẩn hóa 360 đề tài từ file `DS_K3_Formatted.xlsx`, xây dựng 20 golden test cases.
  - `Phạm Thị Thùy Linh - 2A202601181`: Khảo sát người dùng, đo lường vòng validation CP5.
- **Github Repo**: https://github.com/XuanBach410/K3-hackathon-ChickenGuy-E403
