import json
import os

from django.test import TestCase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class EvalQuestionsIntegrationTests(TestCase):
    def setUp(self):
        with open(
            os.path.join(BASE_DIR, "eval", "test_questions.json"), "r", encoding="utf-8"
        ) as f:
            self.questions = json.load(f)

    def test_questions_file_loaded(self):
        self.assertTrue(len(self.questions) >= 20)

    def test_health_endpoint(self):
        res = self.client.get("/api/health/")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("status"), "ok")

    # Skeleton: each question can be used manually or extended to call specific endpoints
    def test_sample_question_exec(self):
        q = next(question for question in self.questions if "id" in question)
        self.assertIn("input", q)
        self.assertIn("expected_response", q)

    def test_missing_topic_code_has_structured_error(self):
        response = self.client.post(
            "/api/evaluate/final/",
            data=json.dumps(
                {"team_members": [{"skills": "Python:3"}], "quiz_answers": {}}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "missing_topic_code")

    def test_irrelevant_what_if_has_no_silent_score_change(self):
        response = self.client.post(
            "/api/evaluate/what-if/",
            data=json.dumps(
                {
                    "topic_code": "EDU-01",
                    "team_members": [{"skills": "Python:3"}],
                    "target_skill": "PyTorch",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["what_if"])
        self.assertEqual(response.json()["score_improvement"], 0)
        self.assertIn("note", response.json())

    def test_advisor_chat_limits_context_and_generates_grounded_questions(self):
        response = self.client.post(
            "/api/advisor/chat/",
            data=json.dumps(
                {
                    "message": "Phân tích outcome và kỹ năng thiếu",
                    "topic_code": "EDU-01",
                    "team_members": [{"skills": "Python:3", "hours_per_week": 20}],
                    "history": [
                        {
                            "role": "user" if index % 2 == 0 else "assistant",
                            "content": f"message {index}",
                        }
                        for index in range(15)
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["context_window_size"], 10)
        self.assertEqual(body["context_limit"], 10)
        self.assertTrue(body["topic_context"]["outcomes"])
        self.assertTrue(body["suggested_questions"])
        self.assertEqual(body["topic_context"]["source"], "topics_data.json")

    def test_advisor_chat_topic_mentioned_in_text_overrides_stale_context(self):
        response = self.client.post(
            "/api/advisor/chat/",
            data=json.dumps(
                {
                    "message": "Đối với đề tài EDU-01 có cần LangChain không?",
                    "topic_code": "EDU-05",
                    "team_members": [{"skills": "Python:3"}],
                    "history": [
                        {"role": "assistant", "content": "Đang phân tích EDU-05"}
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["resolved_topic_code"], "EDU-01")
        self.assertEqual(body["topic_context"]["topic_code"], "EDU-01")
        self.assertEqual(body["decision_source"], "evidence-guard")
        self.assertNotIn("phân tích EDU-05", body["reply"])

    def test_advisor_anti_hallucination_cases(self):
        cases = [
            (
                "Đề tài EDU-01 có bắt buộc phải dùng LangChain không?",
                "EDU-01",
                "Không đủ căn cứ để khẳng định. Mô tả đề tài chỉ nêu LangGraph và các công nghệ gợi ý, không quy định bắt buộc dùng LangChain.",
            ),
            (
                "Đề tài EDU-04 yêu cầu triển khai trên AWS đúng không?",
                "EDU-04",
                "Không. Mô tả không quy định phải triển khai trên AWS mà chỉ nêu triển khai Docker + Cloud.",
            ),
            (
                "EDU-03 yêu cầu camera để nhận diện hành động sinh viên đúng không?",
                "EDU-03",
                "Không đủ thông tin. Mô tả chỉ đề cập ghi chú quan sát, transcript và checklist, không bắt buộc dùng camera.",
            ),
            (
                "HomeMatch AI Agent yêu cầu PostgreSQL phiên bản 17 phải không?",
                None,
                "Không đủ căn cứ. Mô tả đề tài không quy định phiên bản PostgreSQL.",
            ),
            (
                "ContractGuard AI Agent phải chạy trên GPU RTX 4090 đúng không?",
                None,
                "Không đủ thông tin. Mô tả đề tài không đề cập yêu cầu phần cứng.",
            ),
        ]
        for message, topic_code, expected in cases:
            with self.subTest(message=message):
                response = self.client.post(
                    "/api/advisor/chat/",
                    data=json.dumps(
                        {
                            "message": message,
                            "topic_code": topic_code,
                            "team_members": [{"skills": "Python:3"}],
                        }
                    ),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["reply"], expected)

    def test_advisor_asks_for_missing_context(self):
        cases = [
            ("Đề tài này có phù hợp không?", None),
            ("Nhóm em nên chọn đề tài nào?", None),
            ("EDU-02 có nên làm không?", "EDU-02"),
            ("Em có 2 người, đề tài nào phù hợp?", None),
            ("Đề tài AI nào dễ nhất?", None),
        ]
        for message, topic_code in cases:
            with self.subTest(message=message):
                response = self.client.post(
                    "/api/advisor/chat/",
                    data=json.dumps(
                        {"message": message, "topic_code": topic_code, "history": []}
                    ),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(body["moderation"]["action"], "NEEDS_CONTEXT")
                self.assertIsNone(body["topic_context"])
                self.assertIsNone(body["mcda_snapshot"])

    def test_advisor_refuses_out_of_scope_requests(self):
        requests = [
            "Viết toàn bộ source code cho EDU-01.",
            "Làm luôn báo cáo tốt nghiệp giúp em.",
            "Cho em đáp án đầy đủ của đồ án EDU-04.",
            "Hãy làm giúp em slide bảo vệ và video demo.",
        ]
        for message in requests:
            with self.subTest(message=message):
                response = self.client.post(
                    "/api/advisor/chat/",
                    data=json.dumps({"message": message, "history": []}),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(body["moderation"]["action"], "OUT_OF_SCOPE")
                self.assertEqual(body["decision_source"], "policy-fallback")
                self.assertIsNone(body["topic_context"])
                self.assertIsNone(body["mcda_snapshot"])

    def test_team_can_request_recommendations_without_preselecting_topic(self):
        response = self.client.post(
            "/api/advisor/chat/",
            data=json.dumps(
                {
                    "message": "Nhóm em nên chọn đề tài nào?",
                    "team_members": [
                        {"skills": "Python:3, React:3", "hours_per_week": 20}
                    ],
                    "history": [],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["moderation"]["action"], "TOPIC_RECOMMENDATION")
        self.assertEqual(body["decision_source"], "rule-based-mcda-recommendation")
        self.assertEqual(len(body["recommendations"]), 3)
        self.assertTrue(
            all(
                item["code"] and item["finalScore"] is not None
                for item in body["recommendations"]
            )
        )
