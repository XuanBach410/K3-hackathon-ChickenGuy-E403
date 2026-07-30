import json

from django.test import TestCase

from .mcda_engine import calculate_mcda_score, extract_latent_skills


class DecisionSupportTests(TestCase):
	def test_serialized_react_skills_are_available_to_mcda(self):
		skills = extract_latent_skills({"skills": "Python:3, React:4"})

		self.assertEqual(skills, {"Python": 3, "React": 4})

	def test_preliminary_payload_contains_explainable_risk_data(self):
		response = self.client.post(
			"/api/evaluate/preliminary/",
			data=json.dumps({
				"team_members": [{"skills": "Python:3, React:3"}],
				"selected_codes": ["EDU-01"],
			}),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 200)
		result = response.json()["results"][0]
		self.assertIn("riskMatrix", result)
		self.assertIsInstance(result["missingTechs"], list)
		self.assertTrue(all("criticality" in skill for skill in result["missingTechs"]))

	def test_verifier_endpoint_uses_registered_question_bank(self):
		response = self.client.post(
			"/api/evaluate/verify-skills/",
			data=json.dumps({"declared_skills": ["Python", "Docker"]}),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 200)
		quizzes = response.json()["verification_quizzes"]
		self.assertEqual([quiz["skill"] for quiz in quizzes], ["Python", "Docker"])
		self.assertEqual(len(quizzes[0]["options"]), 5)

	def test_what_if_improves_score_for_a_missing_required_skill(self):
		topic = {
			"tech_stack": "Python RAG",
			"requirements": "Build a RAG prototype",
			"category": "AI",
			"max_team": 4,
		}
		team = [{"skills": "Python:3"}]
		baseline = calculate_mcda_score(team, topic)
		improved = calculate_mcda_score([{"skills": "Python:3, RAG:3"}], topic)

		self.assertGreater(improved["finalScore"], baseline["finalScore"])
		self.assertNotEqual(improved["riskMatrix"]["skill_risk"], "High")

# Create your tests here.
