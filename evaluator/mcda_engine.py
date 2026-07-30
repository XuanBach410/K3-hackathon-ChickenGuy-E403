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

    # Learning Cost Mapping (hours)
    learning_costs = {
        "python": 30, "react": 40, "pytorch": 50, "docker": 15, "sql": 20, "rag": 35, 
        "fastapi": 25, "nlp": 45, "computer vision": 45, "node": 30, "flutter": 45, 
        "java": 40, "spark": 50, "pandas": 20, "redis": 10, "postgresql": 20, "mongodb": 15, 
        "typescript": 25, "tailwind": 10, "vue": 30, "firebase": 15, "tensorflow": 50, 
        "keras": 20, "scikit-learn": 25, "langchain": 30, "streamlit": 15, 
        "html/css": 20, "javascript": 30, "c++": 50, "ros": 60, "matlab": 30, 
        "opencv": 35, "yolo": 25, "bert": 40, "gpt": 20, "llm": 40, "api": 15, 
        "aws": 40, "gcp": 40, "azure": 40, "linux": 25, "git": 10
    }
    
    # Criticality Heuristic based on domain
    is_ai = "ai" in topic_cat or "machine learning" in topic_cat or "data" in topic_cat
    is_web = "web" in topic_cat or "phần mềm" in topic_cat or "app" in topic_cat
    
    def get_criticality(tech):
        tech_lower = tech.lower()
        if is_ai and tech_lower in ["python", "pytorch", "tensorflow", "rag", "llm", "nlp", "computer vision", "pandas", "opencv", "yolo"]:
            return "Critical"
        if is_web and tech_lower in ["react", "node", "java", "sql", "postgresql", "javascript", "typescript", "fastapi"]:
            return "Critical"
        if tech_lower in ["git", "docker", "linux", "html/css", "tailwind", "redis"]:
            return "Minor"
        return "Major"

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
                missing_techs.append({
                    "tech": tech,
                    "criticality": get_criticality(tech),
                    "cost_hours": learning_costs.get(tech, 20)
                })

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

    # Total Learning Hours & C3 Adaptability (20%)
    total_learning_hours = sum([m.get("cost_hours", 20) for m in missing_techs])
    c3_adaptability = max(100.0 - (total_learning_hours * 0.5), 20.0)

    # C4: Resource & Risk Matrix (20%)
    max_team_limit = int(topic.get("max_team", 5))
    team_size_penalty = 0
    if len(team_members) > max_team_limit:
        team_size_penalty = -20

    critical_missing = sum(1 for m in missing_techs if m.get("criticality") == "Critical")
    skill_risk = "High" if critical_missing > 0 else ("Medium" if len(missing_techs) > 0 else "Low")
    time_risk = "High" if total_learning_hours > (total_hours * 4) else ("Medium" if total_learning_hours > (total_hours * 2) else "Low")
    team_risk = "High" if team_size_penalty < 0 else "Low"
    domain_risk = "High" if domain_mismatch else "Low"
    
    risk_matrix = {
        "skill_risk": skill_risk,
        "time_risk": time_risk,
        "team_risk": team_risk,
        "domain_risk": domain_risk,
        "total_learning_hours": total_learning_hours,
        "critical_missing_count": critical_missing
    }
    
    # Calculate synthetic c4_risk_score for legacy scoring formula
    risk_deductions = {"High": 20, "Medium": 10, "Low": 0}
    c4_risk_score = 100.0 - risk_deductions[skill_risk] - risk_deductions[time_risk] - risk_deductions[domain_risk]
    c4_risk_score = max(20.0, c4_risk_score)

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
    elif total_score >= 50 and len(missing_techs) <= 4:
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
        "riskMatrix": risk_matrix,
        "domainMismatch": domain_mismatch,
        "explanation": explanation
    }
