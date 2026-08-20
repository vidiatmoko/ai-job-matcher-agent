from typing import List, Dict, Any

from backend.db.database import (
    get_connection,
    initialize_database,
)

from backend.services.opportunity_service import (
    assess_job,
    save_opportunity_assessment,
)


def get_latest_jobs_with_ai() -> List[Dict[str, Any]]:
    initialize_database()

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                jobs.id,
                jobs.title,
                jobs.company,
                jobs.location,
                jobs.description,
                jobs.url,
                jobs.source,
                jobs.remote_status,
                jobs.remote_confidence,

                ai_evaluations.match_score,
                ai_evaluations.recommended_action,
                ai_evaluations.provider,
                ai_evaluations.model

            FROM jobs

            JOIN ai_evaluations
                ON ai_evaluations.id = (
                    SELECT MAX(ae.id)
                    FROM ai_evaluations ae
                    WHERE ae.job_id = jobs.id
                )

            ORDER BY ai_evaluations.match_score DESC
            """
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]


def process_opportunities():

    jobs = get_latest_jobs_with_ai()

    print(
        f"Found {len(jobs)} jobs with AI evaluation."
    )

    processed = []

    for job in jobs:

        assessment = assess_job(
            job
        )

        save_opportunity_assessment(
            job_id=job["id"],
            assessment=assessment,
        )

        processed.append(
            {
                **job,
                **assessment,
            }
        )

    processed.sort(
        key=lambda job: (
            {
                "HIGH": 3,
                "MEDIUM": 2,
                "LOW": 1,
                "VERIFY": 0,
            }.get(
                job["priority"],
                0,
            ),

            job["opportunity_score"],

            job.get(
                "match_score",
                0,
            ),
        ),
        reverse=True,
    )

    return processed


if __name__ == "__main__":

    results = process_opportunities()

    print()
    print("=" * 100)
    print("OPPORTUNITY PRIORITY")
    print("=" * 100)

    for index, job in enumerate(
        results,
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
            f"Location    : {job['location']}"
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
            f"Geo         : {job['geo_status']}"
        )

        print(
            f"Opportunity : "
            f"{job['opportunity_score']}"
        )

        print(
            f"Priority    : {job['priority']}"
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
            f"URL         : {job['url']}"
        )