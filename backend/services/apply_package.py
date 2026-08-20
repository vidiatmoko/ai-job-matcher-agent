import json
from typing import Dict, Any, List, Optional

from backend.db.database import (
    get_connection,
    initialize_database,
)


ACTIONABLE_ACTIONS = {
    "APPLY NOW",
    "APPLY WITH TAILORED CV",
    "VERIFY BEFORE APPLY",
}


def parse_json_list(value: Any) -> List[str]:
    """
    Mengubah JSON string dari SQLite menjadi list.
    """

    if not value:
        return []

    if isinstance(value, list):
        return value

    try:
        result = json.loads(value)

        if isinstance(result, list):
            return [
                str(item)
                for item in result
            ]

    except (
        json.JSONDecodeError,
        TypeError,
    ):
        pass

    return []


def get_best_opportunity() -> Optional[Dict[str, Any]]:
    """
    Mengambil opportunity terbaik saat ini.
    """

    initialize_database()

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                jobs.id,
                jobs.source,
                jobs.source_job_id,
                jobs.title,
                jobs.company,
                jobs.location,
                jobs.description,
                jobs.url,

                jobs.remote_status,
                jobs.remote_confidence,

                ai_evaluations.provider
                    AS ai_provider,

                ai_evaluations.model
                    AS ai_model,

                ai_evaluations.match_score,

                ai_evaluations.fit_summary,

                ai_evaluations.key_pros,

                ai_evaluations.key_gaps,

                ai_evaluations.recommended_action,

                ai_evaluations.draft_outreach,

                opportunity_assessments.geo_status,

                opportunity_assessments.geo_confidence,

                opportunity_assessments.geo_reason,

                opportunity_assessments.opportunity_score,

                opportunity_assessments.priority,

                opportunity_assessments.final_action

            FROM opportunity_assessments

            JOIN jobs
                ON jobs.id =
                   opportunity_assessments.job_id

            LEFT JOIN ai_evaluations
                ON ai_evaluations.id = (
                    SELECT MAX(id)
                    FROM ai_evaluations AS ae
                    WHERE ae.job_id = jobs.id
                )

            ORDER BY
                CASE opportunity_assessments.final_action
                    WHEN 'APPLY NOW' THEN 4
                    WHEN 'APPLY WITH TAILORED CV' THEN 3
                    WHEN 'VERIFY BEFORE APPLY' THEN 2
                    WHEN 'VERIFY' THEN 1
                    ELSE 0
                END DESC,

                opportunity_assessments.opportunity_score DESC,

                ai_evaluations.match_score DESC

            LIMIT 1
            """
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)


def get_application_package(
    opportunity: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Membuat paket lamaran dari data yang sudah ada.

    Tidak memanggil AI.
    """

    pros = parse_json_list(
        opportunity.get("key_pros")
    )

    gaps = parse_json_list(
        opportunity.get("key_gaps")
    )

    final_action = opportunity.get(
        "final_action",
        "REVIEW",
    )

    recommended_action = opportunity.get(
        "recommended_action",
        "Skip",
    )

    # ---------------------------------------------------------
    # CV FOCUS
    # ---------------------------------------------------------

    cv_focus = [
        "Python development",
        "n8n workflow automation",
        "REST API and webhook integration",
        "LLM / Generative AI implementation",
        "RAG and vector-search projects",
        "AI agent development",
        "IT and Operations background",
        "Process optimization and technical auditing",
    ]

    # Jangan menambahkan skill yang tidak ada
    # hanya karena job meminta skill tertentu.
    #
    # Gap tetap ditampilkan untuk human review.

    return {
        "job": {
            "database_id": opportunity.get("id"),
            "title": opportunity.get("title"),
            "company": opportunity.get("company"),
            "location": opportunity.get("location"),
            "source": opportunity.get("source"),
            "source_job_id": opportunity.get(
                "source_job_id"
            ),
            "url": opportunity.get("url"),
        },

        "assessment": {
            "match_score": opportunity.get(
                "match_score"
            ),
            "remote_status": opportunity.get(
                "remote_status"
            ),
            "remote_confidence": opportunity.get(
                "remote_confidence"
            ),
            "geo_status": opportunity.get(
                "geo_status"
            ),
            "geo_confidence": opportunity.get(
                "geo_confidence"
            ),
            "opportunity_score": opportunity.get(
                "opportunity_score"
            ),
            "priority": opportunity.get(
                "priority"
            ),
            "ai_provider": opportunity.get(
                "ai_provider"
            ),
            "ai_model": opportunity.get(
                "ai_model"
            ),
        },

        "decision": {
            "ai_action": recommended_action,
            "final_action": final_action,
            "human_review_required": (
                final_action
                in {
                    "VERIFY",
                    "VERIFY BEFORE APPLY",
                }
            ),
        },

        "application_strategy": {
            "cv_focus": cv_focus,
            "key_strengths": pros,
            "key_gaps": gaps,
            "fit_summary": opportunity.get(
                "fit_summary",
                "",
            ),
        },

        "outreach": opportunity.get(
            "draft_outreach",
            "",
        ),

        "application_url": opportunity.get(
            "url"
        ),

        "status": (
            "READY_FOR_HUMAN_REVIEW"
            if final_action
            in ACTIONABLE_ACTIONS
            else "NOT_READY"
        ),
    }


def print_application_package(
    package: Dict[str, Any],
):
    job = package["job"]
    assessment = package["assessment"]
    decision = package["decision"]
    strategy = package["application_strategy"]

    print()
    print("=" * 100)
    print("APPLICATION PACKAGE")
    print("=" * 100)

    print()
    print("--- JOB ---")
    print(
        f"Title       : {job['title']}"
    )
    print(
        f"Company     : {job['company']}"
    )
    print(
        f"Location    : {job['location']}"
    )
    print(
        f"Source      : {job['source']}"
    )
    print(
        f"URL         : {job['url']}"
    )

    print()
    print("--- SCORE ---")
    print(
        f"AI Match    : {assessment['match_score']}%"
    )
    print(
        f"Remote      : "
        f"{assessment['remote_status']} "
        f"({assessment['remote_confidence']})"
    )
    print(
        f"Geo         : "
        f"{assessment['geo_status']} "
        f"({assessment['geo_confidence']})"
    )
    print(
        f"Opportunity : "
        f"{assessment['opportunity_score']}"
    )
    print(
        f"Priority    : "
        f"{assessment['priority']}"
    )

    print()
    print("--- AI DECISION ---")
    print(
        f"AI Action   : "
        f"{decision['ai_action']}"
    )
    print(
        f"Final Action: "
        f"{decision['final_action']}"
    )
    print(
        f"Human Review: "
        f"{decision['human_review_required']}"
    )

    print()
    print("--- WHY THIS JOB ---")
    print(
        strategy["fit_summary"]
    )

    print()
    print("--- STRENGTHS TO EMPHASIZE ---")

    for item in strategy["key_strengths"]:
        print(
            f"- {item}"
        )

    print()
    print("--- GAPS TO HANDLE ---")

    for item in strategy["key_gaps"]:
        print(
            f"- {item}"
        )

    print()
    print("--- CV FOCUS ---")

    for item in strategy["cv_focus"]:
        print(
            f"- {item}"
        )

    print()
    print("--- OUTREACH ---")
    print(
        package["outreach"]
    )

    print()
    print("--- NEXT ACTION ---")

    if decision["final_action"] == "APPLY NOW":
        print(
            "ACTION: Review package, open URL, "
            "and submit application."
        )

    elif (
        decision["final_action"]
        == "APPLY WITH TAILORED CV"
    ):
        print(
            "ACTION: Tailor CV using CV focus, "
            "review gaps, then submit."
        )

    elif (
        decision["final_action"]
        == "VERIFY BEFORE APPLY"
    ):
        print(
            "ACTION: Verify location/work eligibility "
            "before applying."
        )

    else:
        print(
            "ACTION: Do not apply yet."
        )

    print()
    print("=" * 100)


if __name__ == "__main__":

    opportunity = get_best_opportunity()

    if not opportunity:
        print(
            "No opportunity available."
        )
        raise SystemExit(0)

    package = get_application_package(
        opportunity
    )

    print_application_package(
        package
    )