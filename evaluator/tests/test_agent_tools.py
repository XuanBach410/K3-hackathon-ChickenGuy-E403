import json
import unittest
from evaluator.agent_tools import AgentToolRegistry

class TestAgentToolRegistry(unittest.TestCase):
    def test_get_tool_schemas(self):
        schemas = AgentToolRegistry.get_tool_schemas()
        self.assertTrue(len(schemas) > 0)
        names = [s["name"] for s in schemas]
        self.assertIn("evaluate_preliminary_fit", names)
        self.assertIn("generate_topic_deep_quiz", names)
        self.assertIn("analyze_topic_outcomes", names)
        self.assertIn("verify_declared_skills", names)

    def test_execute_unregistered_tool(self):
        result = AgentToolRegistry.execute("non_existent_tool", {})
        self.assertIn("error", result)

    def test_execute_tool_failure(self):
        # Missing required parameter should cause exception and caught by execute
        result = AgentToolRegistry.execute("evaluate_preliminary_fit", {})
        self.assertIn("error", result)

class TestAgentTools(unittest.TestCase):
    def setUp(self):
        self.dummy_topic = {
            "code": "TEST-01",
            "title": "Test Topic",
            "requirements": "Cần biết Python, Docker, và làm RAG.",
            "tech_stack": "Python, Docker, VectorDB",
            "description": "Dự án yêu cầu làm một hệ thống RAG cơ bản. Cần tuân thủ ràng buộc HITL."
        }
        self.dummy_team = [
            {
                "name": "User 1",
                "proficiency": {"Python": 3, "Docker": 1},
                "skills": "Python:3, Docker:1",
                "hours_per_week": 20
            }
        ]

    def test_parse_member_profile_tool(self):
        res = AgentToolRegistry.execute("parse_member_profile", {"profile_text": "Tôi biết code python cơ bản."})
        self.assertEqual(res.get("status"), "success")
        self.assertIn("latent_skills", res)

    def test_evaluate_preliminary_fit_tool(self):
        res = AgentToolRegistry.execute("evaluate_preliminary_fit", {
            "team_members": self.dummy_team,
            "topic": self.dummy_topic
        })
        self.assertEqual(res.get("status"), "success")
        self.assertIn("mcda_result", res)
        self.assertIn("finalScore", res["mcda_result"])

    def test_analyze_topic_outcomes_tool(self):
        res = AgentToolRegistry.execute("analyze_topic_outcomes", {"topic": self.dummy_topic})
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("topic_code"), "TEST-01")
        self.assertIn("outcomes", res)
        self.assertIn("constraints", res)
        self.assertTrue(any("hitl" in c.lower() for c in res["constraints"]))

    def test_generate_topic_deep_quiz_tool(self):
        res = AgentToolRegistry.execute("generate_topic_deep_quiz", {
            "topic_code": "TEST-01",
            "topic_title": "Test Topic",
            "missing_skills": ["VectorDB"],
            "domain_mismatch": True,
            "outcomes": ["RAG cơ bản"],
            "kpis": ["độ chính xác > 80%"],
            "constraints": ["HITL"]
        })
        self.assertEqual(res.get("status"), "success")
        questions = res.get("questions")
        self.assertEqual(len(questions), 5) # 4 default + 1 domain mismatch
        self.assertTrue(any("TEST-01" in q["question"] for q in questions))

    def test_verify_declared_skills_tool(self):
        res = AgentToolRegistry.execute("verify_declared_skills", {
            "declared_skills": ["Python", "Machine Learning", "UnknownTech"]
        })
        self.assertEqual(res.get("status"), "success")
        quizzes = res.get("verification_quizzes")
        self.assertEqual(len(quizzes), 3)
        skills_tested = [q["skill"] for q in quizzes]
        self.assertIn("Python", skills_tested)
        self.assertIn("UnknownTech", skills_tested)

if __name__ == '__main__':
    unittest.main()
