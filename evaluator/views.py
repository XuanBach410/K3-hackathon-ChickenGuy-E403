from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from .mcda_engine import calculate_mcda_score
from .llm_provider import LLMProvider

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

from .agent_tools import AgentToolRegistry

@csrf_exempt
def get_registered_agent_tools(request):
    """
    DevTool Endpoint: Exposes all registered Agent Tools & Function Calling Schemas.
    """
    schemas = AgentToolRegistry.get_tool_schemas()
    return JsonResponse({"registered_tools": schemas, "count": len(schemas)})

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
    Step 2: On-demand per-topic dynamic quiz generation via Registered Agent Tool.
    Generates dynamic abstract & deep technical essay/choice questions specific to ONE chosen topic.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
        topic_code = body.get("topic_code")
        team_members = body.get("team_members", [])

        topics = load_json(TOPICS_FILE)
        topic = next((t for t in topics if t.get("code") == topic_code), {})
        
        # Calculate MCDA gap context
        mcda_res = calculate_mcda_score(team_members, topic) if team_members else {}
        missing_skills = [m["tech"] if isinstance(m, dict) else m for m in mcda_res.get("missingTechs", [])]
        domain_mismatch = mcda_res.get("domainMismatch", False)

        # Execute Registered Agent Tool
        tool_res = AgentToolRegistry.execute("generate_topic_deep_quiz", {
            "topic_code": topic_code,
            "topic_title": topic.get("title", ""),
            "missing_skills": missing_skills,
            "domain_mismatch": domain_mismatch
        })

        return JsonResponse({
            "topic_code": topic_code,
            "topic_title": topic.get("title", ""),
            "questions": tool_res.get("questions", [])
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
        Nhiệm vụ của bạn là đánh giá khả thi việc chọn đề tài của nhóm học viên, phân tích rủi ro định lượng, và sinh lộ trình 6 tuần.
        Bắt buộc sử dụng thông tin từ 'Ma trận rủi ro (Risk Matrix)' để làm bằng chứng (Evidence) biện luận cho kết luận của bạn.

        Hãy trả về định dạng JSON thuần túy gồm:
        {
          "fitState": "PERFECT_FIT" | "ABLE_TO_LEARN" | "NOT_ABLE_TO_LEARN",
          "verdictTitle": "Tiêu đề kết luận",
          "transparentJustification": ["Theo ma trận rủi ro, kỹ năng X là Critical nên...", "Dự kiến tốn Y giờ tự học..."],
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
             "toLearn": ["Docker (~15 giờ)", "RAG (~35 giờ)"]
          }
        }
        """

        missing_formatted = [f"{m['tech']} (Mức độ: {m.get('criticality')}, {m.get('cost_hours')} giờ)" if isinstance(m, dict) else m for m in base_mcda.get('missingTechs', [])]

        user_prompt = f"""
        - Đề tài: [{topic_code}] {topic.get('title')}
        - Yêu cầu đề tài: {topic.get('requirements')}
        - Điểm sơ bộ MCDA: {base_mcda['finalScore']}% ({base_mcda['verdictLabel']})
        - Ma trận Rủi ro (Risk Matrix): {json.dumps(base_mcda.get('riskMatrix', {}))}
        - Kỹ năng nhóm hiện có: {[m.get('name') + ': ' + str(m.get('proficiency')) for m in team_members]}
        - Kỹ năng thiếu (phân loại & chi phí): {missing_formatted}
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
                    {"week": 1, "title": "Tuần 1: Khởi tạo & Nghiên cứu", "tasks": ["Thiết lập môi trường", "Học bổ sung kỹ năng thiếu: " + ", ".join([m["tech"] if isinstance(m, dict) else m for m in base_mcda["missingTechs"][:2]])]},
                    {"week": 2, "title": "Tuần 2: Xây dựng Prototype MVP", "tasks": ["Xây dựng các API cốt lõi", "Tích hợp dữ liệu thử nghiệm"]},
                    {"week": 3, "title": "Tuần 3: Hoàn thiện Tính năng", "tasks": ["Ghép nối Frontend + Backend", "Đánh giá nội bộ lần 1"]},
                    {"week": 4, "title": "Tuần 4: Kiểm thử & Tối ưu", "tasks": ["Chạy test cases với 3+ user thật", "Sửa lỗi và tối ưu hiệu năng"]},
                    {"week": 5, "title": "Tuần 5: Tài liệu & Nâng cao", "tasks": ["Viết báo cáo spec.md", "Chuẩn bị slide demo 6 trang"]},
                    {"week": 6, "title": "Tuần 6: Demo & Bảo vệ", "tasks": ["Chạy thử dry run", "Bảo vệ đồ án tại CP6"]}
                ],
                "requiredSkillSummary": {
                    "covered": [m["tech"] for m in base_mcda["matchedTechs"]],
                    "toLearn": [f"{m['tech']} (~{m.get('cost_hours', 20)} giờ)" if isinstance(m, dict) else f"{m} (~20 giờ)" for m in base_mcda["missingTechs"]]
                }
            }

        return JsonResponse({"topic_code": topic_code, "evaluation": llm_res, "base_mcda": base_mcda})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def evaluate_what_if(request):
    """
    Step 4: What-If Analysis for demo.
    Simulates what happens to the score and risk if the team learns a specific skill.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    
    try:
        body = json.loads(request.body.decode("utf-8"))
        topic_code = body.get("topic_code")
        team_members = body.get("team_members", [])
        target_skill = body.get("target_skill", "").strip()

        if not target_skill:
            return JsonResponse({"error": "target_skill is required"}, status=400)

        topics = load_json(TOPICS_FILE)
        topic = next((t for t in topics if t.get("code") == topic_code), {})

        # Baseline evaluation
        base_mcda = calculate_mcda_score(team_members, topic)

        # Hypothetical evaluation (injecting target_skill to the first member)
        import copy
        hypothetical_members = copy.deepcopy(team_members)
        if len(hypothetical_members) > 0:
            if "proficiency" not in hypothetical_members[0]:
                hypothetical_members[0]["proficiency"] = {}
            hypothetical_members[0]["proficiency"][target_skill] = 3 # assume they learn it to level 3

        new_mcda = calculate_mcda_score(hypothetical_members, topic)

        return JsonResponse({
            "topic_code": topic_code,
            "target_skill": target_skill,
            "baseline": {
                "score": base_mcda["finalScore"],
                "riskMatrix": base_mcda.get("riskMatrix")
            },
            "what_if": {
                "score": new_mcda["finalScore"],
                "riskMatrix": new_mcda.get("riskMatrix")
            },
            "score_improvement": new_mcda["finalScore"] - base_mcda["finalScore"]
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
