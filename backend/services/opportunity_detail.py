from typing import Optional, Dict, Any

from backend.db.database import (
    get_connection,
    initialize_database,
)


def get_opportunity_detail(
    job_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Mengambil detail lengkap satu opportunity
    beserta hasil AI dan opportunity assessment.
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
                jobs.salary_min,
                jobs.salary_max,
                jobs.created_at,
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

                opportunity_assessments.geo_reason,

                opportunity_assessments.opportunity_score,

                opportunity_assessments.priority,

                opportunity_assessments.final_action

            FROM jobs

            LEFT JOIN ai_evaluations
                ON ai_evaluations.id = (
                    SELECT MAX(ae.id)
                    FROM ai_evaluations ae
                    WHERE ae.job_id = jobs.id
                )

            LEFT JOIN opportunity_assessments
                ON opportunity_assessments.job_id = jobs.id

            WHERE jobs.id = ?

            LIMIT 1
            """,
            (job_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)


def get_top_opportunity_detail(
    limit: int = 1,
) -> list:
    """
    Mengambil opportunity dengan priority tertinggi.
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
                jobs.salary_min,
                jobs.salary_max,
                jobs.created_at,
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
                    SELECT MAX(ae.id)
                    FROM ai_evaluations ae
                    WHERE ae.job_id = jobs.id
                )

            ORDER BY
                CASE opportunity_assessments.priority
                    WHEN 'HIGH' THEN 3
                    WHEN 'MEDIUM' THEN 2
                    WHEN 'LOW' THEN 1
                    ELSE 0
                END DESC,

                opportunity_assessments.opportunity_score DESC,

                ai_evaluations.match_score DESC

            LIMIT ?
            """,
            (limit,),
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]


def print_opportunity(
    opportunity: Dict[str, Any],
) -> None:

    print()
    print("=" * 100)
    print("OPPORTUNITY DETAIL")
    print("=" * 100)

    print()
    print(f"Database ID   : {opportunity.get('id')}")
    print(f"Source         : {opportunity.get('source')}")
    print(f"Source Job ID  : {opportunity.get('source_job_id')}")
    print(f"Title          : {opportunity.get('title')}")
    print(f"Company        : {opportunity.get('company')}")
    print(f"Location       : {opportunity.get('location')}")
    print(f"URL            : {opportunity.get('url')}")

    print()
    print("--- REMOTE ---")
    print(
        f"Status         : "
        f"{opportunity.get('remote_status')}"
    )
    print(
        f"Confidence     : "
        f"{opportunity.get('remote_confidence')}"
    )

    print()
    print("--- GEO ---")
    print(
        f"Status         : "
        f"{opportunity.get('geo_status')}"
    )
    print(
        f"Reason         : "
        f"{opportunity.get('geo_reason')}"
    )

    print()
    print("--- AI ---")
    print(
        f"Provider       : "
        f"{opportunity.get('ai_provider')}"
    )
    print(
        f"Model          : "
        f"{opportunity.get('ai_model')}"
    )
    print(
        f"Match Score    : "
        f"{opportunity.get('match_score')}%"
    )
    print(
        f"AI Action      : "
        f"{opportunity.get('recommended_action')}"
    )

    print()
    print("--- OPPORTUNITY ---")
    print(
        f"Opportunity    : "
        f"{opportunity.get('opportunity_score')}"
    )
    print(
        f"Priority       : "
        f"{opportunity.get('priority')}"
    )
    print(
        f"Final Action   : "
        f"{opportunity.get('final_action')}"
    )

    print()
    print("--- FIT SUMMARY ---")
    print(
        opportunity.get(
            "fit_summary",
            "",
        )
    )

    print()
    print("--- PROS ---")
    print(
        opportunity.get(
            "key_pros",
            "",
        )
    )

    print()
    print("--- GAPS ---")
    print(
        opportunity.get(
            "key_gaps",
            "",
        )
    )

    print()
    print("--- OUTREACH ---")
    print(
        opportunity.get(
            "draft_outreach",
            "",
        )
    )

    print()
    print("--- DESCRIPTION ---")
    print(
        opportunity.get(
            "description",
            "",
        )
    )


if __name__ == "__main__":

    opportunities = get_top_opportunity_detail(
        limit=1
    )

    if not opportunities:
        print(
            "No opportunity found."
        )
        raise SystemExit(0)

    print_opportunity(
        opportunities[0]
    )