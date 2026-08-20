import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.ai.provider import AIProvider


BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


class GeminiProvider(AIProvider):
    """
    Gemini AI provider.

    Gemini menjadi primary provider.
    """

    name = "gemini"

    def __init__(
        self,
        model: str = "gemini-3.6-flash",
    ):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY tidak ditemukan di backend/.env"
            )

        self.client = genai.Client(
            api_key=self.api_key
        )

    def generate_json(
        self,
        prompt: str,
    ) -> Dict[str, Any]:
        """
        Generate JSON menggunakan Gemini.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini mengembalikan response kosong."
                )

            return json.loads(
                response.text.strip()
            )

        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Gemini mengembalikan JSON tidak valid: {error}"
            )

        except Exception as error:
            raise RuntimeError(
                f"Gemini request failed: {error}"
            )