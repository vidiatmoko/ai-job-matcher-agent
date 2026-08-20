import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv

from backend.ai.provider import AIProvider
from backend.ai.gemini_provider import GeminiProvider
from backend.ai.groq_provider import GroqProvider
from backend.ai.openrouter_provider import OpenRouterProvider


BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


class AIRouter:
    """
    AI Provider Router.

    Priority:
        Gemini
        ↓
        Groq
        ↓
        OpenRouter
    """

    def __init__(self):

        self.providers: List[AIProvider] = []

        # Provider terakhir yang berhasil.
        self.last_provider = "unknown"
        self.last_model = "unknown"

        # ====================================================
        # Gemini - PRIMARY
        # ====================================================

        if os.getenv("GEMINI_API_KEY"):
            self.providers.append(
                GeminiProvider(
                    model="gemini-3.6-flash"
                )
            )

        # ====================================================
        # Groq - FALLBACK 1
        # ====================================================

        if os.getenv("GROQ_API_KEY"):
            self.providers.append(
                GroqProvider(
                    model="openai/gpt-oss-120b"
                )
            )

        # ====================================================
        # OpenRouter - FALLBACK 2
        # ====================================================

        if os.getenv("OPENROUTER_API_KEY"):
            self.providers.append(
                OpenRouterProvider(
                    model="openrouter/free"
                )
            )

    def available_providers(self) -> List[str]:
        """
        Menampilkan provider yang tersedia.
        """

        return [
            provider.name
            for provider in self.providers
        ]

    def generate_json(
        self,
        prompt: str,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Mencoba provider berdasarkan urutan priority.

        Return:
            provider_name, result
        """

        if not self.providers:
            raise RuntimeError(
                "Tidak ada AI provider yang tersedia."
            )

        errors = []

        for provider in self.providers:

            try:
                print(
                    f"[AI ROUTER] Trying "
                    f"{provider.name}..."
                )

                result = provider.generate_json(
                    prompt
                )

                # Simpan provider + model yang berhasil.
                self.last_provider = (
                    provider.name
                )

                self.last_model = getattr(
                    provider,
                    "model",
                    "unknown",
                )

                print(
                    f"[AI ROUTER] Success: "
                    f"{provider.name}"
                    f" / {self.last_model}"
                )

                return (
                    provider.name,
                    result,
                )

            except Exception as error:

                message = str(error)

                print(
                    f"[AI ROUTER] Failed: "
                    f"{provider.name}"
                )

                errors.append(
                    f"{provider.name}: {message}"
                )

                continue

        raise RuntimeError(
            "Semua AI provider gagal:\n"
            + "\n".join(errors)
        )


if __name__ == "__main__":

    router = AIRouter()

    print(
        "Available AI Providers:"
    )

    for provider in router.available_providers():
        print(f"- {provider}")