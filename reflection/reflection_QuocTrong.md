# Báo Cáo Thu Hoạch Cá Nhân (Reflection) - Hackathon K3

**Họ và tên:** Trịnh Quốc Trọng
**MSSV:** 2A202601779
**Nhóm:** ChickenGuy (Phòng E403)

## 1. Vai trò và nhiệm vụ trong dự án
Trong khuôn khổ dự án MatchSkill AI, tôi đảm nhận các trọng trách liên quan đến triển khai kỹ thuật và kiểm thử chất lượng (QA). Các công việc cụ thể bao gồm:
- **Xây dựng tập dữ liệu giả lập (Mock Data):** Khởi tạo các hồ sơ học viên (profiles) đa dạng và kho đề tài giả định để cung cấp dữ liệu đầu vào cho quá trình kiểm thử trong các giai đoạn phát triển ban đầu.
- **Gỡ lỗi và tinh chỉnh mã nguồn (Debugging & Refactoring):** Rà soát mã nguồn dự án, phát hiện và khắc phục các lỗi (bugs) nhằm đảm bảo luồng nghiệp vụ (user flow) vận hành ổn định và thông suốt.
- **Thực thi và đánh giá kịch bản kiểm thử (Test Execution):** Trực tiếp chạy các tập dữ liệu kiểm thử (Golden set) trên hệ thống, đo lường tỷ lệ chính xác và từ đó đưa ra các đề xuất tinh chỉnh để hệ thống đạt tiêu chuẩn chất lượng (quality bar) đã cam kết.

## 2. Ứng dụng AI trong quá trình làm việc
Việc ứng dụng các mô hình ngôn ngữ lớn (LLM) đã tối ưu hóa đáng kể hiệu suất làm việc của tôi:
- Thay vì tạo dữ liệu thủ công, tôi sử dụng AI (như Gemini/Claude) để tự động sinh ra hàng loạt hồ sơ nhóm với các phân bố kỹ năng sát với thực tế (nhóm thiên về Development, Data, hoặc thiếu hụt kỹ năng). 
- Trong quá trình gỡ lỗi mã nguồn, AI đóng vai trò như một trợ lý đắc lực trong việc phân tích các log lỗi (error logs) phức tạp, giúp khoanh vùng nguyên nhân và đề xuất hướng giải quyết nhanh chóng, giảm thiểu đáng kể thời gian tra cứu tài liệu truyền thống.

## 3. Bài học rút ra từ các trường hợp lỗi (Case Fail)
Trong quá trình đánh giá Golden set, nhóm chúng tôi đã gặp phải một trường hợp thất bại (failure case) đáng chú ý. Đối với kịch bản đầu vào: *"Nhóm người dùng có kỹ năng hiện tại bằng 0, thời gian triển khai rất ngắn nhưng lại chọn một đề tài có độ khó cực cao"*. 
- **Kết quả mong đợi:** Hệ thống phải đưa ra cảnh báo rủi ro ở mức độ cao nhất và kiên quyết khuyên nhóm đổi đề tài.
- **Hành vi thực tế của AI:** Mô hình LLM đã rơi vào trạng thái "ảo giác" (hallucination) và cố gắng chiều lòng người dùng bằng cách sinh ra một lộ trình học tập bất khả thi (yêu cầu hoàn thành khối lượng kiến thức khổng lồ chỉ trong 1 tuần).

**Bài học kinh nghiệm:** Không thể phó mặc hoàn toàn khả năng ra quyết định cho LLM, đặc biệt là trong các tính năng mang tính chất định hướng quan trọng. Chúng ta bắt buộc phải thiết lập các ràng buộc (constraints) nghiêm ngặt trong hệ thống prompt và quy tắc nghiệp vụ (ví dụ: *"Nếu thời gian học bù kỹ năng vượt quá ngưỡng khả thi 3 tuần, hệ thống bắt buộc phải từ chối và đề xuất phương án khác"*). Sự cố này cũng chứng minh tầm quan trọng của việc xây dựng các tập kiểm thử bao phủ được các trường hợp biên (edge cases).
