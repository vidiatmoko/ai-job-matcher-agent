import sys
from typing import List, Dict, Any

from backend.evaluator import evaluate_jobs_batch
from backend.services.ai_cache import (
    build_cache_key,
    get_cached_result,
    set_cached_result,
)
from backend.services.application_service import save_matched_job
from backend.services.application_tracker import save_ai_evaluation, save_job
from backend.services.job_filter import filter_jobs
from backend.services.source_search import search_all_sources
from backend.services.sources.models import NormalizedJob


def normalized_job_to_dict(
    job: NormalizedJob,
) -> Dict[str, Any]:
    return {
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
        "deadline": job.deadline,
        "local_relevance_score": job.relevance_score,
    }


def merge_ai_result(
    job: NormalizedJob,
    ai_result: Dict[str, Any],
) -> Dict[str, Any]:
    return {
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
        "deadline": job.deadline,
        "local_relevance_score": job.relevance_score,
        "match_score": ai_result.get("match_score", 0),
        "fit_summary": ai_result.get("fit_summary", ""),
        "key_pros": ai_result.get("key_pros", []),
        "key_gaps": ai_result.get("key_gaps", []),
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


def save_discovered_job(
    job: NormalizedJob,
) -> int:
    """
    Simpan/update job ke database walaupun AI belum
    menganalisisnya.
    """

    return save_job(
        {
            "source": job.source,
            "source_job_id": job.source_job_id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "url": job.url,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "created_at": job.created,
            "deadline": job.deadline,
            "remote_status": job.remote_status,
            "remote_confidence": job.remote_confidence,
        }
    )


def match_jobs(
    keyword: str,
    location: str = "",
    per_source_limit: int = 10,
    filter_limit: int = 11,
    execute_ai: bool = False,
) -> List[dict]:
    """
    Pipeline utama:

    Search
    -> Filter
    -> Save discovered jobs
    -> Cache
    -> Optional AI batch
    -> Ranking
    """

    print("=" * 80)
    print("AI CAREER COPILOT - MATCHING PIPELINE")
    print("=" * 80)

    # ========================================================
    # 1. SEARCH
    # ========================================================

    print("\n[1/6] SEARCHING JOB SOURCES...")

    jobs: List[NormalizedJob] = search_all_sources(
        keyword=keyword,
        location=location,
        per_source_limit=per_source_limit,
    )

    print(
        f"[SEARCH] Total unique jobs: {len(jobs)}"
    )

    if not jobs:
        return []

    # ========================================================
    # 2. FILTER
    # ========================================================

    print("\n[2/6] APPLYING LOCAL FILTER...")

    filtered_jobs = filter_jobs(
        jobs=jobs,
        minimum_role_score=15,
        minimum_local_score=20,
        limit=filter_limit,
        include_unknown_remote=True,
    )

    print(
        f"[FILTER] Jobs selected: {len(filtered_jobs)}"
    )

    if not filtered_jobs:
        return []

    # ========================================================
    # 3. SAVE DISCOVERED JOBS
    # ========================================================

    print("\n[3/6] SAVING DISCOVERED JOBS...")

    database_job_ids = {}

    for job in filtered_jobs:
        try:
            db_job_id = save_discovered_job(job)
            database_job_ids[str(job.id)] = db_job_id

        except Exception as error:
            print(
                f"[DATABASE] Failed saving "
                f"{job.title}: {error}"
            )

    print(
        f"[DATABASE] Saved/updated jobs: "
        f"{len(database_job_ids)}"
    )

    # ========================================================
    # 4. CACHE
    # ========================================================

    print("\n[4/6] CHECKING AI CACHE...")

    cached_results = {}
    jobs_needing_ai = []

    for job in filtered_jobs:

        cache_key = build_cache_key(
            job_id=job.id,
            title=job.title,
            description=job.description,
        )

        cached = get_cached_result(cache_key)

        if cached and "error" not in cached:
            cached_results[str(job.id)] = cached

            print(
                f"  CACHE HIT: {job.title}"
            )

        else:
            jobs_needing_ai.append(job)

            print(
                f"  CACHE MISS: {job.title}"
            )

    print(
        f"[CACHE] Hits: {len(cached_results)}"
    )
    print(
        f"[CACHE] Need AI: {len(jobs_needing_ai)}"
    )

    # ========================================================
    # SAFE MODE
    # ========================================================

    if not execute_ai:

        print(
            "\n[SAFE MODE] AI execution is disabled."
        )

        print(
            "Run with '--run' when you are ready "
            "to consume ONE batch AI request."
        )

        return []

    # ========================================================
    # 5. ONE AI BATCH REQUEST
    # ========================================================

    fresh_results = {}

    if jobs_needing_ai:

        print(
            "\n[5/6] RUNNING ONE AI BATCH..."
        )

        evaluator_input = [
            normalized_job_to_dict(job)
            for job in jobs_needing_ai
        ]

        batch_results = evaluate_jobs_batch(
            evaluator_input
        )

        for job, result in zip(
            jobs_needing_ai,
            batch_results,
        ):

            if "error" in result:
                print(
                    f"  [AI ERROR] {job.title}"
                )
                continue

            # Provider/model metadata.
            result.setdefault(
                "_ai_provider",
                "unknown",
            )
            result.setdefault(
                "_ai_model",
                "unknown",
            )

            job_id = str(job.id)

            fresh_results[job_id] = result

            cache_key = build_cache_key(
                job_id=job.id,
                title=job.title,
                description=job.description,
            )

            set_cached_result(
                cache_key,
                result
            )

    else:
        print(
            "\n[5/6] NO NEW AI REQUEST NEEDED."
        )

    # ========================================================
    # 6. MERGE + SAVE + RANK
    # ========================================================

    print(
        "\n[6/6] MERGING, SAVING AI RESULTS "
        "AND RANKING..."
    )

    matched_jobs = []

    for job in filtered_jobs:

        job_id = str(job.id)

        ai_result = (
            fresh_results.get(job_id)
            or cached_results.get(job_id)
        )

        if not ai_result:
            continue

        merged = merge_ai_result(
            job,
            ai_result,
        )

        try:
            db_job_id = database_job_ids.get(job_id)

            if db_job_id is not None:
                save_ai_evaluation(
                    job_id=db_job_id,
                    result=merged,
                    provider=merged.get(
                        "_ai_provider",
                        "unknown",
                    ),
                    model=merged.get(
                        "_ai_model",
                        "unknown",
                    ),
                    profile_version="v1",
                )

        except Exception as error:
            print(
                f"[DATABASE] AI result save failed "
                f"for {job.title}: {error}"
            )

        matched_jobs.append(merged)

    matched_jobs.sort(
        key=lambda job: (
            job.get("match_score", 0),
            job.get("local_relevance_score", 0),
        ),
        reverse=True,
    )

    print(
        f"\n[RESULT] Matched jobs: "
        f"{len(matched_jobs)}"
    )

    return matched_jobs


if __name__ == "__main__":

    execute_ai = "--run" in sys.argv

    results = match_jobs(
        keyword="AI Automation",
        location="",
        per_source_limit=10,
        filter_limit=11,
        execute_ai=execute_ai,
    )

    if not execute_ai:
        raise SystemExit(0)

    print("\n" + "=" * 80)
    print("TOP AI MATCHED JOBS")
    print("=" * 80)

    if not results:
        print("No AI-matched jobs available.")
        raise SystemExit(0)

    for index, job in enumerate(results, start=1):

        print()
        print(f"#{index}")
        print("-" * 80)
        print(f"Title       : {job['title']}")
        print(f"Company     : {job['company']}")
        print(f"Source      : {job['source']}")
        print(f"Location    : {job['location']}")
        print(
            f"Remote      : "
            f"{job['remote_status']} "
            f"({job['remote_confidence']})"
        )
        print(
            f"Local Score : "
            f"{job['local_relevance_score']}"
        )
        print(
            f"AI Match    : "
            f"{job['match_score']}%"
        )
        print(
            f"Provider    : "
            f"{job.get('_ai_provider', 'unknown')}"
        )
        print(
            f"Model       : "
            f"{job.get('_ai_model', 'unknown')}"
        )
        print(
            f"Action      : "
            f"{job['recommended_action']}"
        )
        print(
            f"URL         : {job['url']}"
        )
        print(
            f"Summary     : "
            f"{job['fit_summary']}"
        )