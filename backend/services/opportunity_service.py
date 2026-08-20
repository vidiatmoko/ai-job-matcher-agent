from datetime import datetime, timezone
from typing import Dict, Any, List

from backend.db.database import (
    get_connection,
    initialize_database,
)

from backend.services.geo_eligibility import (
    assess_geo_eligibility,
    calculate_opportunity_score,
    classify_priority,
)


def now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def determine_final_action(
    match_score: float,
    recommended_action: str,
    remote_status: str,
    remote_confidence: str,
    geo_status: str,
) -> str:

    if geo_status == "RESTRICTED":
        return "DO NOT APPLY"

    if remote_status in {
        "ONSITE",
        "HYBRID",
    }:
        return "DO NOT APPLY"

    if geo_status == "NEEDS_VERIFICATION":
        if match_score >= 65:
            return "VERIFY BEFORE APPLY"

        return "VERIFY"

    if remote_status == "UNKNOWN":
        if match_score >= 65:
            return "VERIFY BEFORE APPLY"

        return "VERIFY"

    if recommended_action == "Apply Immediately":
        return "APPLY NOW"

    if recommended_action == "Apply with tailored CV":
        return "APPLY WITH TAILORED CV"

    if recommended_action == "Skip":
        return "SKIP"

    return "REVIEW"


def assess_job(
    job: Dict[str, Any],
) -> Dict[str, Any]:

    geo = assess_geo_eligibility(
        job
    )

    match_score = float(
        job.get(
            "match_score",
            0,
        )
    )

    remote_status = job.get(
        "remote_status",
        "UNKNOWN",
    )

    remote_confidence = job.get(
        "remote_confidence",
        "UNKNOWN",
    )

    recommended_action = job.get(
        "recommended_action",
        "Skip",
    )

    opportunity_score = calculate_opportunity_score(
        match_score=match_score,
        remote_status=remote_status,
        remote_confidence=remote_confidence,
        geo_status=geo["status"],
    )

    priority = classify_priority(
        opportunity_score=opportunity_score,
        match_score=match_score,
        geo_status=geo["status"],
    )

    final_action = determine_final_action(
        match_score=match_score,
        recommended_action=recommended_action,
        remote_status=remote_status,
        remote_confidence=remote_confidence,
        geo_status=geo["status"],
    )

    return {
        "geo_status": geo["status"],
        "geo_confidence": geo.get(
            "confidence",
            "LOW",
        ),
        "geo_reason": geo["reason"],
        "opportunity_score": opportunity_score,
        "priority": priority,
        "final_action": final_action,
    }


def save_opportunity_assessment(
    job_id: int,
    assessment: Dict[str, Any],
):
    initialize_database()

    timestamp = now_iso()

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO opportunity_assessments (
                job_id,
                geo_status,
                geo_confidence,
                geo_reason,
                opportunity_score,
                priority,
                final_action,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(job_id)
            DO UPDATE SET
                geo_status = excluded.geo_status,
                geo_confidence = excluded.geo_confidence,
                geo_reason = excluded.geo_reason,
                opportunity_score =
                    excluded.opportunity_score,
                priority = excluded.priority,
                final_action = excluded.final_action,
                updated_at = excluded.updated_at
            """,
            (
                job_id,
                assessment["geo_status"],
                assessment["geo_confidence"],
                assessment["geo_reason"],
                assessment["opportunity_score"],
                assessment["priority"],
                assessment["final_action"],
                timestamp,
                timestamp,
            ),
        )


def list_priority_opportunities(
    minimum_priority: str = "MEDIUM",
) -> List[Dict[str, Any]]:

    priority_order = {
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
        "VERIFY": 0,
    }

    minimum_value = priority_order.get(
        minimum_priority,
        2,
    )

    allowed = [
        status
        for status, value
        in priority_order.items()
        if value >= minimum_value
    ]

    placeholders = ", ".join(
        "?"
        for _ in allowed
    )

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            f"""
            SELECT
                jobs.id,
                jobs.title,
                jobs.company,
                jobs.location,
                jobs.url,
                jobs.source,

                jobs.remote_status,
                jobs.remote_confidence,

                ai_evaluations.match_score,
                ai_evaluations.recommended_action,

                opportunity_assessments.geo_status,
                opportunity_assessments.geo_confidence,
                opportunity_assessments.geo_reason,
                opportunity_assessments.opportunity_score,
                opportunity_assessments.priority,
                opportunity_assessments.final_action

            FROM opportunity_assessments

            JOIN jobs
                ON opportunity_assessments.job_id =
                   jobs.id

            LEFT JOIN ai_evaluations
                ON ai_evaluations.id = (
                    SELECT MAX(id)
                    FROM ai_evaluations AS ae
                    WHERE ae.job_id = jobs.id
                )

            WHERE opportunity_assessments.priority
                  IN ({placeholders})

            ORDER BY
                CASE opportunity_assessments.priority
                    WHEN 'HIGH' THEN 3
                    WHEN 'MEDIUM' THEN 2
                    WHEN 'LOW' THEN 1
                    ELSE 0
                END DESC,

                opportunity_assessments.opportunity_score DESC,

                ai_evaluations.match_score DESC
            """,
            allowed,
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]