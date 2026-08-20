from typing import List

from backend.services.sources.models import NormalizedJob
from backend.services.sources.registry import get_job_sources


def normalize_dedup_text(text: str) -> str:
    """
    Normalisasi teks untuk kebutuhan deduplication.

    Contoh:
        "AI & Automation Lead"
        "AI and Automation Lead"

    akan dianggap sama.
    """

    text = (text or "").lower()

    text = text.replace("&", " and ")

    return " ".join(text.split())


def search_all_sources(
    keyword: str,
    location: str = "",
    per_source_limit: int = 20,
) -> List[NormalizedJob]:
    """
    Mencari lowongan dari semua source yang aktif.

    Pipeline:

        Source 1
        Source 2
        Source 3
             ↓
        Combine
             ↓
        Deduplicate
             ↓
        Unique jobs
    """

    sources = get_job_sources()

    all_jobs: List[NormalizedJob] = []

    for source in sources:

        print(
            f"[SOURCE] Searching {source.name} "
            f"for '{keyword}'..."
        )

        try:

            jobs = source.search(
                keyword=keyword,
                location=location,
                limit=per_source_limit,
            )

            print(
                f"[SOURCE] {source.name}: "
                f"{len(jobs)} jobs"
            )

            all_jobs.extend(jobs)

        except Exception as error:

            print(
                f"[SOURCE] {source.name} FAILED: "
                f"{error}"
            )

    unique_jobs = deduplicate_jobs(
        all_jobs
    )

    print(
        f"[DEDUP] {len(all_jobs)} raw jobs "
        f"-> {len(unique_jobs)} unique jobs"
    )

    return unique_jobs


def build_logical_dedup_key(
    job: NormalizedJob,
) -> str:
    """
    Membuat key logical untuk mendeteksi job yang sama.

    Kita tidak hanya menggunakan URL atau source_job_id
    karena beberapa job source bisa mempunyai ID/URL berbeda
    untuk lowongan yang sama tetapi lokasi berbeda.

    Contoh:

        AI & Automation Lead
        Sword Group
        Glasgow

    dan

        AI & Automation Lead
        Sword Group
        London

    dianggap sebagai satu opportunity yang sama.

    Location TIDAK digunakan sebagai bagian utama key.
    """

    source = normalize_dedup_text(
        job.source
    )

    company = normalize_dedup_text(
        job.company
    )

    title = normalize_dedup_text(
        job.title
    )

    return (
        f"{source}|"
        f"{company}|"
        f"{title}"
    )


def remote_status_priority(
    status: str,
) -> int:
    """
    Menentukan metadata remote mana yang lebih kuat
    ketika dua duplicate job digabung.
    """

    priorities = {
        "FULLY_REMOTE": 5,
        "REMOTE_FIRST": 4,
        "HYBRID": 3,
        "ONSITE": 2,
        "UNKNOWN": 1,
    }

    return priorities.get(
        status,
        0,
    )


def merge_duplicate_job(
    existing: NormalizedJob,
    duplicate: NormalizedJob,
) -> NormalizedJob:
    """
    Menggabungkan dua record yang dianggap job yang sama.

    Record pertama tetap menjadi basis.

    Tetapi metadata yang lebih baik dari duplicate
    akan digunakan jika tersedia.
    """

    # ==========================================================
    # REMOTE STATUS
    # ==========================================================

    existing_priority = remote_status_priority(
        existing.remote_status
    )

    duplicate_priority = remote_status_priority(
        duplicate.remote_status
    )

    if duplicate_priority > existing_priority:

        existing.remote_status = (
            duplicate.remote_status
        )

        existing.remote_confidence = (
            duplicate.remote_confidence
        )

    elif (
        existing.remote_confidence == "UNKNOWN"
        and duplicate.remote_confidence != "UNKNOWN"
    ):

        existing.remote_confidence = (
            duplicate.remote_confidence
        )

    # ==========================================================
    # LOCATION
    # ==========================================================

    # Jika record pertama tidak punya location,
    # gunakan location dari duplicate.
    if (
        not existing.location
        and duplicate.location
    ):

        existing.location = duplicate.location

    # ==========================================================
    # DESCRIPTION
    # ==========================================================

    # Gunakan description yang lebih panjang.
    if len(
        duplicate.description or ""
    ) > len(
        existing.description or ""
    ):

        existing.description = (
            duplicate.description
        )

    # ==========================================================
    # URL
    # ==========================================================

    if (
        not existing.url
        and duplicate.url
    ):

        existing.url = duplicate.url

    # ==========================================================
    # SALARY
    # ==========================================================

    if (
        existing.salary_min is None
        and duplicate.salary_min is not None
    ):

        existing.salary_min = (
            duplicate.salary_min
        )

    if (
        existing.salary_max is None
        and duplicate.salary_max is not None
    ):

        existing.salary_max = (
            duplicate.salary_max
        )

    # ==========================================================
    # DEADLINE
    # ==========================================================

    if (
        not existing.deadline
        and duplicate.deadline
    ):

        existing.deadline = (
            duplicate.deadline
        )

    # ==========================================================
    # TAGS
    # ==========================================================

    existing_tags = (
        existing.tags or []
    )

    duplicate_tags = (
        duplicate.tags or []
    )

    merged_tags = list(
        dict.fromkeys(
            existing_tags
            + duplicate_tags
        )
    )

    existing.tags = merged_tags

    return existing


def deduplicate_jobs(
    jobs: List[NormalizedJob],
) -> List[NormalizedJob]:
    """
    Menghapus duplicate jobs.

    Strategi:

    1. Gunakan logical identity:
       source + company + title

    2. Location tidak digunakan sebagai key.

       Dengan demikian:

       Sword Group
       AI & Automation Lead
       Glasgow

       Sword Group
       AI & Automation Lead
       London

       Sword Group
       AI & Automation Lead
       Manchester

       akan menjadi satu opportunity.

    3. Jika duplicate ditemukan, metadata terbaik
       akan digabungkan ke record pertama.
    """

    unique_jobs: List[NormalizedJob] = []

    seen = {}

    for job in jobs:

        # ======================================================
        # LOGICAL KEY
        # ======================================================

        key = build_logical_dedup_key(
            job
        )

        # ======================================================
        # NEW JOB
        # ======================================================

        if key not in seen:

            seen[key] = len(
                unique_jobs
            )

            unique_jobs.append(
                job
            )

            continue

        # ======================================================
        # DUPLICATE JOB
        # ======================================================

        existing_index = seen[key]

        existing_job = unique_jobs[
            existing_index
        ]

        unique_jobs[
            existing_index
        ] = merge_duplicate_job(
            existing_job,
            job,
        )

    return unique_jobs


if __name__ == "__main__":

    jobs = search_all_sources(
        keyword="AI Automation",
        per_source_limit=10,
    )

    print()
    print("=" * 80)
    print(
        f"TOTAL UNIQUE JOBS: {len(jobs)}"
    )
    print("=" * 80)

    for index, job in enumerate(
        jobs,
        start=1,
    ):

        print()
        print(
            f"JOB #{index}"
        )

        print(
            f"Source   : {job.source}"
        )

        print(
            f"Title    : {job.title}"
        )

        print(
            f"Company  : {job.company}"
        )

        print(
            f"Location : {job.location}"
        )

        print(
            f"Remote   : {job.remote_status}"
        )

        print(
            f"URL      : {job.url}"
        )