from backend.ai.router import AIRouter


def main():

    router = AIRouter()

    print(
        "AVAILABLE:",
        router.available_providers()
    )

    provider, result = router.generate_json(
        """
Return ONLY valid JSON.

{
    "status": "ok",
    "message": "AI router is working"
}
"""
    )

    print(
        "USED PROVIDER:",
        provider
    )

    print(
        "RESULT:",
        result
    )


if __name__ == "__main__":
    main()