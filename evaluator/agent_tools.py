import json
from .mcda_engine import calculate_mcda_score, extract_latent_skills

class AgentToolRegistry:
    """
    Central Agent Tool Registry & Function Calling Execution Engine for MatchSkill AI.
    """
    _tools = {}

    @classmethod
    def register(cls, name, description, parameters):
        def decorator(func):
            cls._tools[name] = {
                "name": name,
                "description": description,
                "parameters": parameters,
                "func": func
            }
            return func
        return decorator

    @classmethod
    def get_tool_schemas(cls):
        """Returns JSON schema for OpenAI/Gemini function calling declaration."""
        return [
            {
                "name": meta["name"],
                "description": meta["description"],
                "parameters": meta["parameters"]
            }
            for meta in cls._tools.values()
        ]

    @classmethod
    def execute(cls, tool_name, kwargs):
        if tool_name not in cls._tools:
            return {"error": f"Tool '{tool_name}' not registered."}
        try:
            return cls._tools[tool_name]["func"](**kwargs)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}


# =====================================================================
# AGENT TOOL DEFINITIONS & REGISTRATION
# =====================================================================

@AgentToolRegistry.register(
    name="parse_member_profile",
    description="Parse và trích xuất kỹ năng ẩn (latent skills) từ đoạn giới thiệu bản thân của học viên.",
    parameters={
        "type": "object",
        "properties": {
            "profile_text": {"type": "string", "description": "Đoạn văn giới thiệu bản thân"},
            "proficiency": {"type": "object", "description": "Kỹ năng đã khai báo thủ công"}
        },
        "required": ["profile_text"]
    }
)
def parse_member_profile_tool(profile_text, proficiency=None):
    member_mock = {"introduction": profile_text, "proficiency": proficiency or {}}
    extracted = extract_latent_skills(member_mock)
    return {
        "status": "success",
        "latent_skills": extracted,
        "skill_count": len(extracted)
    }


@AgentToolRegistry.register(
    name="evaluate_preliminary_fit",
    description="Tính toán điểm MCDA sơ bộ cho danh sách đề tài multi-select dựa trên ma trận C1-C4.",
    parameters={
        "type": "object",
        "properties": {
            "team_members": {"type": "array", "description": "Danh sách thành viên nhóm"},
            "topic": {"type": "object", "description": "Đối tượng dữ liệu đề tài"}
        },
        "required": ["team_members", "topic"]
    }
)
def evaluate_preliminary_fit_tool(team_members, topic):
    mcda_res = calculate_mcda_score(team_members, topic)
    return {
        "status": "success",
        "mcda_result": mcda_res
    }


@AgentToolRegistry.register(
    name="generate_topic_deep_quiz",
    description="Sinh bộ câu hỏi trừu tượng và chuyên sâu (3-5 câu) thiết kế riêng cho MỘT đề tài cụ thể dựa trên skill gap.",
    parameters={
        "type": "object",
        "properties": {
            "topic_code": {"type": "string", "description": "Mã đề tài"},
            "missing_skills": {"type": "array", "description": "Danh sách kỹ năng thiếu"},
            "domain_mismatch": {"type": "boolean", "description": "Có bị lệch domain không"}
        },
        "required": ["topic_code"]
    }
)
def generate_topic_deep_quiz_tool(topic_code, missing_skills=None, domain_mismatch=False):
    questions = [
        {"id": 1, "question": f"Mức độ hiểu về sản phẩm đầu ra của đề tài [{topic_code}]?", "type": "scale"},
        {"id": 2, "question": f"Kế hoạch bù đắp các skill thiếu ({', '.join(missing_skills or ['nâng cao'])}):", "type": "choice"},
        {"id": 3, "question": "Số giờ/ngày mỗi thành viên sẵn sàng cam kết?", "type": "number", "default": 3}
    ]
    if domain_mismatch:
        questions.append({"id": 4, "question": "Lý do chính nhóm chọn đề tài mới ngoài chuyên môn?", "type": "text"})
    return {"status": "success", "topic_code": topic_code, "questions": questions}
