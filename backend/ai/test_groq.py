from backend.ai.groq_provider import GroqProvider


def main():
    provider = GroqProvider()

    result = provider.generate_json(
        """
Return ONLY valid JSON.

{
    "status": "ok",
    "provider": "groq"
}
"""
    )

    print(result)


if __name__ == "__main__":
    main()