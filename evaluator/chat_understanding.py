"""Deterministic chat understanding for topic aliases and lightweight team evidence."""

import re
import unicodedata


def normalize_text(value):
    text = unicodedata.normalize("NFD", str(value).lower())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", text)


def resolve_topic(message, topics):
    """Resolve codes with optional hyphens and common title aliases from catalog data."""
    compact_message = normalize_text(message)
    for topic in topics:
        code = str(topic.get("code", ""))
        if code and normalize_text(code) in compact_message:
            return topic

    for topic in topics:
        title = str(topic.get("title", ""))
        candidates = re.findall(r"[A-Za-z][A-Za-z0-9]+", title)
        aliases = {normalize_text(candidates[0])} if candidates else set()
        # Title fragments provide stable catalog-grounded aliases such as HomeMatch/Fleet Miner.
        aliases.update({normalize_text(" ".join(candidates[:2])), normalize_text(title.split(":")[0])})
        if any(alias and len(alias) >= 5 and alias in compact_message for alias in aliases):
            return topic
    return None


def parse_chat_team(message, fallback_team=None):
    """Extract only explicit team signals; retain selected profile when chat adds no evidence."""
    normalized = message.lower()
    has_profile_signal = any(signal in normalized for signal in (
        "biết", "biet", "cơ bản", "co ban", "chưa học ai", "chua hoc ai", "backend", "frontend",
        "react", "python", "rag", "fastapi", "langgraph", "thời gian", "tuần", "tháng", "mem", "người", "ng",
    ))
    if not has_profile_signal:
        return fallback_team or [], None

    count_match = re.search(r"\b(\d+)\s*(?:người|nguoi|mem|ng)\b", normalized)
    team_size = int(count_match.group(1)) if count_match else 1
    week_match = re.search(r"\b(\d+)\s*tuần\b", normalized)
    month_match = re.search(r"\b(\d+)\s*tháng\b", normalized)
    duration_weeks = int(week_match.group(1)) if week_match else (int(month_match.group(1)) * 4 if month_match else None)

    proficiency = {}
    if "react" in normalized:
        proficiency["React"] = 2 if "cơ bản" in normalized or "co ban" in normalized else 3
    if "python" in normalized:
        proficiency["Python"] = 2 if "cơ bản" in normalized or "co ban" in normalized else 3
    if "backend" in normalized:
        proficiency["Backend"] = 3
    if "frontend" in normalized or "web" in normalized:
        proficiency["Frontend"] = 2 if "cơ bản" in normalized or "co ban" in normalized else 3
    if "rag" in normalized:
        proficiency["RAG"] = 3
    if "fastapi" in normalized:
        proficiency["FastAPI"] = 3
    if "langgraph" in normalized:
        proficiency["LangGraph"] = 3
    if "chưa học ai" in normalized or "chua hoc ai" in normalized or "chưa biết gì về ai" in normalized:
        proficiency = {key: value for key, value in proficiency.items() if key not in {"RAG", "LangGraph"}}

    members = [
        {
            "name": f"Chat member {index + 1}",
            "proficiency": proficiency,
            "skills": ", ".join(f"{skill}:{level}" for skill, level in proficiency.items()),
            "hours_per_week": 15 if duration_weeks and duration_weeks <= 4 else 20,
        }
        for index in range(team_size)
    ]
    return members, duration_weeks
