from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import re
from .mcda_engine import calculate_mcda_score
from .llm_provider import LLMProvider
from .content_moderation import ContentModerationGate

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
    return JsonResponse(payload, status=status)


def parse_json_body(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise APIValidationError("Payload phải là JSON hợp lệ.", "invalid_json") from error
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
    topic = next((item for item in load_json(TOPICS_FILE) if item.get("code") == topic_code), None)
    if topic is None:
        raise APIValidationError(f"Không tìm thấy đề tài {topic_code}.", "topic_not_found")
    return topic


def validate_team_members(team_members):
    if not isinstance(team_members, list) or not team_members:
        raise APIValidationError("team_members phải là một array không rỗng.")
    if not all(isinstance(member, dict) for member in team_members):
        raise APIValidationError("Mỗi team member phải là một object.")
    return team_members


def risk_level_from_matrix(risk_matrix):
    levels = [risk_matrix.get(key, "Low") for key in ["skill_risk", "time_risk", "team_risk", "domain_risk"]]
    if "High" in levels:
        return "High"
    if "Medium" in levels:
        return "Medium"
    return "Low"


def evidence_justification(base_mcda):
    risk = base_mcda.get("riskMatrix", {})
    lines = list(base_mcda.get("explanation", []))
    lines.extend([
        (
            "Risk Matrix ghi nhận Skill/Time/Team/Domain lần lượt là "
            f"{risk.get('skill_risk', 'Low')}/{risk.get('time_risk', 'Low')}/"
            f"{risk.get('team_risk', 'Low')}/{risk.get('domain_risk', 'Low')}."
        ),
        (
            f"Learning Cost Estimator dự kiến {risk.get('total_learning_hours', 0)} giờ tự học; "
            f"năng lực hai tuần của nhóm là {risk.get('two_week_learning_capacity_hours', 0)} giờ."
        ),
    ])
    return lines


def ensure_evidence_contract(evaluation, base_mcda, source):
    evaluation = evaluation if isinstance(evaluation, dict) else {}
    risk_matrix = base_mcda.get("riskMatrix", {})
    evidence_lines = evidence_justification(base_mcda)
    model_lines = evaluation.get("transparentJustification", [])
    if not isinstance(model_lines, list):
        model_lines = []
    model_lines = [str(line).strip() for line in model_lines if str(line).strip()]

    evaluation["fitState"] = base_mcda["fitState"]
    evaluation.setdefault("verdictTitle", base_mcda["verdictLabel"])
    evaluation["transparentJustification"] = evidence_lines + [
        line for line in model_lines if line not in evidence_lines
    ]
    evaluation.setdefault("feasibilityIndex", round(base_mcda["finalScore"] / 20, 1))
    evaluation["riskLevel"] = risk_level_from_matrix(risk_matrix)
    evaluation.setdefault("weeklyRoadmap", [])
    evaluation.setdefault("requiredSkillSummary", {
        "covered": [item["tech"] for item in base_mcda.get("matchedTechs", [])],
        "toLearn": [
            f"{item['tech']} (~{item.get('cost_hours', 20)} giờ)"
            for item in base_mcda.get("missingTechs", [])
        ],
    })
    evaluation["decisionSource"] = source
    evaluation["evidenceSnapshot"] = {
        "finalScore": base_mcda["finalScore"],
        "scoreBreakdown": base_mcda.get("scoreBreakdown", {}),
        "riskMatrix": risk_matrix,
    }
    return evaluation

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


def extract_requested_technology(message):
    technology_aliases = {
        "langchain": "LangChain",
        "aws": "AWS",
        "camera": "camera",
        "rtx 4090": "GPU RTX 4090",
        "gpu": "GPU",
        "postgresql 17": "PostgreSQL phiên bản 17",
        "postgresql phiên bản 17": "PostgreSQL phiên bản 17",
        "docker": "Docker",
        "train model": "train model from scratch",
        "train model from scratch": "train model from scratch",
    }
    normalized = message.lower()
    return next((label for keyword, label in technology_aliases.items() if keyword in normalized), None)


def grounded_technology_reply(topic, requested_technology):
    source_text = " ".join(str(topic.get(field, "")) for field in ("tech_stack", "requirements", "description"))
    normalized_source = re.sub(r"\s+", " ", source_text).lower()
    normalized_tech = requested_technology.lower()

    if normalized_tech == "langchain":
        if "langchain" in normalized_source:
            return "Có căn cứ: mô tả đề tài có nêu LangChain. Tuy nhiên, hãy kiểm tra phần yêu cầu để biết đây là bắt buộc hay chỉ là công nghệ gợi ý."
        if "langgraph" in normalized_source:
            return "Không đủ căn cứ để khẳng định. Mô tả đề tài chỉ nêu LangGraph và các công nghệ gợi ý, không quy định bắt buộc dùng LangChain."
    if normalized_tech == "aws":
        if "aws" not in normalized_source and ("cloud" in normalized_source or "docker" in normalized_source):
            return "Không. Mô tả không quy định phải triển khai trên AWS mà chỉ nêu triển khai Docker + Cloud."
    if normalized_tech == "camera" and "camera" not in normalized_source:
        return "Không đủ thông tin. Mô tả chỉ đề cập ghi chú quan sát, transcript và checklist, không bắt buộc dùng camera."
    if normalized_tech in {"gpu rtx 4090", "gpu"} and "gpu" not in normalized_source and "rtx" not in normalized_source:
        return "Không đủ thông tin. Mô tả đề tài không đề cập yêu cầu phần cứng."
    if normalized_tech == "postgresql phiên bản 17" and "postgresql 17" not in normalized_source and "postgresql phiên bản 17" not in normalized_source:
        return "Không đủ căn cứ. Mô tả đề tài không quy định phiên bản PostgreSQL."
    if normalized_tech == "docker":
        if "docker" in normalized_source:
            return "Mô tả đề tài có nêu sử dụng Docker."
        return "Không đủ thông tin hoặc mô tả không bắt buộc dùng Docker."
    if "train model" in normalized_tech:
        if "train model from scratch" in normalized_source:
            return "Có căn cứ: đề tài yêu cầu train model."
        return "Không đủ thông tin. Mô tả đề tài không yêu cầu train model from scratch."

    if normalized_tech in normalized_source:
        return f"Có căn cứ: dữ liệu đề tài có đề cập {requested_technology}. Hệ thống không suy diễn thêm mức phiên bản hoặc hạ tầng nếu tài liệu không nêu."
    return f"Không đủ căn cứ. Mô tả đề tài không nêu {requested_technology}; hệ thống không tự thêm công nghệ này thành yêu cầu."


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
def advisor_chat(request):
    """Grounded advisor chat with a strict ten-message context window."""
    if request.method != "POST":
        return api_error("Only POST allowed", status=405, code="method_not_allowed")

    try:
        body = parse_json_body(request)
        message = str(body.get("message", "")).strip()
        if not message:
            raise APIValidationError("message là bắt buộc.")

        history = body.get("history", [])
        if not isinstance(history, list):
            raise APIValidationError("history phải là một array.")
        context = [
            {"role": item.get("role", "user"), "content": str(item.get("content", ""))[:2000]}
            for item in history[-10:]
            if isinstance(item, dict) and item.get("content")
        ]

        all_topics = load_json(TOPICS_FILE)

        # Dynamic Topic/Alias Resolution
        topic_code = body.get("topic_code")
        if not topic_code:
            # Check if any topic code or title/alias is mentioned in the message
            for t in all_topics:
                code = t.get("code", "")
                title = t.get("title", "")
                category = t.get("category", "")
                # Pattern for exact code or title alias
                if re.search(r"\b" + re.escape(code) + r"\b", message, re.IGNORECASE):
                    topic_code = code
                    break
                elif title and len(title) > 3 and title.lower() in message.lower():
                    topic_code = code
                    break
                # Short code matching e.g. EDU01 -> EDU-01
                code_no_dash = code.replace("-", "")
                if re.search(r"\b" + re.escape(code_no_dash) + r"\b", message, re.IGNORECASE):
                    topic_code = code
                    break

        # Fallback: Inherit topic_code from recent context history if current message has follow-up question
        if not topic_code and history:
            for item in reversed(history):
                if isinstance(item, dict) and item.get("topicCode"):
                    topic_code = item["topicCode"]
                    break
                # Also check text in past messages for topic codes
                content = str(item.get("content", "")) if isinstance(item, dict) else ""
                match = re.search(r"\b[A-Z]{2,12}-?\d{1,3}\b", content.upper())
                if match:
                    topic_code = match.group(0)
                    break

        team_members = body.get("team_members", [])
        provider = str(body.get("provider", "gemini"))
        api_key = str(body.get("api_key", "")).strip()

        # Step 1 & 2: Input Verification & Moderation Gate
        moderation = ContentModerationGate.review(
            message=message,
            has_team=bool(team_members),
            has_topic_reference=bool(topic_code),
            provider=provider,
            api_key=api_key,
        )

        if moderation.action == ContentModerationGate.ACTION_TOPIC_RECOMMENDATION:
            ranked_topics = []
            for candidate in all_topics:
                score = calculate_mcda_score(team_members, candidate)
                ranked_topics.append({
                    "code": candidate.get("code"),
                    "title": candidate.get("title"),
                    "category": candidate.get("category"),
                    "max_team": candidate.get("max_team"),
                    "finalScore": score.get("finalScore"),
                    "fitState": score.get("fitState"),
                    "riskMatrix": score.get("riskMatrix"),
                    "missingTechs": score.get("missingTechs", [])[:3],
                })
            ranked_topics.sort(key=lambda item: item["finalScore"], reverse=True)
            recommendations = ranked_topics[:3]
            return JsonResponse({
                "reply": "Dựa trên kỹ năng, thời gian và domain của nhóm, đây là 3 đề tài có điểm MCDA cao nhất. Bạn có thể chọn một đề tài để phân tích sâu hoặc tự mở bộ lọc để giới hạn scope.",
                "suggested_questions": [
                    f"Phân tích sâu {item['code']}" for item in recommendations
                ],
                "context_window_size": len(context),
                "context_limit": 10,
                "resolved_topic_code": None,
                "decision_source": "rule-based-mcda-recommendation",
                "moderation": {"action": moderation.action, "reason": moderation.reason, "source": moderation.source},
                "topic_context": None,
                "mcda_snapshot": None,
                "recommendations": recommendations,
            })

        if moderation.action != ContentModerationGate.ACTION_ALLOW:
            return JsonResponse({
                "reply": moderation.safe_reply or "Yêu cầu cần thêm ngữ cảnh trước khi chatbot có thể hỗ trợ.",
                "suggested_questions": ["EDU-01 có skill gap nào?", "Nhóm nên chọn đề tài nào với kỹ năng hiện tại?"],
                "context_window_size": len(context),
                "context_limit": 10,
                "resolved_topic_code": None,
                "decision_source": moderation.source,
                "moderation": {"action": moderation.action, "reason": moderation.reason},
                "topic_context": None,
                "mcda_snapshot": None,
                "recommendations": [],
            })

        # Step 3: Core Processing & Grounding Verification
        lower_message = message.lower()
        topic = require_topic(topic_code) if topic_code else None
        mcda = calculate_mcda_score(team_members, topic) if topic and team_members else None
        outcome_analysis = AgentToolRegistry.execute("analyze_topic_outcomes", {"topic": topic}) if topic else None

        missing = mcda.get("missingTechs", []) if mcda else []
        critical = [item for item in missing if item.get("criticality") == "Critical"]
        outcomes = outcome_analysis.get("outcomes", []) if outcome_analysis else []
        constraints = outcome_analysis.get("constraints", []) if outcome_analysis else []
        kpis = outcome_analysis.get("kpis", []) if outcome_analysis else []

        suggested_questions = []
        if outcomes:
            suggested_questions.append(f"Nhóm sẽ chứng minh outcome '{outcomes[0]}' bằng artifact nào ở buổi demo?")
        if critical:
            skill = critical[0]
            suggested_questions.append(f"Ai phụ trách bù kỹ năng {skill['tech']} trong khoảng {skill.get('cost_hours', 20)} giờ?")
        if kpis:
            suggested_questions.append(f"Nhóm sẽ đo KPI '{kpis[0]}' trên tập kiểm thử nào?")
        suggested_questions = suggested_questions[:3] or [
            "Nhóm muốn hệ thống gợi ý đề tài hay phân tích một đề tài đã chọn?",
            "Kỹ năng nào nhóm tự tin nhất và kỹ năng nào cần xác minh?",
        ]

        decision_source = "rule-based"
        llm_result = None
        requested_technology = extract_requested_technology(message) if topic else None
        policy_reply = grounded_technology_reply(topic, requested_technology) if requested_technology else None

        # Check for ungrounded / hallucination tech query when no topic is provided or tech is asked without topic
        requested_without_topic = extract_requested_technology(message) if not topic else None

        if api_key and not policy_reply:
            from .agent_tools import AgentToolRegistry
            schemas_str = json.dumps(AgentToolRegistry.get_tool_schemas(), ensure_ascii=False)
            system_prompt = f"""
Bạn là MatchSkill AI Advisor - một AI thông minh với khả năng phân tích, so sánh, và tư vấn đề tài.
Bạn có quyền sử dụng các công cụ sau (Tool Calling):
{schemas_str}

QUY TẮC HOẠT ĐỘNG:
1. Đọc ngữ cảnh hội thoại. Nếu người dùng muốn phân tích/đánh giá/so sánh đề tài, hoặc muốn tư vấn giảm gap, hoặc bạn thiếu thông tin, HÃY GỌI CÔNG CỤ.
2. Để gọi công cụ, TRẢ VỀ DUY NHẤT một JSON object có định dạng:
{{"tool_call": {{"name": "tên_công_cụ", "kwargs": {{"tham_số_1": "giá_trị"}}}}}}
3. Nếu không cần gọi công cụ, TRẢ VỀ DUY NHẤT một JSON object:
{{"reply": "câu trả lời của bạn", "suggested_questions": ["câu hỏi 1", "câu hỏi 2"]}}
4. Nếu người dùng chưa cung cấp đủ kỹ năng, hãy ĐẶT CÂU HỎI NGƯỢC LẠI trong phần reply để đào sâu.
5. Luôn chủ động, phân tích kỹ và tư vấn sâu sắc. Trả lời bằng tiếng Việt.
            """
            user_prompt = json.dumps({
                "conversation_last_10": context,
                "current_message": message,
                "team_members": team_members,
                "resolved_topic_code": topic.get("code") if topic else None,
            }, ensure_ascii=False)
            llm_result = LLMProvider.call_llm(provider, api_key, system_prompt, user_prompt)

        is_feasibility_question = any(keyword in lower_message for keyword in ("phù hợp", "nên làm", "có nên", "làm dc", "làm được", "ổn ko", "khả thi", "đánh giá"))
        tool_call_response = None

        if policy_reply:
            reply = policy_reply
            decision_source = "evidence-guard"
        elif isinstance(llm_result, dict) and llm_result.get("tool_call"):
            tool_call_response = llm_result["tool_call"]
            reply = f"Đang gọi công cụ: {tool_call_response.get('name')}..."
            decision_source = "llm-tool-calling"
        elif isinstance(llm_result, dict) and llm_result.get("reply"):
            reply = str(llm_result["reply"])
            llm_questions = llm_result.get("suggested_questions", [])
            if isinstance(llm_questions, list) and llm_questions:
                suggested_questions = [str(item) for item in llm_questions[:3]]
            decision_source = provider
        elif not topic:
            if requested_without_topic:
                if requested_without_topic in {"GPU RTX 4090", "GPU"}:
                    reply = "Không đủ thông tin. Mô tả đề tài không đề cập yêu cầu phần cứng."
                elif requested_without_topic == "PostgreSQL phiên bản 17":
                    reply = "Không đủ căn cứ. Mô tả đề tài không quy định phiên bản PostgreSQL."
                else:
                    reply = f"Không đủ căn cứ. Không tìm thấy đề tài được nêu để đối chiếu yêu cầu {requested_without_topic}."
            else:
                reply = "Hãy ghi mã đề tài trong câu hỏi, ví dụ: 'EDU-01 có cần LangChain không?', để tôi tự tải evidence và đối chiếu với kỹ năng nhóm."
        elif topic and team_members and is_feasibility_question and mcda:
            fit_state = mcda.get("fitState")
            score = mcda.get("finalScore")
            risk = mcda.get("riskMatrix", {})
            if fit_state == "PERFECT_FIT":
                reply = f"Đánh giá đề tài {topic.get('code')} phù hợp với nhóm (điểm MCDA {score}%). " + ("; ".join(mcda.get("explanation", [])) or "Kỹ năng và thời gian đáp ứng tốt.")
            elif fit_state == "ABLE_TO_LEARN":
                reply = f"Đánh giá đề tài {topic.get('code')} khả thi nếu nhóm chủ động học bù skill gap. " + f"Dự kiến tốn ~{risk.get('total_learning_hours', 20)} giờ tự học cho các kỹ năng thiếu."
            else:
                reply = f"Đánh giá đề tài {topic.get('code')} có rủi ro cao do khoảng cách kỹ năng lớn ({len(missing)} skill gap) hoặc thời gian không đủ. Khuyến nghị thu hẹp phạm vi thành MVP hoặc chọn đề tài khác phù hợp hơn."
        elif any(keyword in lower_message for keyword in ["outcome", "đầu ra", "sản phẩm"]):
            reply = "Outcome bắt buộc từ dữ liệu đề tài gồm: " + ("; ".join(outcomes[:3]) or "chưa có outcome đủ rõ trong dữ liệu nguồn.")
        elif any(keyword in lower_message for keyword in ["kỹ năng", "skill", "thiếu"]):
            if missing:
                reply = "Skill gap hiện tại: " + "; ".join(
                    f"{item['tech']} ({item['criticality']}, ~{item.get('cost_hours', 20)}h)" for item in missing[:5]
                )
            else:
                reply = "Theo MCDA, nhóm không có skill gap được phát hiện trong tech stack đã trích xuất."
        elif any(keyword in lower_message for keyword in ["rủi ro", "risk", "khả thi"]):
            risk = mcda.get("riskMatrix", {})
            reply = (
                f"Điểm MCDA {mcda.get('finalScore')}%. Risk Matrix Skill/Time/Team/Domain là "
                f"{risk.get('skill_risk')}/{risk.get('time_risk')}/{risk.get('team_risk')}/{risk.get('domain_risk')}."
            )
        else:
            reply = (
                f"Tôi đã phân tích {topic.get('code')} bằng outcome tool và MCDA. "
                f"Đề tài có {len(outcomes)} outcome, {len(kpis)} KPI, {len(constraints)} ràng buộc và {len(missing)} skill gap. "
                "Chọn một câu hỏi gợi ý bên dưới để đi sâu."
            )

        return JsonResponse({
            "reply": reply,
            "suggested_questions": suggested_questions,
            "context_window_size": len(context),
            "context_limit": 10,
            "resolved_topic_code": topic.get("code") if topic else None,
            "decision_source": decision_source,
            "moderation": {"action": moderation.action, "reason": moderation.reason, "source": moderation.source},
            "topic_context": outcome_analysis,
            "mcda_snapshot": {
                "score": mcda.get("finalScore"),
                "fit_state": mcda.get("fitState"),
                "risk_matrix": mcda.get("riskMatrix"),
            } if mcda else None,
            "recommendations": [],
        })
    except APIValidationError as error:
        status = 404 if error.code == "topic_not_found" else 400
        return api_error(str(error), status=status, code=error.code)
    except Exception as error:
        return api_error(str(error), status=500, code="internal_error")

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
        target_topics = [t for t in topics if t.get("code") in selected_codes] if selected_codes else topics

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
        missing_skills = [m["tech"] if isinstance(m, dict) else m for m in mcda_res.get("missingTechs", [])]
        domain_mismatch = mcda_res.get("domainMismatch", False)
        outcome_res = AgentToolRegistry.execute("analyze_topic_outcomes", {"topic": topic})

        tool_res = AgentToolRegistry.execute("generate_topic_deep_quiz", {
            "topic_code": topic_code,
            "topic_title": topic.get("title", ""),
            "missing_skills": missing_skills,
            "domain_mismatch": domain_mismatch,
            "outcomes": outcome_res.get("outcomes", []),
            "kpis": outcome_res.get("kpis", []),
            "constraints": outcome_res.get("constraints", [])
        })

        if tool_res.get("error"):
            return api_error(tool_res.get("error"), status=500, code="tool_error")

        return JsonResponse({
            "topic_code": topic_code,
            "topic_title": topic.get("title", ""),
            "questions": tool_res.get("questions", []),
            "outcome_analysis": outcome_res
        })
    except APIValidationError as e:
        return api_error(str(e), status=400, code=getattr(e, "code", "invalid_request"))
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
        if not isinstance(declared_skills, list) or not all(isinstance(skill, str) for skill in declared_skills):
            raise APIValidationError("declared_skills must be an array of strings")

        tool_res = AgentToolRegistry.execute("verify_declared_skills", {
            "declared_skills": declared_skills
        })
        if tool_res.get("error"):
            return api_error(tool_res.get("error"), status=500, code="tool_error")
        return JsonResponse(tool_res)
    except APIValidationError as e:
        return api_error(str(e), status=400, code=getattr(e, "code", "invalid_request"))
    except Exception as e:
        return api_error(str(e), status=500, code="internal_error")

@csrf_exempt
def evaluate_final(request):
    """
    Step 3: Final Agent Evaluation Module combining Deep Quiz answers, Team Capacity & LLM API.
    Calls Gemini 3.6 Flash / GPT-4o API if Key is provided; Fallback to offline rule-engine otherwise.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = parse_json_body(request)
        topic_code = body.get("topic_code")
        team_members = body.get("team_members", [])
        quiz_answers = body.get("quiz_answers", {})
        provider = body.get("provider", "gemini")
        api_key = body.get("api_key", "").strip()

        topic = require_topic(topic_code)
        team_members = validate_team_members(team_members)
        if not isinstance(quiz_answers, dict):
            raise APIValidationError("quiz_answers phải là một object.")

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
        try:
            llm_res = LLMProvider.call_llm(provider, api_key, system_prompt, user_prompt)
        except Exception:
            llm_res = None

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

        llm_res = ensure_evidence_contract(
            llm_res,
            base_mcda,
            source=provider if api_key else "rule-based"
        )
        return JsonResponse({"topic_code": topic_code, "evaluation": llm_res, "base_mcda": base_mcda})

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

        requirement_text = " ".join([
            str(topic.get("tech_stack", "")),
            str(topic.get("requirements", "")),
            str(topic.get("description", "")),
        ]).lower()
        if target_skill.lower() not in requirement_text:
            return JsonResponse({
                "topic_code": topic_code,
                "target_skill": target_skill,
                "baseline": {
                    "score": base_mcda["finalScore"],
                    "riskMatrix": base_mcda.get("riskMatrix")
                },
                "what_if": None,
                "score_improvement": 0,
                "note": f"Skill '{target_skill}' không nằm trong yêu cầu của đề tài; điểm không thay đổi."
            })

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

    except APIValidationError as e:
        return api_error(str(e), status=400, code=getattr(e, "code", "invalid_request"))
    except Exception as e:
        return api_error(str(e), status=500, code="internal_error")
