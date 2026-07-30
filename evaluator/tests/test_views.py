import json

from django.test import TestCase


class ViewTests(TestCase):
    def test_health_endpoint(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["components"]["api"], "ok")

    def test_get_topics_endpoint(self):
        response = self.client.get("/api/topics/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("topics", data)
        self.assertIsInstance(data["topics"], list)

    def test_get_mock_profiles_endpoint(self):
        response = self.client.get("/api/profiles/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("profiles", data)
        self.assertIsInstance(data["profiles"], list)

    def test_get_registered_agent_tools(self):
        response = self.client.get("/api/agent/tools/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("registered_tools", data)
        self.assertIsInstance(data["registered_tools"], list)

    def test_evaluate_preliminary_invalid_json(self):
        response = self.client.post(
            "/api/evaluate/preliminary/",
            data="invalid json format",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["error"]["code"], "invalid_json")

    def test_evaluate_preliminary_missing_team(self):
        response = self.client.post(
            "/api/evaluate/preliminary/",
            data=json.dumps({"selected_codes": ["EDU-01"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_generate_deep_quiz_missing_topic(self):
        response = self.client.post(
            "/api/evaluate/deep-quiz/",
            data=json.dumps({"team_members": [{"skills": "Python:3"}]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["error"]["code"], "missing_topic_code")

    def test_generate_deep_quiz_invalid_topic(self):
        response = self.client.post(
            "/api/evaluate/deep-quiz/",
            data=json.dumps(
                {
                    "topic_code": "INVALID-TOPIC",
                    "team_members": [{"skills": "Python:3"}],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["error"]["code"], "topic_not_found")

    def test_generate_deep_quiz_valid(self):
        response = self.client.post(
            "/api/evaluate/deep-quiz/",
            data=json.dumps(
                {"topic_code": "EDU-01", "team_members": [{"skills": "Python:3"}]}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("questions", data)
        self.assertEqual(data["topic_code"], "EDU-01")

    def test_evaluate_final_missing_topic(self):
        response = self.client.post(
            "/api/evaluate/final/",
            data=json.dumps({"team_members": [{"skills": "Python:3"}]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["error"]["code"], "missing_topic_code")

    def test_evaluate_final_fallback(self):
        response = self.client.post(
            "/api/evaluate/final/",
            data=json.dumps(
                {
                    "topic_code": "EDU-01",
                    "team_members": [{"skills": "Python:3"}],
                    "quiz_answers": {"1": "Yes"},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("evaluation", data)
        self.assertIn("fitState", data["evaluation"])

    def test_advisor_chat_missing_message(self):
        response = self.client.post(
            "/api/advisor/chat/",
            data=json.dumps({"team_members": [{"skills": "Python:3"}]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_advisor_chat_valid(self):
        response = self.client.post(
            "/api/advisor/chat/",
            data=json.dumps(
                {
                    "message": "Cho tôi phân tích EDU-01",
                    "team_members": [{"skills": "Python:3"}],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("reply", data)

    def test_evaluate_what_if_invalid(self):
        response = self.client.post(
            "/api/evaluate/what-if/",
            data=json.dumps(
                {"topic_code": "EDU-01", "team_members": [{"skills": "Python:3"}]}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_json_payload(self):
        response = self.client.post("/api/advisor/chat/", data="{invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_json")

    def test_execute_tool_missing_name(self):
        response = self.client.post("/api/agent/tools/execute/", data="{}", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_execute_tool_invalid_method(self):
        response = self.client.get("/api/agent/tools/execute/")
        self.assertEqual(response.status_code, 405)
        
    def test_verify_declared_skills_invalid(self):
        response = self.client.post("/api/evaluate/verify-skills/", data='{"declared_skills": "not_a_list"}', content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_serve_index(self):
        response = self.client.get("/")
        # Depending on if build exists, could be 200 or 404
        self.assertIn(response.status_code, [200, 404])
