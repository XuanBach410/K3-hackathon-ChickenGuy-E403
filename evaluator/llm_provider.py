import requests
import json
import os

class LLMProvider:
    @staticmethod
    def call_llm(provider, api_key, system_prompt, user_prompt):
        if provider == "qwen":
            key = api_key or os.getenv("QWEN_API_KEY")
            url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}"
            }
            payload = {
                "model": "qwen3.7-plus",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    text = response.json()["choices"][0]["message"]["content"]
                    return json.loads(text)
                else:
                    print("Qwen API Error Status", response.status_code, response.text)
            except Exception as e:
                print("Qwen API Error:", e)
        elif provider == "openai":
            key = api_key or os.getenv("OPENAI_API_KEY")
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}"
            }
            payload = {
                "model": "gpt-5.6-luna",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    text = response.json()["choices"][0]["message"]["content"]
                    return json.loads(text)
                else:
                    print("OpenAI API Error Status", response.status_code, response.text)
            except Exception as e:
                print("OpenAI API Error:", e)
        else: # Default to Gemini
            key = api_key or os.getenv("GEMINI_API_KEY")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    text = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
                    return json.loads(text)
                else:
                    print("Gemini API Error Status", response.status_code, response.text)
            except Exception as e:
                print("Gemini API Error:", e)
        return None
