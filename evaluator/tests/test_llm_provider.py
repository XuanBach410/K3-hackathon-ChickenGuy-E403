import json
import urllib.error
from unittest.mock import patch, MagicMock
from django.test import TestCase
from evaluator.llm_provider import LLMProvider

class LLMProviderTests(TestCase):
    @patch('urllib.request.urlopen')
    def test_call_gemini_success(self, mock_urlopen):
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": '{"result": "success"}'}
                        ]
                    }
                }
            ]
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = LLMProvider._call_gemini("api_key", "system", "user", "gemini-1.5-flash")
        self.assertEqual(res, {"result": "success"})

    @patch('urllib.request.urlopen')
    def test_call_gemini_failure(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Timeout")
        res = LLMProvider._call_gemini("api_key", "system", "user", "gemini-1.5-flash")
        self.assertIsNone(res)

    @patch('urllib.request.urlopen')
    def test_call_openai_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [
                {
                    "message": {
                        "content": '{"openai_result": "ok"}'
                    }
                }
            ]
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = LLMProvider._call_openai("api_key", "system", "user", "gpt-4o-mini")
        self.assertEqual(res, {"openai_result": "ok"})

    @patch('urllib.request.urlopen')
    def test_call_openai_failure(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Network Error")
        res = LLMProvider._call_openai("api_key", "system", "user", "gpt-4o-mini")
        self.assertIsNone(res)

    @patch('evaluator.llm_provider.LLMProvider._call_gemini')
    @patch('evaluator.llm_provider.LLMProvider._call_openai')
    def test_call_llm_dispatch(self, mock_openai, mock_gemini):
        # No api key
        self.assertIsNone(LLMProvider.call_llm(None, None, "sys", "usr"))
        
        # Gemini dispatch
        LLMProvider.call_llm("gemini", "key", "sys", "usr")
        mock_gemini.assert_called_with("key", "sys", "usr", "gemini-1.5-flash")
        
        # OpenAI dispatch
        LLMProvider.call_llm("openai", "key", "sys", "usr")
        mock_openai.assert_called_with("key", "sys", "usr", "gpt-4o-mini")

        # Fallback dispatch (unknown provider)
        LLMProvider.call_llm("unknown", "key", "sys", "usr")
        mock_gemini.assert_called_with("key", "sys", "usr", "gemini-1.5-flash")
