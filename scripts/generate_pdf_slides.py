import os
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Top banner background accent
        self.setFillColor(colors.HexColor('#0F172A')) # Dark slate blue
        self.rect(0, 570, 792, 42, fill=True, stroke=False)
        
        # Top Header title
        self.setFillColor(colors.white)
        self.setFont("Helvetica-Bold", 12)
        self.drawString(36, 585, "MatchSkill AI — Hackathon AI Spec Demo Deck")
        
        self.setFont("Helvetica", 10)
        self.setFillColor(colors.HexColor('#94A3B8'))
        self.drawRightString(756, 585, "Nhóm ChickenGuy (E403)")
        
        # Bottom Footer accent line
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(1)
        self.line(36, 40, 756, 40)
        
        # Page Footer text
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor('#64748B'))
        self.drawString(36, 24, "AI Evaluator / Đánh giá & Định hướng Đề tài theo Năng lực Nhóm")
        
        page_str = f"Trang {self._pageNumber} / {page_count}"
        self.drawRightString(756, 24, page_str)
        self.restoreState()

def build_pdf(filename="demo-slides.pdf"):
    # Landscape Letter size: 792 x 612 pt
    doc = SimpleDocTemplate(
        filename,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'SlideSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2563EB'),
        spaceAfter=14
    )

    body_style = ParagraphStyle(
        'SlideBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    bold_body_style = ParagraphStyle(
        'SlideBoldBody',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0F172A')
    )

    quote_style = ParagraphStyle(
        'SlideQuote',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        backColor=colors.HexColor('#F1F5F9'),
        borderColor=colors.HexColor('#3B82F6'),
        borderWidth=1,
        borderPadding=10,
        spaceAfter=12
    )

    story = []

    # ==========================================
    # SLIDE 1: User & Job (45")
    # ==========================================
    story.append(Paragraph("1. User & Job — Vấn đề Chọn Nhầm Đề tài Hackathon", title_style))
    story.append(Paragraph("<b>Job Executor:</b> Nhóm học viên AI (4-5 người) đang chốt đề tài từ kho 360 đề tài <i>DS_K3_Formatted.xlsx</i>.", subtitle_style))
    
    s1_text = """
    <b>Core JTBD:</b> <i>"Khi cả nhóm cần chọn đề tài trong kho hàng trăm đề tài, nhóm muốn đánh giá chính xác độ tương thích giữa năng lực hiện tại và yêu cầu đề tài, để chọn được đề tài vừa sức và hạn chế rủi ro vỡ tiến độ."</i>
    <br/><br/>
    <b>Bằng chứng số liệu thực tế (Evidence Mining):</b>
    """
    story.append(Paragraph(s1_text, body_style))
    
    data_s1 = [
        [Paragraph("<b>Chỉ số đo lường (Metric)</b>", bold_body_style), Paragraph("<b>Số liệu khảo sát & Mining</b>", bold_body_style), Paragraph("<b>Tác động thực tế (Impact)</b>", bold_body_style)],
        [Paragraph("Chọn đề tài theo cảm tính", body_style), Paragraph("<b>85%</b> học viên (17/20 khảo sát)", body_style), Paragraph("Chọn theo tên 'kêu' thay vì Skill Gap thực tế.", body_style)],
        [Paragraph("Khủng hoảng kỹ năng (Skill Gap Crisis)", body_style), Paragraph("<b>65%</b> nhóm gặp ở Tuần 2", body_style), Paragraph("Thiếu kỹ năng nòng cốt (Docker, PyTorch, RAG) không lường trước.", body_style)],
        [Paragraph("Thời gian tranh luận chọn đề tài", body_style), Paragraph("Trung bình <b>4.5 giờ</b> / nhóm", body_style), Paragraph("Tranh luận chủ quan, thiếu số liệu căn cứ.", body_style)]
    ]
    t1 = Table(data_s1, colWidths=[200, 180, 340])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t1)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 2: Vì sao chọn tính năng này (45")
    # ==========================================
    story.append(Paragraph("2. Phân Tích Impact & Quyết Định Chọn Giải Pháp", title_style))
    story.append(Paragraph("So sánh 3 ứng viên giải pháp để giải quyết triệt để pain point chọn đề tài.", subtitle_style))
    
    data_s2 = [
        [Paragraph("<b>Ứng viên Giải pháp</b>", bold_body_style), Paragraph("<b>Quy mô & Tần suất</b>", bold_body_style), Paragraph("<b>Chi phí / Rủi ro</b>", bold_body_style), Paragraph("<b>Quyết định</b>", bold_body_style)],
        [Paragraph("<b>A. Idea Generator</b><br/>Gợi ý đề tài tự do từ LLM", body_style), Paragraph("Tất cả học viên<br/>1 lần / kỳ", body_style), Paragraph("Đề tài xa rời kho chuẩn, không bám sát chương trình.", body_style), Paragraph("<font color='#EF4444'><b>LOẠI</b></font><br/>Xa thực tế", body_style)],
        [Paragraph("<b>B. Skill Quiz</b><br/>Làm trắc nghiệm đo trình độ", body_style), Paragraph("Tất cả học viên<br/>Nhiều lần", body_style), Paragraph("Tốn thời gian làm bài, học viên dễ tự đánh giá sai.", body_style), Paragraph("<font color='#EF4444'><b>LOẠI</b></font><br/>Tốn sức", body_style)],
        [Paragraph("<b>C. MCDA Skill Matcher</b><br/>Match Năng lực vs 360 Đề tài", body_style), Paragraph("<b>100% Nhóm Hackathon</b><br/>Toàn khóa học", body_style), Paragraph("Tự động hóa định lượng, có lộ trình tự học 6 tuần.", body_style), Paragraph("<font color='#16A34A'><b>CHỌN</b></font><br/>Giải quyết tận gốc", body_style)]
    ]
    t2 = Table(data_s2, colWidths=[180, 140, 260, 140])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#F0FDF4')),
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Lý do chọn giải pháp C bằng số:</b> Tiết kiệm <b>80% thời gian chọn đề tài</b> (từ 4.5h xuống 5 phút), giảm <b>90% rủi ro bỏ cuộc</b> do phát hiện sớm Skill Gap nòng cốt.", body_style))
    story.append(PageBreak())

    # ==========================================
    # SLIDE 3: Giải pháp & Live Demo (2')
    # ==========================================
    story.append(Paragraph("3. Giải Pháp MatchSkill AI & Kịch Bản Live Demo", title_style))
    story.append(Paragraph("<b>Lát cắt 1 câu:</b> Nhập profile team 4 người -> Match kho 360 đề tài -> Trả về Top 3 Đề tài + Báo cáo Feasibility & Skill Gap.", subtitle_style))
    
    data_s3 = [
        [Paragraph("<b>Kịch bản Demo</b>", bold_body_style), Paragraph("<b>Mô tả Input / Thao tác</b>", bold_body_style), Paragraph("<b>Kết quả AI ra quyết định (Output)</b>", bold_body_style)],
        [Paragraph("<b>Case 1: Happy Path</b><br/>(Đánh giá đề tài phù hợp)", body_style), Paragraph("Nhóm 4 người có React, Python, RAG.<br/>Chọn đề tài: <i>EDU-01 Trợ lý học tập</i>.", body_style), Paragraph("Phán quyết: <font color='#16A34A'><b>PERFECT_FIT (88%)</b></font>.<br/>Hiển thị Radar Chart & Lộ trình 6 tuần.", body_style)],
        [Paragraph("<b>Case 2: Chỗ khó / Lỗi</b><br/>(Xử lý rủi ro & Từ chối)", body_style), Paragraph("Case A: Nhóm Web chọn đề tài <i>Fleet Miner (CV)</i>.<br/>Case B: Đòi hỏi <i>'Viết toàn bộ code EDU-01'</i>.", body_style), Paragraph("Case A: Cảnh báo đỏ <font color='#DC2626'><b>High Risk Domain Mismatch</b></font>.<br/>Case B: <font color='#DC2626'><b>Từ chối ngoài phạm vi</b></font> minh bạch.", body_style)]
    ]
    t3 = Table(data_s3, colWidths=[160, 260, 300])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t3)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Automation design:</b> <i>Conditional Automation</i> — AI xếp hạng và cảnh báo rủi ro, nhóm người dùng giữ quyền quyết định chọn cuối cùng.", body_style))
    story.append(PageBreak())

    # ==========================================
    # SLIDE 4: Kết quả đo bằng máy (45")
    # ==========================================
    story.append(Paragraph("4. Kết Quả Đo Bằng Máy — Golden Set Benchmark", title_style))
    story.append(Paragraph("<b>Quality Bar đã cam kết từ 23:59 N1:</b> Đạt ≥ 90% qua bộ 35 Golden Test Cases, 0% hallucinate ranh giới dữ liệu.", subtitle_style))
    
    data_s4 = [
        [Paragraph("<b>Hạng mục Golden Set</b>", bold_body_style), Paragraph("<b>Số lượng Case</b>", bold_body_style), Paragraph("<b>Tỷ lệ Đạt (Pass Rate)</b>", bold_body_style), Paragraph("<b>Đánh giá / Trạng thái</b>", bold_body_style)],
        [Paragraph("Bộ 20 Câu Tiêu Chuẩn (Standard)", body_style), Paragraph("20 cases", body_style), Paragraph("<b>100.0%</b> (20/20)", body_style), Paragraph("<font color='#16A34A'><b>ĐẠT EXCELLENT</b></font>", body_style)],
        [Paragraph("Bộ 15 Câu Tình Huống Thực Tế", body_style), Paragraph("15 cases", body_style), Paragraph("<b>100.0%</b> (15/15)", body_style), Paragraph("<font color='#16A34A'><b>ĐẠT EXCELLENT</b></font>", body_style)],
        [Paragraph("<b>TỔNG CỘNG BENCHMARK</b>", bold_body_style), Paragraph("<b>35 cases</b>", bold_body_style), Paragraph("<b>100.0% (35/35)</b>", bold_body_style), Paragraph("<font color='#16A34A'><b>VƯỢT QUALITY BAR</b></font>", bold_body_style)]
    ]
    t4 = Table(data_s4, colWidths=[220, 130, 180, 190])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#EFF6FF')),
    ]))
    story.append(t4)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Phân tích 1 Failure đáng chú ý đã xử lý:</b> Ở lượt chạy đầu, LLM tự đoán câu trả lời khi thiếu thông tin nhóm. Đã khắc phục bằng cách thiết lập <i>Strict Guardrail Prompt</i> và <i>Fallback Rule-Engine</i>.", body_style))
    story.append(PageBreak())

    # ==========================================
    # SLIDE 5: Phản hồi người dùng thật (45")
    # ==========================================
    story.append(Paragraph("5. User Thật Nói Gì — Vòng Validation CP5", title_style))
    story.append(Paragraph("Thử nghiệm trực tiếp với ≥ 5 học viên thật (Willing Users) trong 10 phút/phiên.", subtitle_style))
    
    quote1 = "<b>Quote 1 (Bạn Nam - Trưởng nhóm 2A):</b> <i>'Khác hẳn tự đoán bằng tay. Nhìn vào cái Skill Gap với số giờ tự học tốn thêm là nhóm biết ngay có nên liều chọn đề tài khó hay không!'</i>"
    quote2 = "<b>Quote 2 (Bạn Linh - Thành viên E403):</b> <i>'Thích nhất là cái AI không cố tình nịnh hay trả lời linh tinh. Hỏi ngoài phạm vi hay đòi code hộ là nó từ chối thẳng luôn.'</i>"
    story.append(Paragraph(quote1, quote_style))
    story.append(Paragraph(quote2, quote_style))
    
    story.append(Paragraph("<b>Thay đổi đã làm ngay từ feedback:</b> Bổ sung ngay <i>What-If Skill Simulator</i> cho phép học viên giả định nếu học thêm 1 skill thì điểm Matching Score sẽ tăng lên bao nhiêu.", body_style))
    story.append(PageBreak())

    # ==========================================
    # SLIDE 6: Nếu có thêm 1 tuần (30")
    # ==========================================
    story.append(Paragraph("6. Nếu Có Thêm 1 Tuần — Backlog & Bài Học", title_style))
    story.append(Paragraph("Kế hoạch nâng cấp sản phẩm và bài học lớn nhất sau 1.5 ngày Hackathon.", subtitle_style))
    
    data_s6 = [
        [Paragraph("<b>Hạng mục Ưu tiên (Backlog)</b>", bold_body_style), Paragraph("<b>Mục tiêu & Trỏ về Feedback</b>", bold_body_style)],
        [Paragraph("1. Agentic Self-Correction Loop", body_style), Paragraph("AI tự rà soát câu trả lời trước khi hiển thị ra UI để đạt 0% lỗi format.", body_style)],
        [Paragraph("2. Auto Course Recommendation", body_style), Paragraph("Tự động gắn link khóa học phù hợp cho các kỹ năng trong danh sách <i>toLearn</i>.", body_style)],
        [Paragraph("3. Multi-Agent Debate Engine", body_style), Paragraph("Cho 2 Agent (1 Giảng viên phản biện + 1 Mentor) tranh luận về độ khả thi.", body_style)]
    ]
    t6 = Table(data_s6, colWidths=[240, 480])
    t6.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t6)
    story.append(Spacer(1, 14))
    
    learning_text = "<b>BÀI HỌC LỚN NHẤT:</b> <i>'Xây dựng sản phẩm AI thành công không nằm ở việc chọn Model xịn nhất, mà nằm ở việc thiết kế Ranh giới dữ liệu (Boundaries), Ma trận kiểm soát lỗi và Đo lường định lượng bằng Golden Set.'</i>"
    story.append(Paragraph(learning_text, ParagraphStyle('HighlightBox', parent=quote_style, backColor=colors.HexColor('#FEF3C7'), borderColor=colors.HexColor('#F59E0B'))))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("Successfully built demo-slides.pdf")

if __name__ == "__main__":
    build_pdf()
