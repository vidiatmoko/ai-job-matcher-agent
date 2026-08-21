from datetime import datetime, timezone
import json
from typing import Optional, Dict, Any

from backend.db.database import (
    get_connection,
    initialize_database,
)


def now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def save_job(
    job: Dict[str, Any],
) -> int:
    initialize_database()

    timestamp = now_iso()

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO jobs (
                source,
                source_job_id,
                title,
                company,
                location,
                description,
                url,
                salary_min,
                salary_max,
                created_at,
                deadline,
                remote_status,
                remote_confidence,
                first_seen_at,
                last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(source, source_job_id)
            DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                location = excluded.location,
                description = excluded.description,
                url = excluded.url,
                salary_min = excluded.salary_min,
                salary_max = excluded.salary_max,
                created_at = excluded.created_at,
                deadline = excluded.deadline,
                remote_status = excluded.remote_status,
                remote_confidence = excluded.remote_confidence,
                last_seen_at = excluded.last_seen_at
            """,
            (
                job.get("source", ""),
                job.get("source_job_id"),
                job.get("title", ""),
                job.get("company", ""),
                job.get("location", ""),
                job.get("description", ""),
                job.get("url", ""),
                job.get("salary_min"),
                job.get("salary_max"),
                job.get("created_at"),
                job.get("deadline"),
                job.get(
                    "remote_status",
                    "UNKNOWN",
                ),
                job.get(
                    "remote_confidence",
                    "UNKNOWN",
                ),
                timestamp,
                timestamp,
            ),
        )

        cursor.execute(
            """
            SELECT id
            FROM jobs
            WHERE source = ?
              AND source_job_id = ?
            """,
            (
                job.get("source", ""),
                job.get("source_job_id"),
            ),
        )

        row = cursor.fetchone()

        if row is None:
            raise RuntimeError(
                "Job berhasil diproses tetapi ID "
                "tidak dapat ditemukan."
            )

        return int(row["id"])


def save_ai_evaluation(
    job_id: int,
    result: Dict[str, Any],
    provider: str,
    model: str,
    profile_version: str = "v1",
) -> int:

    initialize_database()

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO ai_evaluations (
                job_id,
                provider,
                model,
                profile_version,
                match_score,
                fit_summary,
                key_pros,
                key_gaps,
                recommended_action,
                draft_outreach,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                provider,
                model,
                profile_version,
                result.get(
                    "match_score"
                ),
                result.get(
                    "fit_summary",
                    "",
                ),
                json.dumps(
                    result.get(
                        "key_pros",
                        [],
                    ),
                    ensure_ascii=False,
                ),
                json.dumps(
                    result.get(
                        "key_gaps",
                        [],
                    ),
                    ensure_ascii=False,
                ),
                result.get(
                    "recommended_action",
                    "Skip",
                ),
                result.get(
                    "draft_outreach",
                    "",
                ),
                now_iso(),
            ),
        )

        return cursor.lastrowid


def get_latest_ai_evaluation_id(
    job_id: int,
) -> Optional[int]:

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM ai_evaluations
            WHERE job_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (job_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return int(row["id"])


def get_application_eligibility(
    job_id: int,
) -> Dict[str, Any]:

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                opportunity_assessments.final_action,
                jobs.deadline,
                ai_evaluations.id AS ai_evaluation_id,
                ai_evaluations.match_score,
                ai_evaluations.recommended_action

            FROM jobs

            LEFT JOIN opportunity_assessments
                ON opportunity_assessments.job_id =
                   jobs.id

            LEFT JOIN ai_evaluations
                ON ai_evaluations.id = (
                    SELECT MAX(ae.id)
                    FROM ai_evaluations ae
                    WHERE ae.job_id = jobs.id
                )

            WHERE jobs.id = ?

            LIMIT 1
            """,
            (job_id,),
        )

        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                "Job tidak ditemukan."
            )

        return dict(row)


def create_application(
    job_id: int,
    ai_evaluation_id: Optional[int] = None,
    application_channel: str = "MANUAL",
    cv_version: str = "v1",
    notes: str = "",
) -> int:
    """
    Membuat application.

    Job dengan:
        SKIP
        DO NOT APPLY

    tidak boleh ditandai APPLIED.

    Job tanpa AI evaluation juga ditolak.
    """

    initialize_database()

    eligibility = get_application_eligibility(
        job_id
    )

    final_action = eligibility.get(
        "final_action"
    )

    if final_action in {
        "SKIP",
        "DO NOT APPLY",
    }:
        raise ValueError(
            f"Job tidak boleh ditandai APPLIED "
            f"karena final action adalah: "
            f"{final_action}"
        )

    deadline = eligibility.get("deadline")

    if deadline:
        try:
            deadline_dt = datetime.fromisoformat(
                deadline.replace("Z", "+00:00")
            )

            if deadline_dt.tzinfo is None:
                deadline_dt = deadline_dt.replace(
                    tzinfo=timezone.utc
                )

            if deadline_dt < datetime.now(timezone.utc):
                raise ValueError(
                    "Job sudah melewati deadline dan "
                    "tidak boleh ditandai APPLIED."
                )

        except ValueError as error:
            if "sudah melewati deadline" in str(error):
                raise

    if ai_evaluation_id is None:
        ai_evaluation_id = eligibility.get(
            "ai_evaluation_id"
        )

    if ai_evaluation_id is None:
        ai_evaluation_id = (
            get_latest_ai_evaluation_id(
                job_id
            )
        )

    if ai_evaluation_id is None:
        raise ValueError(
            "AI evaluation untuk job ini tidak ditemukan."
        )

    timestamp = now_iso()

    with get_connection() as connection:

        cursor = connection.cursor()

        # Hindari duplicate application yang aktif.
        cursor.execute(
            """
            SELECT id
            FROM applications
            WHERE job_id = ?
              AND status NOT IN (
                  'REJECTED',
                  'WITHDRAWN'
              )
            ORDER BY id DESC
            LIMIT 1
            """,
            (job_id,),
        )

        existing = cursor.fetchone()

        if existing is not None:
            raise ValueError(
                "Job ini sudah memiliki application aktif "
                f"dengan ID {existing['id']}."
            )

        cursor.execute(
            """
            INSERT INTO applications (
                job_id,
                ai_evaluation_id,
                application_channel,
                cv_version,
                status,
                applied_at,
                last_updated_at,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                ai_evaluation_id,
                application_channel,
                cv_version,
                "APPLIED",
                timestamp,
                timestamp,
                notes,
            ),
        )

        application_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO application_events (
                application_id,
                event_type,
                event_date,
                notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                application_id,
                "APPLIED",
                timestamp,
                notes,
            ),
        )

        return application_id


def update_application_status(
    application_id: int,
    status: str,
    notes: str = "",
) -> None:

    valid_statuses = {
        "SAVED",
        "REVIEWED",
        "APPLIED",
        "RECRUITER_CONTACTED",
        "INTERVIEW",
        "TECHNICAL_TEST",
        "FINAL_INTERVIEW",
        "OFFER",
        "REJECTED",
        "NO_RESPONSE",
        "WITHDRAWN",
    }

    if status not in valid_statuses:
        raise ValueError(
            f"Status tidak valid: {status}"
        )

    timestamp = now_iso()

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE applications
            SET status = ?,
                last_updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                timestamp,
                application_id,
            ),
        )

        cursor.execute(
            """
            INSERT INTO application_events (
                application_id,
                event_type,
                event_date,
                notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                application_id,
                status,
                timestamp,
                notes,
            ),
        )


def list_applications():

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                applications.id,
                applications.status,
                applications.application_channel,
                applications.cv_version,
                applications.applied_at,
                applications.last_updated_at,

                jobs.id AS job_id,
                jobs.title,
                jobs.company,
                jobs.location,
                jobs.url,
                jobs.source,

                ai_evaluations.match_score,
                ai_evaluations.recommended_action,

                opportunity_assessments.final_action,
                opportunity_assessments.opportunity_score,
                opportunity_assessments.priority

            FROM applications

            JOIN jobs
                ON applications.job_id =
                   jobs.id

            LEFT JOIN ai_evaluations
                ON applications.ai_evaluation_id =
                   ai_evaluations.id

            LEFT JOIN opportunity_assessments
                ON applications.job_id =
                   opportunity_assessments.job_id

            ORDER BY
                applications.last_updated_at DESC
            """
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

def list_application_events(
    application_id: int,
):
    """
    Mengambil seluruh riwayat event sebuah application.
    """

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                application_id,
                event_type,
                event_date,
                notes
            FROM application_events
            WHERE application_id = ?
            ORDER BY
                event_date ASC,
                id ASC
            """,
            (application_id,),
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]


if __name__ == "__main__":

    initialize_database()

    print(
        "Application Tracker database ready."
    )