from backend.services.opportunity_service import (
    list_priority_opportunities,
)


def get_top_opportunities(
    limit: int = 5,
):
    """
    Mengambil peluang terbaik yang actionable.

    Yang ditampilkan:
    - APPLY NOW
    - APPLY WITH TAILORED CV
    - VERIFY BEFORE APPLY

    Yang tidak ditampilkan:
    - DO NOT APPLY
    - SKIP
    - VERIFY biasa
    """

    opportunities = list_priority_opportunities(
        minimum_priority="MEDIUM"
    )

    actionable = [
        item
        for item in opportunities
        if item["final_action"]
        in {
            "APPLY NOW",
            "APPLY WITH TAILORED CV",
            "VERIFY BEFORE APPLY",
        }
    ]

    return actionable[:limit]


if __name__ == "__main__":

    opportunities = get_top_opportunities(
        limit=5
    )

    print()
    print("=" * 100)
    print("TOP ACTIONABLE OPPORTUNITIES")
    print("=" * 100)

    if not opportunities:
        print("No actionable opportunities found.")
        raise SystemExit(0)

    for index, job in enumerate(
        opportunities,
        start=1,
    ):

        print()
        print(f"#{index}")
        print("-" * 100)

        print(
            f"Title       : {job['title']}"
        )

        print(
            f"Company     : {job['company']}"
        )

        print(
            f"Source      : {job['source']}"
        )

        print(
            f"Match Score : {job['match_score']}%"
        )

        print(
            f"Remote      : "
            f"{job['remote_status']} "
            f"({job['remote_confidence']})"
        )

        print(
            f"Geo         : "
            f"{job['geo_status']}"
        )

        print(
            f"Opportunity : "
            f"{job['opportunity_score']}"
        )

        print(
            f"Priority    : "
            f"{job['priority']}"
        )

        print(
            f"AI Action   : "
            f"{job['recommended_action']}"
        )

        print(
            f"FINAL ACTION: "
            f"{job['final_action']}"
        )

        print(
            f"URL         : "
            f"{job['url']}"
        )