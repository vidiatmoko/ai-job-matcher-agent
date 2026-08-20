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


class OpenRouterProvider(AIProvider):
    """
    OpenRouter provider.

    Untuk MVP gratis kita menggunakan:
        openrouter/free

    Model aktual dipilih oleh OpenRouter dari
    model free yang tersedia.
    """

    name = "openrouter"

    def __init__(
        self,
        model: str = "openrouter/free",
        timeout: int = 90,
    ):
        self.api_key = os.getenv(
            "OPENROUTER_API_KEY"
        )

        self.model = model
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY tidak ditemukan "
                "di backend/.env"
            )

    def generate_json(
        self,
        prompt: str,
    ) -> Dict[str, Any]:

        url = (
            "https://openrouter.ai/api/v1/"
            "chat/completions"
        )

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
            "Content-Type": "application/json",
            "X-Title": "AI Career Copilot",
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
                f"OpenRouter request failed: {error}"
            )

        except (
            KeyError,
            IndexError,
            json.JSONDecodeError,
        ) as error:
            raise RuntimeError(
                f"OpenRouter response tidak valid: {error}"
            )