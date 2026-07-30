import json
import urllib.error
import urllib.request


class LLMProvider:
    @staticmethod
    def call_llm(provider, api_key, system_prompt, user_prompt, model_name=None):
        """
        Generic LLM caller supporting Gemini API (gemini-3.6-flash / gemini-1.5-flash)
        and OpenAI API (gpt-4o / gpt-4o-mini).
        Fallback to rule-based response if API key is missing or call fails.
        """
        if not api_key:
            return None  # Fallback signal

        provider = provider.lower() if provider else "gemini"

        if "gemini" in provider:
            return LLMProvider._call_gemini(
                api_key, system_prompt, user_prompt, model_name or "gemini-1.5-flash"
            )
        elif "openai" in provider or "gpt" in provider:
            return LLMProvider._call_openai(
                api_key, system_prompt, user_prompt, model_name or "gpt-4o-mini"
            )
        else:
            return LLMProvider._call_gemini(
                api_key, system_prompt, user_prompt, "gemini-1.5-flash"
            )

    @staticmethod
    def _call_gemini(api_key, system_prompt, user_prompt, model):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_prompt}\n\nUSER REQUEST:\n{user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json",
            },
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                result = json.loads(response.read().decode("utf-8"))
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except Exception as e:
            print(f"[LLMProvider] Gemini error: {e}")
            return None

    @staticmethod
    def _call_openai(api_key, system_prompt, user_prompt, model):
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                result = json.loads(response.read().decode("utf-8"))
                text = result["choices"][0]["message"]["content"]
                return json.loads(text)
        except Exception as e:
            print(f"[LLMProvider] OpenAI error: {e}")
            return None
