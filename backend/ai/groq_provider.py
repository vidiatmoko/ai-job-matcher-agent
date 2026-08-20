import json
import os
from pathlib import Path
from typing import Any, Dict

import requests
from dotenv import load_dotenv

from backend.ai.provider import AIProvider


BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


class GroqProvider(AIProvider):
    """
    Groq provider menggunakan OpenAI-compatible API.
    """

    name = "groq"

    def __init__(
        self,
        model: str = "openai/gpt-oss-120b",
        timeout: int = 60,
    ):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = model
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY tidak ditemukan di backend/.env"
            )

    def generate_json(
        self,
        prompt: str,
    ) -> Dict[str, Any]:

        url = (
            "https://api.groq.com/openai/v1/"
            "chat/completions"
        )

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0,
            "response_format": {
                "type": "json_object"
            },
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()

            content = (
                data["choices"][0]["message"]["content"]
            )

            return json.loads(content)

        except requests.RequestException as error:
            raise RuntimeError(
                f"Groq request failed: {error}"
            )

        except (KeyError, IndexError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Groq response tidak valid: {error}"
            )