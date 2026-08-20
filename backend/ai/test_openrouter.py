from backend.ai.openrouter_provider import OpenRouterProvider


def main():
    provider = OpenRouterProvider()

    result = provider.generate_json(
        """
Return ONLY valid JSON.

{
    "status": "ok",
    "provider": "openrouter"
}
"""
    )

    print(result)


if __name__ == "__main__":
    main()