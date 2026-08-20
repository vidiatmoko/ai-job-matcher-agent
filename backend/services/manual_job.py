import re
from typing import Dict, Any

from backend.services.sources.models import NormalizedJob
from backend.services.application_tracker import save_job


# ============================================================
# REMOTE DETECTION
# ============================================================

FULLY_REMOTE_TERMS = [
    "fully remote",
    "fully-remote",
    "remote only",
    "remote-only",
    "100% remote",
    "100% remote",
    "work from anywhere",
    "work anywhere",
    "worldwide remote",
    "remote worldwide",
    "global remote",
]


REMOTE_FIRST_TERMS = [
    "remote-first",
    "remote first",
    "remote first company",
    "remote-first company",
]


HYBRID_TERMS = [
    "hybrid",
    "hybrid role",
    "hybrid position",
    "hybrid working",
    "office and remote",
]


ONSITE_TERMS = [
    "on-site",
    "onsite",
    "on site",
    "office-based",
    "office based",
    "in office",
    "on premises",
]


def normalize_text(text: str) -> str:
    return " ".join(
        (text or "").lower().split()
    )


def detect_remote_status(
    location: str,
    description: str,
) -> Dict[str, str]:
    """
    Mendeteksi status kerja remote dari
    location + job description.

    Prioritas evidence:
        1. Fully remote
        2. Remote-first
        3. Hybrid
        4. Onsite
        5. Unknown
    """

    location_text = normalize_text(
        location
    )

    description_text = normalize_text(
        description
    )

    combined_text = " ".join(
        [
            location_text,
            description_text,
        ]
    )

    # ========================================================
    # FULLY REMOTE
    # ========================================================

    for term in FULLY_REMOTE_TERMS:
        if term in combined_text:
            return {
                "status": "FULLY_REMOTE",
                "confidence": "HIGH",
                "reason": (
                    f"Explicit remote signal: {term}"
                ),
            }

    # Location yang eksplisit hanya "remote".
    if location_text in {
        "remote",
        "remote, indonesia",
        "remote indonesia",
        "remote worldwide",
        "remote anywhere",
    }:
        return {
            "status": "FULLY_REMOTE",
            "confidence": "HIGH",
            "reason": (
                "Job location explicitly indicates remote work."
            ),
        }

    # ========================================================
    # REMOTE FIRST
    # ========================================================

    for term in REMOTE_FIRST_TERMS:
        if term in combined_text:
            return {
                "status": "REMOTE_FIRST",
                "confidence": "HIGH",
                "reason": (
                    f"Remote-first signal: {term}"
                ),
            }

    # ========================================================
    # HYBRID
    # ========================================================

    for term in HYBRID_TERMS:
        if term in combined_text:
            return {
                "status": "HYBRID",
                "confidence": "HIGH",
                "reason": (
                    f"Hybrid signal: {term}"
                ),
            }

    # ========================================================
    # ONSITE
    # ========================================================

    for term in ONSITE_TERMS:
        if term in combined_text:
            return {
                "status": "ONSITE",
                "confidence": "HIGH",
                "reason": (
                    f"Onsite signal: {term}"
                ),
            }

    # ========================================================
    # UNKNOWN
    # ========================================================

    return {
        "status": "UNKNOWN",
        "confidence": "LOW",
        "reason": (
            "No reliable remote/onsite signal found."
        ),
    }


# ============================================================
# MANUAL JOB NORMALIZATION
# ============================================================

def normalize_manual_job(
    *,
    source: str,
    title: str,
    company: str,
    location: str,
    description: str,
    url: str = "",
) -> NormalizedJob:
    """
    Mengubah job manual menjadi NormalizedJob.

    Cocok untuk:
        LinkedIn
        Upwork
        Glints
        Wellfound
        Dealls
        Tech in Asia
        Freelancer
    """

    if not title.strip():
        raise ValueError(
            "Job title tidak boleh kosong."
        )

    if not description.strip():
        raise ValueError(
            "Job description tidak boleh kosong."
        )

    manual_id = (
        f"manual:"
        f"{source.strip().lower()}:"
        f"{title.strip().lower()}:"
        f"{company.strip().lower()}"
    )

    remote = detect_remote_status(
        location=location,
        description=description,
    )

    return NormalizedJob(
        id=manual_id,

        title=title.strip(),

        company=company.strip(),

        location=location.strip(),

        description=description.strip(),

        url=url.strip(),

        salary_min=None,

        salary_max=None,

        created=None,

        source=source.strip().lower(),

        source_job_id=manual_id,

        remote_status=remote["status"],

        remote_confidence=remote["confidence"],

        relevance_score=0.0,

        tags=[],
    )


# ============================================================
# SAVE
# ============================================================

def save_manual_job(
    job: NormalizedJob,
) -> int:
    """
    Menyimpan manual job ke SQLite.
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

            "remote_status": job.remote_status,

            "remote_confidence": job.remote_confidence,
        }
    )


# ============================================================
# FRONTEND/API PREPARATION
# ============================================================

def prepare_manual_job(
    data: Dict[str, Any],
) -> NormalizedJob:
    """
    Menyiapkan data manual dari frontend/API.
    """

    required_fields = [
        "source",
        "title",
        "company",
        "description",
    ]

    missing = [
        field
        for field in required_fields
        if not str(
            data.get(field, "")
        ).strip()
    ]

    if missing:
        raise ValueError(
            "Field wajib belum diisi: "
            + ", ".join(missing)
        )

    return normalize_manual_job(
        source=data["source"],
        title=data["title"],
        company=data["company"],
        location=data.get(
            "location",
            "",
        ),
        description=data["description"],
        url=data.get(
            "url",
            "",
        ),
    )


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    sample_jobs = [
        {
            "source": "glints",
            "title": "AI Automation Engineer",
            "company": "Example Company",
            "location": "Remote, Indonesia",
            "description": (
                "We are looking for an AI Automation "
                "Engineer with Python, n8n, REST APIs, "
                "LLM and RAG experience."
            ),
            "url": "https://example.com/job",
        },
        {
            "source": "linkedin",
            "title": "AI Engineer",
            "company": "Example Company",
            "location": "Hybrid, Jakarta",
            "description": (
                "Hybrid working model with office presence."
            ),
            "url": "https://example.com/job2",
        },
        {
            "source": "upwork",
            "title": "AI Automation Freelancer",
            "company": "Client",
            "location": "Worldwide",
            "description": (
                "Work from anywhere on a fully remote basis."
            ),
            "url": "https://example.com/job3",
        },
    ]

    print("=" * 70)
    print("MANUAL JOB REMOTE DETECTION TEST")
    print("=" * 70)

    for sample in sample_jobs:

        job = prepare_manual_job(
            sample
        )

        print()
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
            f"Confidence: {job.remote_confidence}"
        )