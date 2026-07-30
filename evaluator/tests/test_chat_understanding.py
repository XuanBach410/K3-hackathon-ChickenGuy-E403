from django.test import TestCase
from evaluator.chat_understanding import normalize_text, resolve_topic, parse_chat_team

class ChatUnderstandingTests(TestCase):
    def test_normalize_text(self):
        self.assertEqual(normalize_text("Đề tài AI số 1!"), "etaiaiso1")
        self.assertEqual(normalize_text("Hệ thống quản lý EDU-01"), "hethongquanlyedu01")
        self.assertEqual(normalize_text("   "), "")

    def test_resolve_topic_by_code(self):
        topics = [{"code": "EDU-01", "title": "Test Topic"}, {"code": "FIN-02", "title": "Finance"}]
        # Exact code match
        self.assertEqual(resolve_topic("tôi chọn edu-01", topics)["code"], "EDU-01")
        # Code without dash match is handled differently? Wait, the code inside resolve_topic:
        # if normalize_text(code) in compact_message: ...
        # normalize_text("EDU-01") is "edu01"
        self.assertEqual(resolve_topic("tôi làm edu01 nhé", topics)["code"], "EDU-01")
        
        # No match
        self.assertIsNone(resolve_topic("tôi chọn edu-99", topics))

    def test_resolve_topic_by_title_alias(self):
        topics = [
            {"code": "A-01", "title": "HomeMatch: Hệ thống nhà thông minh"},
            {"code": "A-02", "title": "Fleet Miner"}
        ]
        # First word alias (HomeMatch)
        self.assertEqual(resolve_topic("mình làm homematch được không", topics)["code"], "A-01")
        # Multi-word alias (Fleet Miner)
        self.assertEqual(resolve_topic("đề tài fleet miner nha", topics)["code"], "A-02")
        
    def test_parse_chat_team_no_signal(self):
        members, duration = parse_chat_team("chào buổi sáng", fallback_team=[{"name": "Fallback"}])
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0]["name"], "Chat member 1")
        self.assertIsNone(duration)

    def test_parse_chat_team_signals(self):
        message = "nhóm 3 người, thời gian 2 tháng, biết react cơ bản và python, có làm backend"
        members, duration = parse_chat_team(message)
        self.assertEqual(len(members), 3)
        self.assertEqual(duration, 8)  # 2 months = 8 weeks
        prof = members[0]["proficiency"]
        self.assertEqual(prof.get("React"), 2)
        self.assertEqual(prof.get("Python"), 2)
        self.assertEqual(prof.get("Backend"), 3)

    def test_parse_chat_team_no_ai_knowledge(self):
        message = "nhóm 2 mem làm trong 3 tuần, biết rag và fastapi, nhưng chưa học ai bao giờ"
        members, duration = parse_chat_team(message)
        self.assertEqual(len(members), 2)
        self.assertEqual(duration, 3)
        prof = members[0]["proficiency"]
        self.assertEqual(prof.get("FastAPI"), 3)
        # RAG should be removed because of "chưa học ai"
        self.assertNotIn("RAG", prof)
        
    def test_parse_chat_team_default_duration(self):
        message = "nhóm 1 mem biết frontend cơ bản và langgraph"
        members, duration = parse_chat_team(message)
        self.assertEqual(len(members), 1)
        self.assertIsNone(duration)
        self.assertEqual(members[0]["hours_per_week"], 20) # Default if duration > 4 or None
        self.assertEqual(members[0]["proficiency"]["Frontend"], 2)
        self.assertEqual(members[0]["proficiency"]["LangGraph"], 3)
