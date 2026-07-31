import json
import os
import re

from django.http import HttpResponse, JsonResponse
from .llm_provider import LLMProvider
from django.views.decorators.csrf import csrf_exempt

from .mcda_engine import calculate_mcda_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_FILE = os.path.join(BASE_DIR, "topics_data.json")
MOCK_PROFILES_FILE = os.path.join(BASE_DIR, "mork_data", "mock_profiles.json")


class APIValidationError(ValueError):
    def __init__(self, message, code="invalid_request"):
        super().__init__(message)
        self.code = code


def api_error(message, status=400, code="invalid_request", details=None):
    payload = {"error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    if status == 500:
        import traceback
        traceback.print_exc()
    return JsonResponse(payload, status=status)


def parse_json_body(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise APIValidationError(
            "Payload phải là JSON hợp lệ.", "invalid_json"
        ) from error
    if not isinstance(body, dict):
        raise APIValidationError("Payload JSON phải là một object.")
    return body


def require_list(body, field, allow_empty=False):
    value = body.get(field)
    if not isinstance(value, list) or (not allow_empty and not value):
        suffix = "" if allow_empty else " không rỗng"
        raise APIValidationError(f"{field} phải là một array{suffix}.")
    return value


def require_topic(topic_code):
    if not isinstance(topic_code, str) or not topic_code.strip():
        raise APIValidationError("topic_code là bắt buộc.", "missing_topic_code")
    topic_code = topic_code.strip().upper()
    topic = next(
        (item for item in load_json(TOPICS_FILE) if item.get("code") == topic_code),
        None,
    )
    if topic is None:
        raise APIValidationError(
            f"Không tìm thấy đề tài {topic_code}.", "topic_not_found"
        )
    return topic


def validate_team_members(team_members):
    if not isinstance(team_members, list) or not team_members:
        raise APIValidationError("team_members phải là một array không rỗng.")
    if not all(isinstance(member, dict) for member in team_members):
        raise APIValidationError("Mỗi team member phải là một object.")
    return team_members




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


def health(request):
    return JsonResponse({"status": "ok", "components": {"api": "ok", "mcda": "ok"}})




@csrf_exempt
def execute_tool(request):
    if request.method != "POST":
        return api_error("Only POST allowed", status=405)
    try:
        body = parse_json_body(request)
        tool_name = body.get("name")
        kwargs = body.get("kwargs", {})
        if not tool_name:
            return api_error("Missing tool name")

        from .agent_tools import AgentToolRegistry

        result = AgentToolRegistry.execute(tool_name, kwargs)
        return JsonResponse({"status": "success", "result": result})
    except Exception as e:
        return api_error(str(e))




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
        body = parse_json_body(request)
        team_members = validate_team_members(body.get("team_members", []))
        selected_codes = set(body.get("selected_codes", []))
        if not all(isinstance(code, str) for code in selected_codes):
            raise APIValidationError("selected_codes phải là array các chuỗi.")

        topics = load_json(TOPICS_FILE)
        target_topics = (
            [t for t in topics if t.get("code") in selected_codes]
            if selected_codes
            else topics
        )

        results = []
        for t in target_topics:
            res = calculate_mcda_score(team_members, t)
            results.append({**t, **res})

        results.sort(key=lambda x: x["finalScore"], reverse=True)
        return JsonResponse({"results": results, "count": len(results)})

    except APIValidationError as e:
        return api_error(str(e), status=400, code=getattr(e, "code", "invalid_request"))
    except Exception as e:
        return api_error(str(e), status=500, code="internal_error")


@csrf_exempt
def generate_deep_quiz(request):
    """
    Step 2: On-demand per-topic dynamic quiz generation via Registered Agent Tool.
    Generates dynamic abstract & deep technical essay/choice questions specific to ONE chosen topic.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = parse_json_body(request)
        topic_code = body.get("topic_code")
        team_members = body.get("team_members", [])
        topic = require_topic(topic_code)
        validate_team_members(team_members)

        mcda_res = calculate_mcda_score(team_members, topic) if team_members else {}
        missing_skills = [
            m["tech"] if isinstance(m, dict) else m
            for m in mcda_res.get("missingTechs", [])
        ]
        domain_mismatch = mcda_res.get("domainMismatch", False)
        outcome_res = AgentToolRegistry.execute(
            "analyze_topic_outcomes", {"topic": topic}
        )

        tool_res = AgentToolRegistry.execute(
            "generate_topic_deep_quiz",
            {
                "topic_code": topic_code,
                "topic_title": topic.get("title", ""),
                "missing_skills": missing_skills,
                "domain_mismatch": domain_mismatch,
                "outcomes": outcome_res.get("outcomes", []),
                "kpis": outcome_res.get("kpis", []),
                "constraints": outcome_res.get("constraints", []),
            },
        )

        if tool_res.get("error"):
            return api_error(tool_res.get("error"), status=500, code="tool_error")

        return JsonResponse(
            {
                "topic_code": topic_code,
                "topic_title": topic.get("title", ""),
                "questions": tool_res.get("questions", []),
                "outcome_analysis": outcome_res,
            }
        )
    except APIValidationError as e:
        status_code = 404 if e.code == "topic_not_found" else 400
        return api_error(str(e), status=status_code, code=getattr(e, "code", "invalid_request"))
    except Exception as e:
        return api_error(str(e), status=500, code="internal_error")


@csrf_exempt
def verify_declared_skills(request):
    """Generate practical verification questions for the skills a team declared."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        body = parse_json_body(request)
        declared_skills = body.get("declared_skills", [])
        if not isinstance(declared_skills, list) or not all(
            isinstance(skill, str) for skill in declared_skills
        ):
            raise APIValidationError("declared_skills must be an array of strings")

        tool_res = AgentToolRegistry.execute(
            "verify_declared_skills", {"declared_skills": declared_skills}
        )
        if tool_res.get("error"):
            return api_error(tool_res.get("error"), status=500, code="tool_error")
        return JsonResponse(tool_res)
    except APIValidationError as e:
        return api_error(str(e), status=400, code=getattr(e, "code", "invalid_request"))
    except Exception as e:
        return api_error(str(e), status=500, code="internal_error")



@csrf_exempt
def evaluate_what_if(request):
    """
    Step 4: What-If Analysis for demo.
    Simulates what happens to the score and risk if the team learns a specific skill.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = parse_json_body(request)
        topic_code = body.get("topic_code")
        team_members = validate_team_members(body.get("team_members", []))
        target_skill = str(body.get("target_skill", "")).strip()

        if not target_skill:
            raise APIValidationError("target_skill is required")

        topic = require_topic(topic_code)

        # Baseline evaluation
        base_mcda = calculate_mcda_score(team_members, topic)

        requirement_text = " ".join(
            [
                str(topic.get("tech_stack", "")),
                str(topic.get("requirements", "")),
                str(topic.get("description", "")),
            ]
        ).lower()
        if target_skill.lower() not in requirement_text:
            return JsonResponse(
                {
                    "topic_code": topic_code,
                    "target_skill": target_skill,
                    "baseline": {
                        "score": base_mcda["finalScore"],
                        "riskMatrix": base_mcda.get("riskMatrix"),
                    },
                    "what_if": None,
                    "score_improvement": 0,
                    "note": f"Skill '{target_skill}' không nằm trong yêu cầu của đề tài; điểm không thay đổi.",
                }
            )

        # Hypothetical evaluation (injecting target_skill to the first member)
        import copy

        hypothetical_members = copy.deepcopy(team_members)
        if len(hypothetical_members) > 0:
            if "proficiency" not in hypothetical_members[0]:
                hypothetical_members[0]["proficiency"] = {}
            hypothetical_members[0]["proficiency"][target_skill] = (
                3  # assume they learn it to level 3
            )

        new_mcda = calculate_mcda_score(hypothetical_members, topic)

        return JsonResponse(
            {
                "topic_code": topic_code,
                "target_skill": target_skill,
                "baseline": {
                    "score": base_mcda["finalScore"],
                    "riskMatrix": base_mcda.get("riskMatrix"),
                },
                "what_if": {
                    "score": new_mcda["finalScore"],
                    "riskMatrix": new_mcda.get("riskMatrix"),
                },
                "score_improvement": new_mcda["finalScore"] - base_mcda["finalScore"],
            }
        )

    except APIValidationError as e:
        return api_error(str(e), status=400, code=getattr(e, "code", "invalid_request"))
    except Exception as e:
        return api_error(str(e), status=500, code="internal_error")


@csrf_exempt
def advisor_chat(request):
    if request.method != "POST":
        return api_error("Only POST allowed", status=405)
    try:
        body = parse_json_body(request)
        message = str(body.get("message", "")).strip()
        history = body.get("history", [])
        provider = str(body.get("provider", "qwen")).strip()
        
        if provider == "gemini":
            api_key = str(body.get("api_key", "")).strip() or os.getenv("GEMINI_API_KEY", "")
        elif provider == "openai":
            api_key = str(body.get("api_key", "")).strip() or os.getenv("OPENAI_API_KEY", "")
        else:
            api_key = str(body.get("api_key", "")).strip() or os.getenv("QWEN_API_KEY", "")
        
        if not api_key:
            return JsonResponse({"reply": "API Key không hợp lệ. Vui lòng nhập API Key để dùng Chatbot.", "suggested_questions": []})
            
        schemas_str = json.dumps(AgentToolRegistry.get_tool_schemas(), ensure_ascii=False)
        system_prompt = f"""Bạn là MatchSkill AI Advisor - một AI thông minh phân tích, so sánh, và tư vấn đề tài.
Bạn có quyền gọi các công cụ (Tool Calling):
{schemas_str}

LUẬT BẮT BUỘC (QUAN TRỌNG):
1. TRẢ VỀ DUY NHẤT 1 JSON (KHÔNG CÓ MARKDOWN HOẶC BACKTICKS KHÁC).
2. Nếu người dùng muốn phân tích/đánh giá/tư vấn sâu và bạn cần gọi công cụ, TRẢ VỀ JSON CÓ CẤU TRÚC SAU (KHÔNG DÙNG BACKTICKS BAO QUANH JSON):
{{"tool_call_raw": {{"name": "tên_tool", "kwargs": {{"tham_số": "giá_trị"}}}}, "reply": "Đang gọi công cụ: tên_tool..."}}
3. Nếu trò chuyện thông thường hoặc đã có kết quả tool, TRẢ VỀ JSON:
{{"reply": "câu trả lời", "suggested_questions": ["câu 1", "câu 2"]}}
"""
        user_prompt = json.dumps({"history": history[-3:], "current_message": message}, ensure_ascii=False)
        llm_result = LLMProvider.call_llm(provider, api_key, system_prompt, user_prompt)
        
        if not llm_result:
            return JsonResponse({"reply": "Lỗi kết nối tới LLM.", "suggested_questions": []})
            
        if llm_result.get("tool_call_raw"):
            return JsonResponse({
                "reply": llm_result.get("reply", f"Đang gọi công cụ: {llm_result['tool_call_raw'].get('name')}..."),
                "tool_call_raw": llm_result["tool_call_raw"]
            })
            
        return JsonResponse({
            "reply": llm_result.get("reply", "Tôi chưa hiểu rõ yêu cầu."),
            "suggested_questions": llm_result.get("suggested_questions", [])[:3]
        })
    except Exception as e:
        return api_error(str(e))

@csrf_exempt
def evaluate_final(request):
    if request.method != "POST":
        return api_error("Only POST allowed", status=405)
    try:
        body = parse_json_body(request)
        topic_code = body.get("topic_code")
        team_members = validate_team_members(body.get("team_members", []))
        quiz_answers = body.get("quiz_answers", {})
        topic = require_topic(topic_code)
        
        base_mcda = calculate_mcda_score(team_members, topic)
        fit_state = base_mcda["fitState"]
        
        # Lean offline fallback directly inside the function
        evaluation = {
            "fitState": fit_state,
            "verdictTitle": base_mcda["verdictLabel"] + " (Offline Engine)",
            "transparentJustification": base_mcda["explanation"],
            "feasibilityIndex": 4.0 if fit_state == "PERFECT_FIT" else 2.5,
            "riskLevel": "Low" if fit_state == "PERFECT_FIT" else "High",
            "weeklyRoadmap": [
                {"week": 1, "title": "Tuần 1", "tasks": ["Khởi tạo", "Nghiên cứu yêu cầu"]},
                {"week": 2, "title": "Tuần 2", "tasks": ["Học kỹ năng thiếu", "Viết API"]},
                {"week": 3, "title": "Tuần 3", "tasks": ["Phát triển giao diện", "Kết nối DB"]},
                {"week": 4, "title": "Tuần 4", "tasks": ["Kiểm thử", "Sửa lỗi"]},
                {"week": 5, "title": "Tuần 5", "tasks": ["Hoàn thiện tài liệu"]},
                {"week": 6, "title": "Tuần 6", "tasks": ["Demo và bảo vệ đồ án"]}
            ],
            "requiredSkillSummary": {
                "covered": [m["tech"] for m in base_mcda["matchedTechs"]],
                "toLearn": [m["tech"] if isinstance(m, dict) else str(m) for m in base_mcda["missingTechs"]]
            },
            "decisionSource": "rule-based",
            "evidenceSnapshot": {
                "finalScore": base_mcda["finalScore"],
                "riskMatrix": base_mcda.get("riskMatrix", {})
            }
        }
        
        return JsonResponse({"topic_code": topic_code, "evaluation": evaluation, "base_mcda": base_mcda})
    except Exception as e:
        return api_error(str(e))
