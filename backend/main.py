from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.evaluator import evaluate_job

from backend.services.manual_job import (
    prepare_manual_job,
    save_manual_job,
)

from backend.services.application_tracker import (
    save_ai_evaluation,
    create_application,
    list_applications,
    update_application_status,
)

from backend.services.opportunity_service import (
    assess_job,
    save_opportunity_assessment,
    list_priority_opportunities,
)

from backend.services.opportunity_detail import (
    get_opportunity_detail,
)

app = FastAPI(
    title="AI Career Copilot API",
    description=(
        "API Engine untuk AI job matching, "
        "manual job analysis, geo eligibility, "
        "opportunity scoring, dan application preparation."
    ),
    version="2.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class JobRequest(BaseModel):
    job_title: str
    job_description: str


class ManualJobRequest(BaseModel):
    source: str
    title: str
    company: str
    location: str = ""
    description: str
    url: str = ""


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "AI Career Copilot Engine",
        "version": "2.0.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-career-copilot",
    }


# ============================================================
# LEGACY SINGLE JOB
# ============================================================

@app.post("/api/evaluate")
def evaluate_job_endpoint(
    payload: JobRequest,
):
    if not payload.job_title.strip():
        raise HTTPException(
            status_code=400,
            detail="job_title tidak boleh kosong.",
        )

    if not payload.job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="job_description tidak boleh kosong.",
        )

    result = evaluate_job(
        payload.job_title,
        payload.job_description,
    )

    if "error" in result:
        raise HTTPException(
            status_code=500,
            detail=result["error"],
        )

    return result


# ============================================================
# MANUAL JOB
# ============================================================

@app.post("/api/manual-job")
def manual_job_endpoint(
    payload: ManualJobRequest,
):
    if not payload.source.strip():
        raise HTTPException(
            status_code=400,
            detail="source tidak boleh kosong.",
        )

    if not payload.title.strip():
        raise HTTPException(
            status_code=400,
            detail="title tidak boleh kosong.",
        )

    if not payload.company.strip():
        raise HTTPException(
            status_code=400,
            detail="company tidak boleh kosong.",
        )

    if not payload.description.strip():
        raise HTTPException(
            status_code=400,
            detail="description tidak boleh kosong.",
        )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    try:
        job = prepare_manual_job(
            {
                "source": payload.source,
                "title": payload.title,
                "company": payload.company,
                "location": payload.location,
                "description": payload.description,
                "url": payload.url,
            }
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    # --------------------------------------------------------
    # AI Evaluation
    # --------------------------------------------------------

    ai_result = evaluate_job(
        job.title,
        job.description,
    )

    if "error" in ai_result:
        raise HTTPException(
            status_code=500,
            detail=ai_result["error"],
        )

    combined = {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "url": job.url,
        "source": job.source,
        "source_job_id": job.source_job_id,
        "remote_status": job.remote_status,
        "remote_confidence": job.remote_confidence,
        "match_score": ai_result.get(
            "match_score",
            0,
        ),
        "fit_summary": ai_result.get(
            "fit_summary",
            "",
        ),
        "key_pros": ai_result.get(
            "key_pros",
            [],
        ),
        "key_gaps": ai_result.get(
            "key_gaps",
            [],
        ),
        "recommended_action": ai_result.get(
            "recommended_action",
            "Skip",
        ),
        "draft_outreach": ai_result.get(
            "draft_outreach",
            "",
        ),
        "_ai_provider": ai_result.get(
            "_ai_provider",
            "unknown",
        ),
        "_ai_model": ai_result.get(
            "_ai_model",
            "unknown",
        ),
    }

    # --------------------------------------------------------
    # Save job
    # --------------------------------------------------------

    try:
        database_job_id = save_manual_job(job)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Gagal menyimpan manual job: {error}"
            ),
        )

    # --------------------------------------------------------
    # Save AI evaluation
    # --------------------------------------------------------

    try:
        evaluation_id = save_ai_evaluation(
            job_id=database_job_id,
            result=combined,
            provider=combined.get(
                "_ai_provider",
                "unknown",
            ),
            model=combined.get(
                "_ai_model",
                "unknown",
            ),
            profile_version="v1",
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Gagal menyimpan AI evaluation: {error}"
            ),
        )

    # --------------------------------------------------------
    # Opportunity
    # --------------------------------------------------------

    try:
        assessment = assess_job(combined)

        save_opportunity_assessment(
            job_id=database_job_id,
            assessment=assessment,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Gagal membuat opportunity assessment: {error}"
            ),
        )

    return {
        "status": "analyzed",

        "job": {
            "database_id": database_job_id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "source": job.source,
            "url": job.url,
        },

        "ai": {
            "evaluation_id": evaluation_id,
            "provider": combined.get(
                "_ai_provider",
                "unknown",
            ),
            "model": combined.get(
                "_ai_model",
                "unknown",
            ),
            "match_score": combined.get(
                "match_score",
                0,
            ),
            "fit_summary": combined.get(
                "fit_summary",
                "",
            ),
            "key_pros": combined.get(
                "key_pros",
                [],
            ),
            "key_gaps": combined.get(
                "key_gaps",
                [],
            ),
            "recommended_action": combined.get(
                "recommended_action",
                "Skip",
            ),
            "draft_outreach": combined.get(
                "draft_outreach",
                "",
            ),
        },

        "opportunity": {
            "geo_status": assessment.get(
                "geo_status",
            ),
            "geo_confidence": assessment.get(
                "geo_confidence",
            ),
            "geo_reason": assessment.get(
                "geo_reason",
            ),
            "opportunity_score": assessment.get(
                "opportunity_score",
            ),
            "priority": assessment.get(
                "priority",
            ),
            "final_action": assessment.get(
                "final_action",
            ),
        },
    }

    # ============================================================
    # OPPORTUNITIES
    # ============================================================

@app.get("/api/opportunities")
def opportunities_endpoint():
    """
    Mengambil daftar opportunity dari database.

    Tidak memanggil AI.
    """

    try:
        opportunities = list_priority_opportunities(
            minimum_priority="LOW"
        )

        return {
            "status": "ok",
            "count": len(opportunities),
            "opportunities": opportunities,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Gagal mengambil opportunities: {error}"
            ),
        )

    # ============================================================
    # APPLY PACKAGE
    # ============================================================

@app.get("/api/opportunities/{job_id}/package")
def opportunity_package_endpoint(
    job_id: int,
):
    """
    Mengambil detail lengkap opportunity untuk
    Apply Package.

    Tidak memanggil AI.
    """

    try:
        opportunity = get_opportunity_detail(
            job_id
        )

        if opportunity is None:
            raise HTTPException(
                status_code=404,
                detail="Opportunity tidak ditemukan.",
            )

        return {
            "status": "ok",
            "opportunity": opportunity,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Gagal mengambil Apply Package: {error}"
            ),
        )

    # ============================================================
    # MARK AS APPLIED
    # ============================================================

class ApplicationRequest(BaseModel):
    job_id: int
    ai_evaluation_id: int | None = None
    application_channel: str = "MANUAL"
    cv_version: str = "v1"
    notes: str = ""


@app.post("/api/applications")
def create_application_endpoint(
    payload: ApplicationRequest,
):
    """
    Menandai job sebagai sudah dilamar.

    Tidak memanggil AI.
    """

    try:
        application_id = create_application(
            job_id=payload.job_id,
            ai_evaluation_id=payload.ai_evaluation_id,
            application_channel=payload.application_channel,
            cv_version=payload.cv_version,
            notes=payload.notes,
        )

        return {
            "status": "applied",
            "application_id": application_id,
            "job_id": payload.job_id,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Gagal menyimpan application: {error}"
            ),
        )
    # ============================================================
    # APPLICATIONS
    # ============================================================

@app.get("/api/applications")
def applications_endpoint():
    """
    Mengambil semua application yang sudah dicatat.

    Tidak memanggil AI.
    """

    try:
        applications = list_applications()

        return {
            "status": "ok",
            "count": len(applications),
            "applications": applications,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Gagal mengambil applications: {error}"
            ),
        )

    # ============================================================
    # UPDATE APPLICATION STATUS
    # ============================================================

class ApplicationStatusRequest(BaseModel):
    status: str
    notes: str = ""


@app.patch("/api/applications/{application_id}/status")
def update_application_status_endpoint(
    application_id: int,
    payload: ApplicationStatusRequest,
    ):
    """
    Mengubah status application dan mencatat event.
    Tidak memanggil AI.
    """

    try:
        update_application_status(
            application_id=application_id,
            status=payload.status,
            notes=payload.notes,
        )

        return {
            "status": "ok",
            "application_id": application_id,
            "new_status": payload.status,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Gagal mengubah status application: {error}"
            ),
        )

    # ============================================================
# NOTIFICATION OPPORTUNITIES
# ============================================================

@app.get("/api/notifications/opportunities")
def notification_opportunities_endpoint():
    """
    Mengambil opportunity yang membutuhkan perhatian manusia.

    Tidak melakukan auto-apply.
    Tidak memanggil AI.
    """

    try:
        opportunities = list_priority_opportunities(
            minimum_priority="LOW"
        )

        actionable = [
            opportunity
            for opportunity in opportunities
            if opportunity.get("final_action")
            in {
                "APPLY NOW",
                "APPLY WITH TAILORED CV",
                "VERIFY BEFORE APPLY",
            }
        ]

        return {
            "status": "ok",
            "count": len(actionable),
            "opportunities": actionable,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Gagal mengambil notification opportunities: {error}"
            ),
        )