from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.db.database import initialize_database
from backend.evaluator import evaluate_job
from backend.services.manual_job import prepare_manual_job, save_manual_job
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
from backend.services.opportunity_detail import get_opportunity_detail
from backend.services.job_matcher import match_jobs
from backend.services.process_opportunities import process_opportunities


app = FastAPI(
    title="AI Career Copilot API",
    description=(
        "API Engine untuk AI job matching, job source search, filtering, "
        "deadline protection, AI matching, geo eligibility, opportunity "
        "scoring, dan application preparation."
    ),
    version="2.2.0",
)


@app.on_event("startup")
def startup_event():
    initialize_database()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ai-job-matcher-agent.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class SearchRequest(BaseModel):
    keyword: str
    location: str = ""
    per_source_limit: int = 10
    filter_limit: int = 11
    execute_ai: bool = True


class ApplicationRequest(BaseModel):
    job_id: int
    ai_evaluation_id: int | None = None
    application_channel: str = "MANUAL"
    cv_version: str = "v1"
    notes: str = ""


class ApplicationStatusRequest(BaseModel):
    status: str
    notes: str = ""


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "AI Career Copilot Engine",
        "version": "2.2.0",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-career-copilot",
    }


@app.post("/api/search")
def search_jobs_endpoint(payload: SearchRequest):
    """
    Menjalankan pipeline job search -> AI matching ->
    opportunity assessment.
    Tidak melakukan auto-apply.
    """
    if not payload.keyword.strip():
        raise HTTPException(
            status_code=400,
            detail="keyword tidak boleh kosong.",
        )

    if payload.per_source_limit < 1:
        raise HTTPException(
            status_code=400,
            detail="per_source_limit harus minimal 1.",
        )

    if payload.filter_limit < 1:
        raise HTTPException(
            status_code=400,
            detail="filter_limit harus minimal 1.",
        )

    try:
        results = match_jobs(
            keyword=payload.keyword.strip(),
            location=payload.location.strip(),
            per_source_limit=payload.per_source_limit,
            filter_limit=payload.filter_limit,
            execute_ai=payload.execute_ai,
        )

        opportunities = (
            process_opportunities()
            if payload.execute_ai
            else []
        )

        return {
            "status": "ok",
            "count": len(results),
            "jobs": results,
            "opportunities_count": len(opportunities),
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal menjalankan job search: {error}",
        )

@app.get("/api/debug/sources")
def debug_sources():
    import os

    return {
        "adzuna_app_id_present": bool(os.getenv("ADZUNA_APP_ID")),
        "adzuna_app_key_present": bool(os.getenv("ADZUNA_APP_KEY")),
        "gemini_api_key_present": bool(os.getenv("GEMINI_API_KEY")),
    }

@app.get("/api/debug/source-connectivity")
def debug_source_connectivity():
    import requests

    results = {}

    for name, url in {
        "remoteok": "https://remoteok.com/api",
        "adzuna": "https://api.adzuna.com/v1/api/jobs/gb/search/1",
    }.items():
        try:
            response = requests.get(url, timeout=15)
            results[name] = {
                "status_code": response.status_code,
                "content_length": len(response.content),
            }
        except Exception as error:
            results[name] = {
                "error": str(error),
            }

    return results

@app.get("/api/debug/source-diagnostics")
def debug_source_diagnostics():
    from backend.services.sources.registry import get_job_sources

    results = []

    for source in get_job_sources():
        entry = {
            "source": source.name,
            "raw_count": None,
            "search_count": None,
            "error": None,
        }

        try:
            if source.name == "remoteok":
                raw_jobs = source._fetch_jobs()
            elif source.name == "adzuna":
                raw_jobs = source._fetch_jobs(
                    keyword="developer",
                    location="",
                    page=1,
                    limit=5,
                )
            else:
                raw_jobs = []

            entry["raw_count"] = len(raw_jobs)

            try:
                searched = source.search(
                    keyword="developer",
                    location="",
                    limit=5,
                )
                entry["search_count"] = len(searched)
            except Exception as error:
                entry["error"] = f"search: {error}"

        except Exception as error:
            entry["error"] = f"fetch: {error}"

        results.append(entry)

    return results


@app.post("/api/evaluate")
def evaluate_job_endpoint(payload: JobRequest):
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


@app.post("/api/manual-job")
def manual_job_endpoint(payload: ManualJobRequest):
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

    ai_result = evaluate_job(
        job.title,
        job.description,
    )

    if "error" in ai_result:
        raise HTTPException(
            status_code=500,
            detail=ai_result["error"],
        )

    deadline = getattr(job, "deadline", None)
    if deadline is None:
        deadline = getattr(job, "application_deadline", None)

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
        "application_deadline": deadline,
        "match_score": ai_result.get("match_score", 0),
        "fit_summary": ai_result.get("fit_summary", ""),
        "key_pros": ai_result.get("key_pros", []),
        "key_gaps": ai_result.get("key_gaps", []),
        "recommended_action": ai_result.get(
            "recommended_action", "Skip"
        ),
        "draft_outreach": ai_result.get(
            "draft_outreach", ""
        ),
        "_ai_provider": ai_result.get(
            "_ai_provider", "unknown"
        ),
        "_ai_model": ai_result.get(
            "_ai_model", "unknown"
        ),
    }

    try:
        database_job_id = save_manual_job(job)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal menyimpan manual job: {error}",
        )

    try:
        evaluation_id = save_ai_evaluation(
            job_id=database_job_id,
            result=combined,
            provider=combined.get("_ai_provider", "unknown"),
            model=combined.get("_ai_model", "unknown"),
            profile_version="v1",
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal menyimpan AI evaluation: {error}",
        )

    try:
        assessment = assess_job(combined)
        save_opportunity_assessment(
            job_id=database_job_id,
            assessment=assessment,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal membuat opportunity assessment: {error}",
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
            "provider": combined.get("_ai_provider", "unknown"),
            "model": combined.get("_ai_model", "unknown"),
            "match_score": combined.get("match_score", 0),
            "fit_summary": combined.get("fit_summary", ""),
            "key_pros": combined.get("key_pros", []),
            "key_gaps": combined.get("key_gaps", []),
            "recommended_action": combined.get(
                "recommended_action", "Skip"
            ),
            "draft_outreach": combined.get(
                "draft_outreach", ""
            ),
        },
        "opportunity": {
            "geo_status": assessment.get("geo_status"),
            "geo_confidence": assessment.get("geo_confidence"),
            "geo_reason": assessment.get("geo_reason"),
            "opportunity_score": assessment.get(
                "opportunity_score"
            ),
            "priority": assessment.get("priority"),
            "final_action": assessment.get("final_action"),
            "application_deadline": assessment.get(
                "application_deadline"
            ),
            "expired": assessment.get("expired", False),
        },
    }


@app.get("/api/notifications/opportunities")
def notification_opportunities_endpoint():
    try:
        opportunities = list_priority_opportunities(
            minimum_priority="LOW"
        )

        applications = list_applications()
        applied_job_ids = {
            application["job_id"]
            for application in applications
        }

        actionable = [
            opportunity
            for opportunity in opportunities
            if opportunity.get("id") not in applied_job_ids
            and opportunity.get("final_action")
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
                "Gagal mengambil notification opportunities: "
                f"{error}"
            ),
        )


@app.get("/api/opportunities/{job_id}/package")
def opportunity_package_endpoint(job_id: int):
    try:
        opportunity = get_opportunity_detail(job_id)

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
            detail=f"Gagal mengambil Apply Package: {error}",
        )


@app.post("/api/applications")
def create_application_endpoint(
    payload: ApplicationRequest,
):
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

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal menyimpan application: {error}",
        )


@app.get("/api/applications")
def applications_endpoint():
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
            detail=f"Gagal mengambil applications: {error}",
        )


@app.patch("/api/applications/{application_id}/status")
def update_application_status_endpoint(
    application_id: int,
    payload: ApplicationStatusRequest,
):
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
                f"Gagal mengubah application status: {error}"
            ),
        )
