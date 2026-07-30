import json
from django.test import TestCase
from django.urls import reverse

class EvalQuestionsIntegrationTests(TestCase):
    def setUp(self):
        with open('eval/test_questions.json', 'r', encoding='utf-8') as f:
            self.questions = json.load(f)

    def test_questions_file_loaded(self):
        self.assertTrue(len(self.questions) >= 20)

    def test_health_endpoint(self):
        res = self.client.get('/api/health/')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get('status'), 'ok')

    # Skeleton: each question can be used manually or extended to call specific endpoints
    def test_sample_question_exec(self):
        q = self.questions[0]
        self.assertIn('input', q)
        self.assertIn('expected_response', q)
