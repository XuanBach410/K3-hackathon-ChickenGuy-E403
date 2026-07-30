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
    description="Sinh bộ câu hỏi trừu tượng và chuyên sâu (thang điểm, trắc nghiệm, tự luận) thiết kế riêng cho MỘT đề tài cụ thể dựa trên skill gap.",
    parameters={
        "type": "object",
        "properties": {
            "topic_code": {"type": "string", "description": "Mã đề tài"},
            "topic_title": {"type": "string", "description": "Tên đề tài"},
            "missing_skills": {"type": "array", "description": "Danh sách kỹ năng thiếu"},
            "domain_mismatch": {"type": "boolean", "description": "Có bị lệch domain không"}
        },
        "required": ["topic_code"]
    }
)
def generate_topic_deep_quiz_tool(topic_code, topic_title="", missing_skills=None, domain_mismatch=False):
    missing_str = ", ".join(missing_skills) if missing_skills else "công nghệ nâng cao"
    
    questions = [
        {
            "id": 1,
            "question": f"Nhóm bạn hình dung như thế nào về kết quả đầu ra thực tế của đề tài [{topic_code}] '{topic_title}'?",
            "type": "scale",
            "options": ["1. Chưa hình dung", "2. Mơ hồ", "3. Khá rõ", "4. Đã có kiến trúc", "5. Rất rõ ràng"]
        },
        {
            "id": 2,
            "question": f"Đối với các kỹ năng chưa có ({missing_str}), nhóm có kế hoạch bù đắp thế nào trong 6 tuần?",
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
            "question": f"[Tự Luận Chuyên Sâu] Mô tả ngắn gọn hướng tiếp cận kỹ thuật cốt lõi nhóm sẽ dùng để giải quyết bài toán [{topic_code}]?",
            "type": "text",
            "placeholder": f"Nhập câu trả lời tự luận (ví dụ: Dùng RAG kết hợp Vector DB để xây dựng Agent cá nhân hóa cho {topic_code}...)"
        }
    ]

    if domain_mismatch:
        questions.append({
            "id": 5,
            "question": f"[Lệch Domain] Đề tài [{topic_code}] thuộc lĩnh vực mới so với chuyên môn nhóm. Lý do và động lực chính nhóm vẫn muốn chọn là gì?",
            "type": "text",
            "placeholder": "Nhập lý do nhóm sẵn sàng vượt rào cản domain..."
        })

    return {"status": "success", "topic_code": topic_code, "questions": questions}

@AgentToolRegistry.register(
    name="verify_declared_skills",
    description="Xác minh trình độ thực tế của các kỹ năng được khai báo bằng các câu hỏi trắc nghiệm chuyên môn.",
    parameters={
        "type": "object",
        "properties": {
            "declared_skills": {
                "type": "array", 
                "items": {"type": "string"},
                "description": "Danh sách các kỹ năng nhóm tự khai báo (VD: ['Docker', 'Python'])"
            }
        },
        "required": ["declared_skills"]
    }
)
def verify_declared_skills_tool(declared_skills):
    question_bank = {
        "docker": {
            "question": "Bạn đã từng thực hiện thao tác nào với Docker?",
            "options": ["Chưa từng dùng", "Pull và run image có sẵn", "Tự viết Dockerfile cơ bản", "Dùng Docker Compose chạy multi-container", "Triển khai Kubernetes/Swarm"],
            "levels": [0, 1, 2, 3, 4]
        },
        "python": {
            "question": "Kinh nghiệm Python của bạn ở mức nào?",
            "options": ["Chưa biết", "Viết script cơ bản, cú pháp for/if", "Sử dụng OOP, Pandas/Numpy", "Viết API (FastAPI/Django/Flask)", "Tối ưu hóa performance, AsyncIO"],
            "levels": [0, 1, 2, 3, 4]
        },
        "react": {
            "question": "Bạn thường dùng React như thế nào?",
            "options": ["Chưa từng dùng", "Chỉnh sửa template có sẵn", "Tạo component đơn giản, dùng useState", "Quản lý state phức tạp (Redux/Context), Hooks custom", "Tối ưu render, Next.js SSR"],
            "levels": [0, 1, 2, 3, 4]
        },
        "machine learning": {
            "question": "Bạn đã làm gì với Machine Learning?",
            "options": ["Chỉ nghe nói", "Dùng thư viện scikit-learn cơ bản", "Huấn luyện model Deep Learning (PyTorch/TF)", "Tự tinh chỉnh kiến trúc model, Transfer Learning", "Triển khai model lên production (MLOps)"],
            "levels": [0, 1, 2, 3, 4]
        },
        "default": {
            "question": "Bạn đã ứng dụng công nghệ này vào dự án thực tế nào chưa?",
            "options": ["Chỉ mới nghe tên", "Đã học qua tutorial", "Làm bài tập lớn trên lớp", "Làm dự án cá nhân hoàn chỉnh", "Sử dụng trong dự án công ty/production"],
            "levels": [0, 1, 2, 3, 4]
        }
    }
    
    quizzes = []
    for skill in declared_skills:
        skill_lower = skill.lower().strip()
        matched = False
        for key, qdata in question_bank.items():
            if key != "default" and key in skill_lower:
                quizzes.append({
                    "skill": skill,
                    "question": qdata["question"],
                    "options": qdata["options"]
                })
                matched = True
                break
        
        if not matched:
            qdata = question_bank["default"]
            quizzes.append({
                "skill": skill,
                "question": qdata["question"].replace("công nghệ này", skill),
                "options": qdata["options"]
            })
            
    return {
        "status": "success",
        "verification_quizzes": quizzes
    }

