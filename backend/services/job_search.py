import os
import requests
from pathlib import Path
from dotenv import load_dotenv

from backend.services.sources.remoteok import RemoteOKSource


# ============================================================
# ENVIRONMENT
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
    raise ValueError(
        "ADZUNA_APP_ID atau ADZUNA_APP_KEY belum ditemukan di backend/.env"
    )


# ============================================================
# ADZUNA SEARCH
# ============================================================

def search_jobs(
    keyword: str,
    country: str = "gb",
    location: str = "",
    page: int = 1,
    results_per_page: int = 10,
) -> list:
    """
    Mengambil lowongan dari Adzuna Job Search API.
    """

    if not keyword or not keyword.strip():
        raise ValueError(
            "Keyword pekerjaan tidak boleh kosong."
        )

    url = (
        f"https://api.adzuna.com/v1/api/jobs/"
        f"{country}/search/{page}"
    )

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": results_per_page,
        "what": keyword.strip(),
        "content-type": "application/json",
    }

    if location and location.strip():
        params["where"] = location.strip()

    try:
        response = requests.get(
            url,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        jobs = []

        for job in data.get("results", []):
            jobs.append(
                {
                    "id": job.get("id"),
                    "title": job.get("title"),
                    "company": job.get(
                        "company",
                        {}
                    ).get("display_name"),
                    "location": job.get(
                        "location",
                        {}
                    ).get("display_name"),
                    "description": job.get(
                        "description"
                    ),
                    "salary_min": job.get(
                        "salary_min"
                    ),
                    "salary_max": job.get(
                        "salary_max"
                    ),
                    "url": job.get(
                        "redirect_url"
                    ),
                    "created": job.get(
                        "created"
                    ),
                }
            )

        return jobs

    except requests.RequestException as error:
        raise RuntimeError(
            f"Gagal mengambil data dari Adzuna: {error}"
        )


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_jobs(jobs: list) -> list:
    """
    Menghapus lowongan duplikat berdasarkan ID job.
    Jika ID tidak tersedia, gunakan URL sebagai fallback.
    """

    unique_jobs = []
    seen = set()

    for job in jobs:

        job_id = job.get("id")
        job_url = job.get("url")

        unique_key = job_id or job_url

        if not unique_key:
            continue

        if unique_key in seen:
            continue

        seen.add(unique_key)
        unique_jobs.append(job)

    return unique_jobs


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_jobs(jobs: list) -> list:
    """
    Membersihkan data agar format internal aplikasi konsisten.
    """

    normalized = []

    for job in jobs:

        normalized.append(
            {
                "id": (
                    str(job.get("id"))
                    if job.get("id") is not None
                    else None
                ),

                "title": (
                    job.get("title") or ""
                ).strip(),

                "company": (
                    job.get("company") or ""
                ).strip(),

                "location": (
                    job.get("location") or ""
                ).strip(),

                "description": (
                    job.get("description") or ""
                ).strip(),

                "salary_min": job.get(
                    "salary_min"
                ),

                "salary_max": job.get(
                    "salary_max"
                ),

                "url": (
                    job.get("url") or ""
                ).strip(),

                "created": job.get(
                    "created"
                ),
            }
        )

    return normalized


# ============================================================
# ADZUNA PIPELINE
# ============================================================

def prepare_jobs(
    keyword: str,
    country: str = "gb",
    location: str = "",
    page: int = 1,
    results_per_page: int = 10,
) -> list:
    """
    Pipeline Adzuna:

    Adzuna
       ↓
    Normalize
       ↓
    Deduplicate
    """

    raw_jobs = search_jobs(
        keyword=keyword,
        country=country,
        location=location,
        page=page,
        results_per_page=results_per_page,
    )

    normalized_jobs = normalize_jobs(
        raw_jobs
    )

    unique_jobs = deduplicate_jobs(
        normalized_jobs
    )

    return unique_jobs


# ============================================================
# MULTI SOURCE PIPELINE
# ============================================================

def prepare_multi_source_jobs(
    keyword: str,
    country: str = "gb",
    location: str = "",
    page: int = 1,
    results_per_page: int = 10,
) -> list:
    """
    Mengambil lowongan dari:

    1. Adzuna
    2. RemoteOK

    Kemudian menggabungkannya dalam format
    dictionary yang kompatibel dengan
    job_filter.py.
    """

    all_jobs = []

    # --------------------------------------------------------
    # ADZUNA
    # --------------------------------------------------------

    try:

        adzuna_jobs = prepare_jobs(
            keyword=keyword,
            country=country,
            location=location,
            page=page,
            results_per_page=results_per_page,
        )

        for job in adzuna_jobs:

            job["source"] = "adzuna"

            all_jobs.append(job)

        print(
            f"[Adzuna] {len(adzuna_jobs)} jobs"
        )

    except Exception as error:

        print(
            f"[Adzuna] ERROR: {error}"
        )

    # --------------------------------------------------------
    # REMOTEOK
    # --------------------------------------------------------

    try:

        remoteok = RemoteOKSource()

        remoteok_jobs = remoteok.search(
            keyword=keyword,
            location=location,
            limit=results_per_page,
        )

        for job in remoteok_jobs:

            # NormalizedJob → dictionary
            if hasattr(job, "__dict__"):
                job = dict(job.__dict__)

            job.setdefault(
                "source",
                "remoteok",
            )

            job.setdefault(
                "remote_status",
                "FULLY_REMOTE",
            )

            all_jobs.append(job)

        print(
            f"[RemoteOK] {len(remoteok_jobs)} jobs"
        )

    except Exception as error:

        print(
            f"[RemoteOK] ERROR: {error}"
        )

    # --------------------------------------------------------
    # DEDUPLICATION
    # --------------------------------------------------------

    unique_jobs = []
    seen = set()

    for job in all_jobs:

        source = job.get(
            "source",
            "unknown",
        )

        job_id = job.get("id")
        job_url = job.get("url")

        if job_id:

            unique_key = (
                f"{source}:{job_id}"
            )

        elif job_url:

            unique_key = (
                f"{source}:{job_url}"
            )

        else:

            continue

        if unique_key in seen:
            continue

        seen.add(unique_key)

        unique_jobs.append(job)

    return unique_jobs


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\nTesting Multi Source Search...\n"
    )

    jobs = prepare_multi_source_jobs(
        keyword="AI Automation",
        country="gb",
        results_per_page=5,
    )

    print(
        f"\nTOTAL JOBS: {len(jobs)}\n"
    )

    for index, job in enumerate(
        jobs,
        start=1,
    ):

        print(
            f"{index}. "
            f"[{job.get('source')}] "
            f"{job.get('title')} - "
            f"{job.get('company')}"
        )