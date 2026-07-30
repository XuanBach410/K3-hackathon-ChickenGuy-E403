import json
import os
import re

TAXONOMY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "skill_taxonomy.json")

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
    proficiency = member.get("proficiency", {}) or {}
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
    taxonomy = get_taxonomy()

    # Aggregate Team Skills
    team_skill_map = {}
    team_domains = set()
    total_hours = 0
    max_exp = 0

    for m in team_members:
        skills = extract_latent_skills(m)
        total_hours += m.get("hours_per_week", 20)
        max_exp = max(max_exp, m.get("years_of_experience", 1))
        
        for d in m.get("fields_of_interest", []):
            team_domains.add(d.lower())

        for sk, lvl in skills.items():
            sk_key = sk.lower()
            team_skill_map[sk_key] = Math_max = max(team_skill_map.get(sk_key, 0), int(lvl))

    # Topic Requirements Text
    req_text = f"{topic.get('tech_stack', '')} {topic.get('requirements', '')} {topic.get('description', '')}".lower()
    topic_cat = topic.get("category", "").lower()

    # C1: Skill Compatibility (35%)
    common_techs = ["python", "react", "pytorch", "docker", "sql", "rag", "fastapi", "nlp", "computer vision", 
                    "node", "flutter", "java", "spark", "pandas", "redis", "postgresql", "mongodb", "typescript", 
                    "tailwind", "vue", "firebase", "tensorflow", "keras", "scikit-learn", "langchain", "streamlit", 
                    "html/css", "javascript", "c++", "ros", "matlab", "opencv", "yolo", "bert", "gpt", "llm", "api", 
                    "aws", "gcp", "azure", "linux", "git", "frontend", "backend", "mobile", "devops/cloud", 
                    "data analysis", "machine learning", "product management", "project management", "ui/ux design"]

    matched_techs = []
    missing_techs = []
    skill_sum = 0
    tech_count = 0

    for tech in common_techs:
        if tech in req_text:
            tech_count += 1
            user_lvl = 0
            # Check direct or taxonomy match
            for t_sk, t_lvl in team_skill_map.items():
                if t_sk == tech or (t_sk in taxonomy and tech in taxonomy[t_sk]):
                    user_lvl = max(user_lvl, t_lvl)
            
            if user_lvl >= 3:
                matched_techs.append({"tech": tech, "level": user_lvl})
                skill_sum += min(user_lvl / 5.0, 1.0)
            elif user_lvl > 0:
                matched_techs.append({"tech": tech, "level": user_lvl})
                skill_sum += 0.4
            else:
                missing_techs.append(tech)

    c1_skill_score = (skill_sum / tech_count * 100) if tech_count > 0 else 65.0
    c1_skill_score = min(100.0, c1_skill_score)

    # C2: Domain Fit (25%)
    c2_domain_score = 70.0
    domain_mismatch = False

    # Mismatch Detection (e.g. Web/NLP team choosing Robotics)
    is_robotics_topic = "robot" in req_text or "ros" in req_text or "xe tự hành" in req_text
    is_cv_topic = "computer vision" in req_text or "opencv" in req_text or "yolo" in req_text
    is_nlp_topic = "nlp" in req_text or "bert" in req_text or "llm" in req_text or "rag" in req_text

    has_robotics = any("ros" in k or "c++" in k for k in team_skill_map)
    has_cv = any("opencv" in k or "computer vision" in k for k in team_skill_map)
    has_nlp = any("nlp" in k or "rag" in k or "llm" in k for k in team_skill_map)

    if (is_robotics_topic and not has_robotics) or (is_cv_topic and not has_cv and has_nlp) or (is_nlp_topic and not has_nlp and has_cv):
        domain_mismatch = True
        c2_domain_score = 30.0
    else:
        for dom in team_domains:
            if dom in topic_cat:
                c2_domain_score = 95.0
                break

    # C3: Adaptability (20%)
    c3_adaptability = max(100.0 - (len(missing_techs) * 15.0), 20.0)

    # C4: Resource & Risk (20%)
    c4_risk_score = 85.0
    max_team_limit = int(topic.get("max_team", 5))
    team_size_penalty = 0

    if len(team_members) > max_team_limit:
        team_size_penalty = -20
        c4_risk_score -= 30.0

    # Total Score
    total_score = round(
        (c1_skill_score * 0.35) + 
        (c2_domain_score * 0.25) + 
        (c3_adaptability * 0.20) + 
        (c4_risk_score * 0.20) + 
        team_size_penalty
    )
    total_score = max(10, min(98, total_score))

    # Fit State Classification
    if total_score >= 75 and not domain_mismatch:
        fit_state = "PERFECT_FIT"
        verdict_label = "Perfect / High Fit"
    elif total_score >= 50 and len(missing_techs) <= 3:
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
        explanation.append(f"Còn thiếu {len(missing_techs)} kỹ năng: {', '.join(missing_techs[:4])}. Ước tính cần {len(missing_techs)*3}-{len(missing_techs)*5} ngày tự học.")
    if domain_mismatch:
        explanation.append("Cảnh báo lệch Domain: Chuyên môn của nhóm khác với lĩnh vực cốt lõi của đề tài này.")
    if team_size_penalty:
        explanation.append(f"Quy mô nhóm ({len(team_members)} người) vượt quá giới hạn đề tài ({max_team_limit} người).")

    return {
        "finalScore": total_score,
        "skillScore": round(c1_skill_score),
        "domainScore": round(c2_domain_score),
        "feasibilityScore": round(c3_adaptability),
        "riskScore": round(c4_risk_score),
        "fitState": fit_state,
        "verdictLabel": verdict_label,
        "matchedTechs": matched_techs,
        "missingTechs": missing_techs,
        "domainMismatch": domain_mismatch,
        "explanation": explanation
    }
