"""
Step 19: Test LLM Connection
Purpose: Verify Python can call the configured LLM provider.
Input: LLM settings from .env.
Output: Short LLM response or clear error.
Run: python scripts/test_llm_connection.py
"""

import os

import requests
from dotenv import load_dotenv


GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise ValueError(f"Missing required environment variable: {name}")

    return value


def call_groq_test_message(api_key: str, model: str) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Reply with exactly: LLM connection working",
            },
            {
                "role": "user",
                "content": "Test connection.",
            },
        ],
        "temperature": 0,
        "max_completion_tokens": 20,
    }

    response = requests.post(
        GROQ_CHAT_COMPLETIONS_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(f"LLM request failed: {response.status_code} {response.text}")

    response_json = response.json()

    return response_json["choices"][0]["message"]["content"]


def main() -> None:
    load_dotenv()

    provider = get_required_env("LLM_PROVIDER")

    if provider != "groq":
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

    api_key = get_required_env("LLM_API_KEY")
    model = get_required_env("LLM_MODEL")

    result = call_groq_test_message(api_key, model)

    print("LLM connection successful.")
    print(f"Model: {model}")
    print(f"Response: {result}")


if __name__ == "__main__":
    main()

