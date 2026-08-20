from typing import Dict, Any

from backend.services.application_tracker import (
    save_ai_evaluation,
    save_job,
)


def save_matched_job(
    job: Dict[str, Any],
) -> Dict[str, int]:
    """
    Menyimpan job dan hasil AI evaluation ke database.
    """

    database_job_id = save_job(job)

    provider = job.get(
        "_ai_provider",
        "unknown",
    )

    model = job.get(
        "_ai_model",
        "unknown",
    )

    evaluation_id = save_ai_evaluation(
        job_id=database_job_id,
        result=job,
        provider=provider,
        model=model,
        profile_version="v1",
    )

    return {
        "job_id": database_job_id,
        "evaluation_id": evaluation_id,
    }