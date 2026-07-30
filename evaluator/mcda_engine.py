import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAXONOMY_PATH = os.path.join(BASE_DIR, "skill_taxonomy.json")

LEARNING_COSTS = {
    "python": 30, "react": 40, "pytorch": 50, "docker": 15, "sql": 20, "rag": 35,
    "fastapi": 25, "nlp": 45, "computer vision": 45, "nodejs": 30, "flutter": 45,
    "java": 40, "spark": 50, "pandas": 20, "redis": 10, "postgresql": 20, "mongodb": 15,
    "typescript": 25, "tailwind": 10, "vue": 30, "firebase": 15, "tensorflow": 50,
    "keras": 20, "scikit-learn": 25, "langchain": 30, "streamlit": 15,
    "html/css": 20, "javascript": 30, "c++": 50, "ros": 60, "matlab": 30,
    "opencv": 35, "yolo": 25, "bert": 40, "gpt": 20, "llm": 40, "rest api": 15,
    "aws": 40, "gcp": 40, "azure": 40, "linux": 25, "git": 10, "qdrant": 20,
    "pgvector": 20, "langgraph": 30, "kubernetes": 45, "celery": 20, "whisper": 25,
    "ragas": 20, "next.js": 30, "django": 30, "kafka": 35, "kotlin": 40,
    "frontend": 25, "backend": 30, "mobile": 40, "devops/cloud": 40,
    "data analysis": 25, "machine learning": 45, "deep learning": 50,
    "product management": 20, "project management": 20, "ui/ux design": 25,
    "prompt engineering": 15,
}

TRACKED_TECHS = tuple(LEARNING_COSTS)

TECH_ALIASES = {
    "nodejs": ["nodejs", "node.js", "node js"],
    "next.js": ["next.js", "nextjs", "next js"],
    "rest api": ["rest api", "restful api"],
    "postgresql": ["postgresql", "postgres"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "computer vision": ["computer vision", "thị giác máy tính"],
    "machine learning": ["machine learning", "học máy"],
    "html/css": ["html/css", "html css"],
    "c++": ["c++", "cpp"],
}

DOMAIN_SIGNALS = {
    "education": ["giáo dục", "đào tạo", "học tập", "sinh viên", "giảng viên", "education", "learning"],
    "health": ["y tế", "sức khỏe", "health", "medical", "clinical"],
    "agriculture": ["nông nghiệp", "agriculture", "farm"],
    "government": ["chính phủ", "hành chính", "public sector", "government"],
    "finance": ["tài chính", "ngân hàng", "finance", "banking"],
    "robotics": ["robot", "ros", "xe tự hành", "robotics"],
}


def normalize_skill_name(value):
    return re.sub(r"\s+", " ", str(value).strip().lower())


def text_contains_term(text, term):
    aliases = TECH_ALIASES.get(term, [term])
    return any(re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text) for alias in aliases)


def extract_domain_tags(text):
    normalized = normalize_skill_name(text)
    return {
        domain
        for domain, signals in DOMAIN_SIGNALS.items()
        if any(signal in normalized for signal in signals)
    }

def get_taxonomy():
    if os.path.exists(TAXONOMY_PATH):
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def extract_latent_skills(member):
    """
    Parse latent skills from member introduction and proficiency dictionary.
    """
    intro = member.get("introduction", "")
    proficiency = dict(member.get("proficiency", {}) or {})

    # The React team editor serializes skills as "Python:3, React:4".
    # Accept that API shape alongside the structured proficiency object.
    serialized_skills = member.get("skills", "")
    if isinstance(serialized_skills, str):
        for entry in serialized_skills.split(","):
            skill, separator, level = entry.strip().partition(":")
            if not skill:
                continue
            try:
                proficiency[skill] = max(proficiency.get(skill, 0), int(level.strip()) if separator else 1)
            except ValueError:
                proficiency[skill] = max(proficiency.get(skill, 0), 1)

    latent_skills = dict(proficiency)

    # Keywords heuristic parsing for latent skills
    intro_lower = intro.lower()
    
    keyword_map = {
        "rag": ("RAG", 4),
        "chatbot": ("Chatbot", 4),
        "di động": ("Mobile", 3),
        "mobile": ("Mobile", 3),
        "học máy": ("Machine Learning", 3),
        "dữ liệu": ("Data Analysis", 3),
        "quản trị": ("Project Management", 4),
        "chính phủ": ("Government Tech", 3),
        "thiết bị": ("IoT/Hardware", 3),
        "y tế": ("HealthTech", 3),
    }

    for kw, (skill, lvl) in keyword_map.items():
        if kw in intro_lower and skill not in latent_skills:
            latent_skills[skill] = lvl

    return latent_skills

def calculate_mcda_score(team_members, topic):
    """
    Core MCDA Matching Algorithm based on criteria.md:
    C1: Skill Compatibility (35%)
    C2: Domain & Problem Fit (25%)
    C3: Learning Curve & Adaptability (20%)
    C4: Resource & Execution Risk (20%)
    """
    taxonomy = {
        normalize_skill_name(category): {normalize_skill_name(skill) for skill in skills}
        for category, skills in get_taxonomy().items()
    }

    # Aggregate Team Skills
    team_skill_map = {}
    team_domains = set()
    total_hours = 0
    max_exp = 0

    for member in team_members:
        skills = extract_latent_skills(member)
        try:
            total_hours += max(0, int(member.get("hours_per_week", 20)))
            max_exp = max(max_exp, max(0, int(member.get("years_of_experience", 1))))
        except (TypeError, ValueError):
            total_hours += 20

        member_domain_text = " ".join([
            *member.get("fields_of_interest", []),
            str(member.get("current_industry", "")),
            str(member.get("introduction", "")),
        ])
        team_domains.update(extract_domain_tags(member_domain_text))

        for skill, level in skills.items():
            skill_key = normalize_skill_name(skill)
            try:
                normalized_level = max(0, min(5, int(level)))
            except (TypeError, ValueError):
                normalized_level = 1
            team_skill_map[skill_key] = max(team_skill_map.get(skill_key, 0), normalized_level)

    # Topic Requirements Text
    req_text = normalize_skill_name(
        f"{topic.get('tech_stack', '')} {topic.get('requirements', '')} {topic.get('description', '')}"
    )
    topic_cat = normalize_skill_name(topic.get("category", ""))
    topic_domains = extract_domain_tags(f"{topic_cat} {req_text}")
    
    # Criticality Heuristic based on domain
    is_ai = "ai" in topic_cat or "machine learning" in topic_cat or "data" in topic_cat
    is_web = "web" in topic_cat or "phần mềm" in topic_cat or "app" in topic_cat
    
    def get_criticality(tech):
        if is_ai and tech in ["python", "pytorch", "tensorflow", "rag", "llm", "nlp", "computer vision", "pandas", "opencv", "yolo", "qdrant", "pgvector", "langgraph"]:
            return "Critical"
        if is_web and tech in ["react", "next.js", "nodejs", "java", "sql", "postgresql", "javascript", "typescript", "fastapi", "django"]:
            return "Critical"
        if tech in ["git", "docker", "linux", "html/css", "tailwind", "redis"]:
            return "Minor"
        return "Major"

    # C1: Skill Compatibility (35%)
    matched_techs = []
    missing_techs = []
    skill_sum = 0
    required_techs = [tech for tech in TRACKED_TECHS if text_contains_term(req_text, tech)]

    for tech in required_techs:
        user_lvl = 0
        evidence_skill = None
        for team_skill, team_level in team_skill_map.items():
            is_direct_match = team_skill == tech or text_contains_term(team_skill, tech)
            is_taxonomy_match = team_skill in taxonomy and tech in taxonomy[team_skill]
            if (is_direct_match or is_taxonomy_match) and team_level > user_lvl:
                user_lvl = team_level
                evidence_skill = team_skill

        if user_lvl > 0:
            if user_lvl >= 3:
                matched_techs.append({"tech": tech, "level": user_lvl, "evidence_skill": evidence_skill})
                skill_sum += min(user_lvl / 5.0, 1.0)
            else:
                matched_techs.append({"tech": tech, "level": user_lvl, "evidence_skill": evidence_skill})
                skill_sum += 0.4
        else:
            missing_techs.append({
                "tech": tech,
                "criticality": get_criticality(tech),
                "cost_hours": LEARNING_COSTS[tech],
            })

    c1_skill_score = (skill_sum / len(required_techs) * 100) if required_techs else 65.0
    c1_skill_score = min(100.0, c1_skill_score)

    # C2: Domain Fit (25%)
    c2_domain_score = 70.0
    domain_mismatch = False

    # Mismatch Detection (e.g. Web/NLP team choosing Robotics)
    is_robotics_topic = any(text_contains_term(req_text, tech) for tech in ["ros", "c++"])
    is_cv_topic = any(text_contains_term(req_text, tech) for tech in ["computer vision", "opencv", "yolo"])
    is_nlp_topic = any(text_contains_term(req_text, tech) for tech in ["nlp", "bert", "llm", "rag"])

    has_robotics = any("ros" in k or "c++" in k for k in team_skill_map)
    has_cv = any("opencv" in k or "computer vision" in k for k in team_skill_map)
    has_nlp = any("nlp" in k or "rag" in k or "llm" in k for k in team_skill_map)

    if (is_robotics_topic and not has_robotics) or (is_cv_topic and not has_cv and has_nlp) or (is_nlp_topic and not has_nlp and has_cv):
        domain_mismatch = True
        c2_domain_score = 30.0
    elif team_domains & topic_domains:
        c2_domain_score = 95.0

    # Total Learning Hours & C3 Adaptability (20%)
    total_learning_hours = sum([m.get("cost_hours", 20) for m in missing_techs])
    two_week_capacity = max(total_hours * 2, 1)
    learning_load_ratio = total_learning_hours / two_week_capacity
    c3_adaptability = max(20.0, 100.0 - min(80.0, learning_load_ratio * 60.0))

    # C4: Resource & Risk Matrix (20%)
    max_team_limit = int(topic.get("max_team", 5))

    critical_missing = sum(1 for m in missing_techs if m.get("criticality") == "Critical")
    skill_risk = "High" if critical_missing > 0 else ("Medium" if len(missing_techs) > 0 else "Low")
    time_risk = "High" if total_learning_hours > two_week_capacity else ("Medium" if total_learning_hours > total_hours else "Low")
    team_risk = "High" if len(team_members) > max_team_limit else "Low"
    domain_risk = "High" if domain_mismatch else "Low"
    
    risk_matrix = {
        "skill_risk": skill_risk,
        "time_risk": time_risk,
        "team_risk": team_risk,
        "domain_risk": domain_risk,
        "total_learning_hours": total_learning_hours,
        "critical_missing_count": critical_missing,
        "weekly_capacity_hours": total_hours,
        "two_week_learning_capacity_hours": two_week_capacity,
        "team_size": len(team_members),
        "max_team_size": max_team_limit,
    }

    risk_deductions = {"High": 25, "Medium": 12, "Low": 0}
    c4_risk_score = max(0.0, 100.0 - sum(
        risk_deductions[level]
        for level in [skill_risk, time_risk, team_risk, domain_risk]
    ))

    # Total Score
    total_score = round(
        (c1_skill_score * 0.35) + 
        (c2_domain_score * 0.25) + 
        (c3_adaptability * 0.20) + 
        (c4_risk_score * 0.20)
    )
    total_score = max(10, min(98, total_score))

    # Fit State Classification
    if team_risk == "High":
        fit_state = "OVER_CAPACITY"
        verdict_label = "Over Capacity / Team Constraint"
    elif total_score >= 75 and not domain_mismatch and critical_missing == 0:
        fit_state = "PERFECT_FIT"
        verdict_label = "Perfect / High Fit"
    elif total_score >= 50 and len(missing_techs) <= 4 and time_risk != "High":
        fit_state = "ABLE_TO_LEARN"
        verdict_label = "Able to Learn (Conditionally Feasible)"
    else:
        fit_state = "NOT_ABLE_TO_LEARN"
        verdict_label = "High Risk / Not Able to Learn"

    # Explanation Generation
    explanation = []
    if matched_techs:
        explanation.append(f"Nhóm đáp ứng {len(matched_techs)} kỹ năng yêu cầu: {', '.join([m['tech'] for m in matched_techs[:4]])}.")
    if missing_techs:
        missing_names = [m['tech'] for m in missing_techs]
        explanation.append(f"Còn thiếu {len(missing_techs)} kỹ năng: {', '.join(missing_names[:4])}. Ước tính cần {total_learning_hours} giờ tự học.")
        if critical_missing > 0:
            explanation.append(f"CẢNH BÁO: Thiếu {critical_missing} kỹ năng cốt lõi (Critical) ảnh hưởng trực tiếp đến khả năng thành công của dự án.")
    if domain_mismatch:
        explanation.append("Cảnh báo lệch Domain: Chuyên môn của nhóm khác với lĩnh vực cốt lõi của đề tài này.")
    if team_risk == "High":
        explanation.append(f"Quy mô nhóm ({len(team_members)} người) vượt quá giới hạn đề tài ({max_team_limit} người).")

    score_breakdown = {
        "skill": {"label": "Skill compatibility", "score": round(c1_skill_score), "weight": 35, "contribution": round(c1_skill_score * 0.35, 1)},
        "domain": {"label": "Domain & problem fit", "score": round(c2_domain_score), "weight": 25, "contribution": round(c2_domain_score * 0.25, 1)},
        "adaptability": {"label": "Learning adaptability", "score": round(c3_adaptability), "weight": 20, "contribution": round(c3_adaptability * 0.20, 1)},
        "execution": {"label": "Execution readiness", "score": round(c4_risk_score), "weight": 20, "contribution": round(c4_risk_score * 0.20, 1)},
    }

    return {
        "finalScore": total_score,
        "skillScore": round(c1_skill_score),
        "domainScore": round(c2_domain_score),
        "feasibilityScore": round(c3_adaptability),
        "riskScore": round(c4_risk_score),
        "scoreBreakdown": score_breakdown,
        "fitState": fit_state,
        "verdictLabel": verdict_label,
        "matchedTechs": matched_techs,
        "missingTechs": missing_techs,
        "riskMatrix": risk_matrix,
        "domainMismatch": domain_mismatch,
        "explanation": explanation,
        "evidence": {
            "requiredTechs": required_techs,
            "teamDomains": sorted(team_domains),
            "topicDomains": sorted(topic_domains),
            "maxExperienceYears": max_exp,
            "method": "Rule-based MCDA 35/25/20/20",
        },
    }
