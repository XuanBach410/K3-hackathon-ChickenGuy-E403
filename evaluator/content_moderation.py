import json
from dataclasses import dataclass

from .llm_provider import LLMProvider


@dataclass
class ModerationDecision:
    action: str
    reason: str
    safe_reply: str | None = None
    source: str = "policy-fallback"


class ContentModerationGate:
    """Reviews a chat request before the advisor can access topic evidence or an LLM."""

    ACTION_ALLOW = "ALLOW"
    ACTION_OUT_OF_SCOPE = "OUT_OF_SCOPE"
    ACTION_NEEDS_CONTEXT = "NEEDS_CONTEXT"
    ACTION_TOPIC_RECOMMENDATION = "TOPIC_RECOMMENDATION"

    SYSTEM_PROMPT = """
You are the content moderation gate for an academic topic-fit advisor.
Return JSON only with this exact shape:
{"action":"ALLOW|OUT_OF_SCOPE|NEEDS_CONTEXT|TOPIC_RECOMMENDATION","reason":"short reason","safe_reply":"optional Vietnamese reply"}

Choose OUT_OF_SCOPE when the user asks the system to produce substantial deliverables for a graded project,
such as complete source code, a thesis/report, answer keys, presentation slides, or a demo video.
Choose NEEDS_CONTEXT when the user asks whether a topic fits, which topic to choose, or which is easiest but
the provided context cannot support a decision.
Choose TOPIC_RECOMMENDATION when the user asks which topic to choose and a team profile is available,
even if no topic code was provided.
Choose ALLOW for grounded questions about a topic's stated requirements, outcomes, risks, skills, or KPIs.
Do not answer the topic question itself. Do not invent requirements. Use Vietnamese for safe_reply.
"""

    @classmethod
    def review(cls, message, has_team, has_topic_reference, provider="gemini", api_key=""):
        facts = {
            "message": message,
            "has_team_profile": has_team,
            "has_topic_reference": has_topic_reference,
        }
        if api_key:
            result = LLMProvider.call_llm(
                provider,
                api_key,
                cls.SYSTEM_PROMPT,
                json.dumps(facts, ensure_ascii=False),
            )
            if isinstance(result, dict) and result.get("action") in {
                cls.ACTION_ALLOW,
                cls.ACTION_OUT_OF_SCOPE,
                cls.ACTION_NEEDS_CONTEXT,
                cls.ACTION_TOPIC_RECOMMENDATION,
            }:
                return ModerationDecision(
                    action=result["action"],
                    reason=str(result.get("reason", "LLM moderation")),
                    safe_reply=str(result.get("safe_reply", "")).strip() or None,
                    source=f"{provider}-moderation",
                )

        return cls._fallback(message, has_team, has_topic_reference)

    @classmethod
    def _fallback(cls, message, has_team, has_topic_reference):
        normalized = message.lower()
        deliverable_terms = (
            "source code", "code hoàn chỉnh", "báo cáo", "luận văn", "đáp án",
            "làm thay", "slide bảo vệ", "video demo", "thi hộ",
        )
        if any(term in normalized for term in deliverable_terms):
            return ModerationDecision(
                action=cls.ACTION_OUT_OF_SCOPE,
                reason="Requested a deliverable outside topic-fit advising.",
                safe_reply="Từ chối. Chatbot chỉ hỗ trợ đánh giá mức độ phù hợp của đề tài, không làm thay hoặc tạo artifact nộp bài.",
            )

        recommendation_intents = ("nên chọn đề tài", "đề tài nào", "gợi ý đề tài", "chọn giúp", "chắc ăn lấy điểm", "né đề nào", "ít code ai nhất", "recommend giúp")
        if any(intent in normalized for intent in recommendation_intents) and not has_topic_reference:
            if has_team:
                return ModerationDecision(
                    action=cls.ACTION_TOPIC_RECOMMENDATION,
                    reason="Team profile is sufficient for MCDA recommendation across the topic catalog.",
                )
            return ModerationDecision(
                action=cls.ACTION_NEEDS_CONTEXT,
                reason="Topic recommendation needs a team profile.",
                safe_reply="Chưa đủ thông tin. Cần biết số thành viên, kỹ năng, thời gian và mục tiêu dự án.",
            )

        fit_intents = ("phù hợp", "có nên", "nên làm", "dễ nhất", "easy hay hard", "khó k", "dc ko", "dc hông", "thế nào")
        if any(intent in normalized for intent in fit_intents):
            if not has_topic_reference:
                return ModerationDecision(
                    action=cls.ACTION_NEEDS_CONTEXT,
                    reason="A fit decision needs a topic reference.",
                    safe_reply="Chưa đủ thông tin. Vui lòng cung cấp tên hoặc mã đề tài, cùng thông tin nhóm.",
                )
            if not has_team:
                return ModerationDecision(
                    action=cls.ACTION_NEEDS_CONTEXT,
                    reason="A fit decision needs team capacity evidence.",
                    safe_reply="Chưa thể kết luận nếu chưa biết năng lực, thời gian và quy mô của nhóm.",
                )

        return ModerationDecision(action=cls.ACTION_ALLOW, reason="Grounded advisor question.")
