import re

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
                "func": func,
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
                "parameters": meta["parameters"],
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
            return {"error": f"Tool execution failed: {e!s}"}


# =====================================================================
# AGENT TOOL DEFINITIONS & REGISTRATION
# =====================================================================


@AgentToolRegistry.register(
    name="parse_member_profile",
    description="Parse và trích xuất kỹ năng ẩn (latent skills) từ đoạn giới thiệu bản thân của học viên.",
    parameters={
        "type": "object",
        "properties": {
            "profile_text": {
                "type": "string",
                "description": "Đoạn văn giới thiệu bản thân",
            },
            "proficiency": {
                "type": "object",
                "description": "Kỹ năng đã khai báo thủ công",
            },
        },
        "required": ["profile_text"],
    },
)
def parse_member_profile_tool(profile_text, proficiency=None):
    member_mock = {"introduction": profile_text, "proficiency": proficiency or {}}
    extracted = extract_latent_skills(member_mock)
    return {
        "status": "success",
        "latent_skills": extracted,
        "skill_count": len(extracted),
    }


@AgentToolRegistry.register(
    name="evaluate_preliminary_fit",
    description="Tính toán điểm MCDA sơ bộ cho danh sách đề tài multi-select dựa trên ma trận C1-C4.",
    parameters={
        "type": "object",
        "properties": {
            "team_members": {
                "type": "array",
                "description": "Danh sách thành viên nhóm",
            },
            "topic": {"type": "object", "description": "Đối tượng dữ liệu đề tài"},
        },
        "required": ["team_members", "topic"],
    },
)
def evaluate_preliminary_fit_tool(team_members, topic):
    mcda_res = calculate_mcda_score(team_members, topic)
    return {"status": "success", "mcda_result": mcda_res}


@AgentToolRegistry.register(
    name="generate_topic_deep_quiz",
    description="Sinh bộ câu hỏi trừu tượng và chuyên sâu (thang điểm, trắc nghiệm, tự luận) thiết kế riêng cho MỘT đề tài cụ thể dựa trên skill gap.",
    parameters={
        "type": "object",
        "properties": {
            "topic_code": {"type": "string", "description": "Mã đề tài"},
            "topic_title": {"type": "string", "description": "Tên đề tài"},
            "missing_skills": {
                "type": "array",
                "description": "Danh sách kỹ năng thiếu",
            },
            "domain_mismatch": {
                "type": "boolean",
                "description": "Có bị lệch domain không",
            },
            "outcomes": {
                "type": "array",
                "description": "Outcome đã trích từ dữ liệu đề tài",
            },
            "kpis": {"type": "array", "description": "KPI đã trích từ dữ liệu đề tài"},
            "constraints": {
                "type": "array",
                "description": "Ràng buộc đã trích từ dữ liệu đề tài",
            },
        },
        "required": ["topic_code"],
    },
)
def generate_topic_deep_quiz_tool(
    topic_code,
    topic_title="",
    missing_skills=None,
    domain_mismatch=False,
    outcomes=None,
    kpis=None,
    constraints=None,
):
    missing_str = ", ".join(missing_skills) if missing_skills else "công nghệ nâng cao"
    primary_outcome = outcomes[0] if outcomes else f"prototype của {topic_code}"
    primary_kpi = kpis[0] if kpis else "KPI thành công do nhóm xác định"
    primary_constraint = (
        constraints[0] if constraints else "ràng buộc vận hành của đề tài"
    )

    questions = [
        {
            "id": 1,
            "question": f"Nhóm hình dung artifact demo nào để chứng minh outcome: '{primary_outcome}'?",
            "type": "scale",
            "options": [
                "1. Chưa hình dung",
                "2. Mơ hồ",
                "3. Khá rõ",
                "4. Đã có kiến trúc",
                "5. Rất rõ ràng",
            ],
        },
        {
            "id": 2,
            "question": f"Để đạt outcome của [{topic_code}], nhóm sẽ bù các kỹ năng còn thiếu ({missing_str}) như thế nào trong 6 tuần?",
            "type": "choice",
            "options": [
                "Học qua tài liệu chính thức & bài tập ngắn (1-2 tuần đầu)",
                "Phân chia người chuyên trách học rồi hướng dẫn lại nhóm",
                "Chưa có kế hoạch cụ thể",
                "Sẽ nhờ cố vấn/TA hỗ trợ trực tiếp",
            ],
        },
        {
            "id": 3,
            "question": "Mỗi thành viên trong nhóm có thể cam kết tối thiểu bao nhiêu giờ/ngày cho dự án này?",
            "type": "number",
            "default": 3,
        },
        {
            "id": 4,
            "question": f"[Thiết kế & Đo lường] Mô tả kiến trúc cốt lõi, cách đo '{primary_kpi}' và cách tuân thủ '{primary_constraint}'.",
            "type": "text",
            "placeholder": f"Nhập câu trả lời tự luận (ví dụ: Dùng RAG kết hợp Vector DB để xây dựng Agent cá nhân hóa cho {topic_code}...)",
        },
    ]

    if domain_mismatch:
        questions.append(
            {
                "id": 5,
                "question": f"[Lệch Domain] Đề tài [{topic_code}] thuộc lĩnh vực mới so với chuyên môn nhóm. Lý do và động lực chính nhóm vẫn muốn chọn là gì?",
                "type": "text",
                "placeholder": "Nhập lý do nhóm sẵn sàng vượt rào cản domain...",
            }
        )

    return {"status": "success", "topic_code": topic_code, "questions": questions}


@AgentToolRegistry.register(
    name="analyze_topic_outcomes",
    description="Phân tích outcome, KPI và ràng buộc của đề tài từ dữ liệu nguồn để làm căn cứ đặt câu hỏi đánh giá linh động.",
    parameters={
        "type": "object",
        "properties": {
            "topic": {
                "type": "object",
                "description": "Đề tài đầy đủ từ topics_data.json",
            }
        },
        "required": ["topic"],
    },
)
def analyze_topic_outcomes_tool(topic):
    requirements = str(topic.get("requirements", ""))
    description = str(topic.get("description", ""))
    tech_stack = str(topic.get("tech_stack", ""))

    def extract_bullets(text):
        normalized = re.sub(r"\s+", " ", text).strip()
        fragments = re.split(r"\s*•\s*", normalized)
        return [item.strip(" :-")[:260] for item in fragments if len(item.strip()) > 12]

    requirement_items = extract_bullets(requirements)
    description_items = extract_bullets(description)
    tech_items = extract_bullets(tech_stack)

    source_sentences = re.split(
        r"(?<=[.!?])\s+|\s*•\s*", re.sub(r"\s+", " ", f"{description} {requirements}")
    )
    kpi_keywords = (
        "kpi",
        "metric",
        "độ chính xác",
        "tỷ lệ",
        "precision",
        "recall",
        "≥",
        "%",
    )
    kpis = [
        sentence.strip(" :-")[:260]
        for sentence in source_sentences
        if any(keyword in sentence.lower() for keyword in kpi_keywords)
    ]

    constraint_keywords = (
        "ràng buộc",
        "không",
        "bắt buộc",
        "phân quyền",
        "ẩn danh",
        "guardrail",
        "hitl",
        "chi phí",
        "độ trễ",
    )
    constraints = [
        item
        for item in description_items + requirement_items
        if any(keyword in item.lower() for keyword in constraint_keywords)
    ]

    basic_marker = requirements.lower().find("cơ bản")
    advanced_marker = requirements.lower().find("nâng cao")
    basic_text = (
        requirements[basic_marker:advanced_marker]
        if basic_marker >= 0 and advanced_marker > basic_marker
        else requirements
    )
    outcomes = extract_bullets(basic_text)[:6]

    return {
        "status": "success",
        "topic_code": topic.get("code"),
        "outcomes": outcomes,
        "kpis": list(dict.fromkeys(kpis))[:4],
        "constraints": list(dict.fromkeys(constraints))[:5],
        "suggested_tech": tech_items[:8],
        "source": "topics_data.json",
    }


@AgentToolRegistry.register(
    name="verify_declared_skills",
    description="Xác minh trình độ thực tế của các kỹ năng được khai báo bằng các câu hỏi trắc nghiệm chuyên môn.",
    parameters={
        "type": "object",
        "properties": {
            "declared_skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Danh sách các kỹ năng nhóm tự khai báo (VD: ['Docker', 'Python'])",
            }
        },
        "required": ["declared_skills"],
    },
)
def verify_declared_skills_tool(declared_skills):
    question_bank = {
        "docker": {
            "question": "Bạn đã từng thực hiện thao tác nào với Docker?",
            "options": [
                "Chưa từng dùng",
                "Pull và run image có sẵn",
                "Tự viết Dockerfile cơ bản",
                "Dùng Docker Compose chạy multi-container",
                "Triển khai Kubernetes/Swarm",
            ],
            "levels": [0, 1, 2, 3, 4],
        },
        "python": {
            "question": "Kinh nghiệm Python của bạn ở mức nào?",
            "options": [
                "Chưa biết",
                "Viết script cơ bản, cú pháp for/if",
                "Sử dụng OOP, Pandas/Numpy",
                "Viết API (FastAPI/Django/Flask)",
                "Tối ưu hóa performance, AsyncIO",
            ],
            "levels": [0, 1, 2, 3, 4],
        },
        "react": {
            "question": "Bạn thường dùng React như thế nào?",
            "options": [
                "Chưa từng dùng",
                "Chỉnh sửa template có sẵn",
                "Tạo component đơn giản, dùng useState",
                "Quản lý state phức tạp (Redux/Context), Hooks custom",
                "Tối ưu render, Next.js SSR",
            ],
            "levels": [0, 1, 2, 3, 4],
        },
        "machine learning": {
            "question": "Bạn đã làm gì với Machine Learning?",
            "options": [
                "Chỉ nghe nói",
                "Dùng thư viện scikit-learn cơ bản",
                "Huấn luyện model Deep Learning (PyTorch/TF)",
                "Tự tinh chỉnh kiến trúc model, Transfer Learning",
                "Triển khai model lên production (MLOps)",
            ],
            "levels": [0, 1, 2, 3, 4],
        },
        "default": {
            "question": "Bạn đã ứng dụng công nghệ này vào dự án thực tế nào chưa?",
            "options": [
                "Chỉ mới nghe tên",
                "Đã học qua tutorial",
                "Làm bài tập lớn trên lớp",
                "Làm dự án cá nhân hoàn chỉnh",
                "Sử dụng trong dự án công ty/production",
            ],
            "levels": [0, 1, 2, 3, 4],
        },
    }

    quizzes = []
    for skill in declared_skills:
        skill_lower = skill.lower().strip()
        matched = False
        for key, qdata in question_bank.items():
            if key != "default" and key in skill_lower:
                quizzes.append(
                    {
                        "skill": skill,
                        "question": qdata["question"],
                        "options": qdata["options"],
                    }
                )
                matched = True
                break

        if not matched:
            qdata = question_bank["default"]
            quizzes.append(
                {
                    "skill": skill,
                    "question": qdata["question"].replace("công nghệ này", skill),
                    "options": qdata["options"],
                }
            )

    return {"status": "success", "verification_quizzes": quizzes}
