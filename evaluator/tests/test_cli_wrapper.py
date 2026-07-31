import json
import subprocess
import unittest
import os

class TestCliAgentTools(unittest.TestCase):
    def setUp(self):
        self.script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "scripts", 
            "cli_agent_tools.py"
        )
        self.python_exec = "python" # assuming python is in PATH or venv is active

    def run_cli(self, tool_name, kwargs):
        cmd = [self.python_exec, self.script_path, tool_name, "--kwargs", json.dumps(kwargs)]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        return result

    def test_cli_get_topic_by_keyword(self):
        # We test get_topic_by_keyword which does not require complex kwargs
        res = self.run_cli("get_topic_by_keyword", {"keyword": "edu"})
        self.assertEqual(res.returncode, 0)
        
        try:
            output_json = json.loads(res.stdout)
            self.assertEqual(output_json.get("status"), "success")
            self.assertIn("topics", output_json)
        except json.JSONDecodeError:
            self.fail("CLI did not return valid JSON: " + res.stdout)

    def test_cli_invalid_json_kwargs(self):
        cmd = [self.python_exec, self.script_path, "verify_declared_skills", "--kwargs", "{invalid_json}"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0)
        output_json = json.loads(result.stdout)
        self.assertIn("error", output_json)
        self.assertIn("Lỗi parse JSON kwargs", output_json["error"])

    def test_cli_unregistered_tool(self):
        res = self.run_cli("non_existent_tool_xyz", {})
        self.assertEqual(res.returncode, 0) # The script prints JSON with error gracefully
        output_json = json.loads(res.stdout)
        self.assertIn("error", output_json)

if __name__ == '__main__':
    unittest.main()
