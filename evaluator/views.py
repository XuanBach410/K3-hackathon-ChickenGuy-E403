from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from .mcda_engine import calculate_mcda_score
from .llm_provider import LLMProvider

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
TOPICS_FILE = os.path.join(BASE_DIR, "topics_data.json")
MOCK_PROFILES_FILE = os.path.join(BASE_DIR, "mork_data", "mock_profiles.json")

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def serve_index(request):
    react_dist_path = os.path.join(BASE_DIR, "frontend", "dist", "index.html")
    if os.path.exists(react_dist_path):
        with open(react_dist_path, "r", encoding="utf-8") as f:
            return HttpResponse(f.read(), content_type="text/html")
    
    legacy_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(legacy_path):
        with open(legacy_path, "r", encoding="utf-8") as f:
            return HttpResponse(f.read(), content_type="text/html")
            
    return HttpResponse("Frontend React build not found", status=404)

@csrf_exempt
def get_topics(request):
    topics = load_json(TOPICS_FILE)
    return JsonResponse({"topics": topics, "count": len(topics)})

@csrf_exempt
def get_mock_profiles(request):
    profiles = load_json(MOCK_PROFILES_FILE)
    return JsonResponse({"profiles": profiles, "count": len(profiles)})

@csrf_exempt
def evaluate_preliminary(request):
    """
    Step 1: Client-side / DRF fast preliminary fitting for multi-selected topics (0$ API Cost).
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
        team_members = body.get("team_members", [])
        selected_codes = set(body.get("selected_codes", []))

        topics = load_json(TOPICS_FILE)
        target_topics = [t for t in topics if t.get("code") in selected_codes] if selected_codes else topics

        results = []
        for t in target_topics:
            res = calculate_mcda_score(team_members, t)
            results.append({**t, **res})

        results.sort(key=lambda x: x["finalScore"], reverse=True)
        return JsonResponse({"results": results, "count": len(results)})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def generate_deep_quiz(request):
    """
    Step 2: On-demand per-topic dynamic quiz generation.
    Generates 3-5 abstract & deep questions specific to ONE chosen topic.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
        topic_code = body.get("topic_code")
        missing_skills = body.get("missing_skills", [])
        domain_mismatch = body.get("domain_mismatch", False)

        topics = load_json(TOPICS_FILE)
        topic = next((t for t in topics if t.get("code") == topic_code), {})

        # Default dynamic questions
        questions = [
          {
            "id": 1,
            "question": f"Nhóm bạn hình dung như thế nào về kết quả đầu ra thực tế của đề tài '{topic.get('title', topic_code)}'?",
            "type": "scale",
            "options": ["Chưa hình dung", "Hiểu mơ hồ", "Hình dung khá rõ", "Đã có bản thiết kế chi tiết"]
          },
          {
            "id": 2,
            "question": f"Đối với các kỹ năng chưa có ({', '.join(missing_skills) if missing_skills else 'công nghệ nâng cao'}), nhóm kế hoạch bù đắp thế nào trong 6 tuần?",
            "type": "choice",
            "options": [
              "Học qua tài liệu chính thức & bài tập ngắn (1-2 tuần đầu)",
              "Phân chia người chuyên trách học rồi hướng dẫn lại nhóm",
              "Chưa có kế hoạch cụ thể",
              "Sẽ nhờ cố vấn/TA hỗ trợ trực tiếp"
            ]
          },
          {
            "id": 3,
            "question": "Mỗi thành viên trong nhóm có thể cam kết tối thiểu bao nhiêu giờ/ngày cho dự án này?",
            "type": "number",
            "default": 3
          },
          {
            "id": 4,
            "question": "Nhóm đã từng làm dự án/bài tập có độ phức tạp tương đương bài toán này chưa?",
            "type": "choice",
            "options": [
              "Đã từng làm và hoàn thành tốt",
              "Đã từng làm nhưng chưa tới đâu",
              "Chưa từng làm dự án nào tương tự",
              "Có thành viên nòng cốt từng làm"
            ]
          }
        ]

        if domain_mismatch:
          questions.append({
            "id": 5,
            "question": "Đề tài thuộc lĩnh vực mới so với chuyên môn nhóm. Lý do chính nhóm vẫn muốn chọn là gì?",
            "type": "text",
            "placeholder": "Ví dụ: Muốn thử sức với AI Robotics, sẵn sàng bỏ thêm thời gian..."
          })

        return JsonResponse({
            "topic_code": topic_code,
            "topic_title": topic.get("title", ""),
            "questions": questions
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def evaluate_final(request):
    """
    Step 3: Final Agent Evaluation Module combining Deep Quiz answers, Team Capacity & LLM API.
    Calls Gemini 3.6 Flash / GPT-4o API if Key is provided; Fallback to offline rule-engine otherwise.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
        topic_code = body.get("topic_code")
        team_members = body.get("team_members", [])
        quiz_answers = body.get("quiz_answers", {})
        provider = body.get("provider", "gemini")
        api_key = body.get("api_key", "").strip()

        topics = load_json(TOPICS_FILE)
        topic = next((t for t in topics if t.get("code") == topic_code), {})

        # Run Preliminary MCDA Base Score
        base_mcda = calculate_mcda_score(team_members, topic)

        # Build System Prompt & Instructions
        system_prompt = """
        Bạn là Chuyên gia Cố vấn Công nghệ & Đào tạo xuất sắc (Chief Academic & Tech Advisor) cho Mini Hackathon AI.
        Nhiệm vụ của bạn là đánh giá khả thi việc chọn đề tài của nhóm học viên và sinh lộ trình 6 tuần.

        Hãy trả về định dạng JSON thuần túy gồm:
        {
          "fitState": "PERFECT_FIT" | "ABLE_TO_LEARN" | "NOT_ABLE_TO_LEARN",
          "verdictTitle": "Tiêu đề kết luận",
          "transparentJustification": ["Lý do 1 kèm bằng chứng", "Lý do 2"],
          "feasibilityIndex": 4.2, // Thang 5.0
          "riskLevel": "Low" | "Medium" | "High",
          "weeklyRoadmap": [
             {"week": 1, "title": "Tuần 1", "tasks": ["Task 1", "Task 2"]},
             {"week": 2, "title": "Tuần 2", "tasks": ["Task 1", "Task 2"]},
             {"week": 3, "title": "Tuần 3", "tasks": ["Task 1"]},
             {"week": 4, "title": "Tuần 4", "tasks": ["Task 1"]},
             {"week": 5, "title": "Tuần 5", "tasks": ["Task 1"]},
             {"week": 6, "title": "Tuần 6", "tasks": ["Task 1"]}
          ],
          "requiredSkillSummary": {
             "covered": ["Python", "SQL"],
             "toLearn": ["Docker (~3 ngày)", "RAG (~5 ngày)"]
          }
        }
        """

        user_prompt = f"""
        - Đề tài: [{topic_code}] {topic.get('title')}
        - Yêu cầu đề tài: {topic.get('requirements')}
        - Điểm sơ bộ MCDA: {base_mcda['finalScore']}% ({base_mcda['verdictLabel']})
        - Kỹ năng nhóm hiện có: {[m.get('name') + ': ' + str(m.get('proficiency')) for m in team_members]}
        - Kỹ năng thiếu: {base_mcda['missingTechs']}
        - Lệch Domain: {base_mcda['domainMismatch']}
        - Trả lời Đánh Giá Sâu: {json.dumps(quiz_answers, ensure_ascii=False)}
        """

        # Call LLM Provider
        llm_res = LLMProvider.call_llm(provider, api_key, system_prompt, user_prompt)

        # Fallback Mechanism if API call fails or no API Key
        if not llm_res:
            hours = int(quiz_answers.get("3", 3)) if isinstance(quiz_answers.get("3"), (int, str)) else 3
            fit_state = base_mcda["fitState"]
            
            llm_res = {
                "fitState": fit_state,
                "verdictTitle": base_mcda["verdictLabel"] + " (Offline Fallback Engine)",
                "transparentJustification": base_mcda["explanation"] + [
                    f"Tổng thời gian cam kết của nhóm: {hours * len(team_members) * 5} giờ/tuần.",
                    "Đánh giá dựa trên ma trận tiêu chí MCDA chuẩn (criteria.md)."
                ],
                "feasibilityIndex": 4.5 if fit_state == "PERFECT_FIT" else 3.2 if fit_state == "ABLE_TO_LEARN" else 1.8,
                "riskLevel": "Low" if fit_state == "PERFECT_FIT" else "Medium" if fit_state == "ABLE_TO_LEARN" else "High",
                "weeklyRoadmap": [
                    {"week": 1, "title": "Tuần 1: Khởi tạo & Nghiên cứu", "tasks": ["Thiết lập môi trường", "Học bổ sung kỹ năng thiếu: " + ", ".join(base_mcda["missingTechs"][:2])]},
                    {"week": 2, "title": "Tuần 2: Xây dựng Prototype MVP", "tasks": ["Xây dựng các API cốt lõi", "Tích hợp dữ liệu thử nghiệm"]},
                    {"week": 3, "title": "Tuần 3: Hoàn thiện Tính năng", "tasks": ["Ghép nối Frontend + Backend", "Đánh giá nội bộ lần 1"]},
                    {"week": 4, "title": "Tuần 4: Kiểm thử & Tối ưu", "tasks": ["Chạy test cases với 3+ user thật", "Sửa lỗi và tối ưu hiệu năng"]},
                    {"week": 5, "title": "Tuần 5: Tài liệu & Nâng cao", "tasks": ["Viết báo cáo spec.md", "Chuẩn bị slide demo 6 trang"]},
                    {"week": 6, "title": "Tuần 6: Demo & Bảo vệ", "tasks": ["Chạy thử dry run", "Bảo vệ đồ án tại CP6"]}
                ],
                "requiredSkillSummary": {
                    "covered": [m["tech"] for m in base_mcda["matchedTechs"]],
                    "toLearn": [m + " (~3-5 ngày)" for m in base_mcda["missingTechs"]]
                }
            }

        return JsonResponse({"topic_code": topic_code, "evaluation": llm_res, "base_mcda": base_mcda})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
