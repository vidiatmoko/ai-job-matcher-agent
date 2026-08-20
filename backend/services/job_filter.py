from typing import List

from backend.candidate_profile import CANDIDATE_PROFILE
from backend.services.sources.models import NormalizedJob


ROLE_KEYWORDS = {
    "ai automation": 25,
    "ai automation engineer": 30,
    "automation engineer": 25,
    "automation developer": 25,
    "ai engineer": 20,
    "ai developer": 20,
    "python developer": 20,
    "llm engineer": 20,
    "ai workflow": 20,
    "workflow automation": 20,
    "ai agent": 15,
    "generative ai": 15,
    "genai engineer": 20,
    "rag": 15,
    "python": 8,
    "n8n": 10,
    "ai solutions": 20,
    "ai solutions builder": 25,
}


UNRELATED_TITLE_TERMS = {
    "firmware engineer": 40,
    "modem engineer": 40,
    "telephony engineer": 40,
    "senior data engineer": 30,
    "data engineer": 25,
    "sre": 30,
    "infrastructure engineer": 30,
    "change manager": 40,
    "project manager": 35,
    "sales manager": 40,
    "account manager": 35,
}


def normalize_text(text: str) -> str:
    """
    Normalisasi teks.

    "&" dianggap sebagai pemisah kata, bukan kata "and".

    Contoh:
        AI & Automation
        ->
        ai automation

        AI & Automation Engineer
        ->
        ai automation engineer
    """

    text = (text or "").lower()

    # "&" harus dianggap separator.
    text = text.replace("&", " ")

    # Rapikan whitespace.
    return " ".join(text.split())


def detect_remote_status(job: NormalizedJob) -> str:
    """
    Menentukan status remote dari metadata source atau teks job.

    Hasil:
        FULLY_REMOTE
        REMOTE_FIRST
        HYBRID
        ONSITE
        UNKNOWN
    """

    # ==========================================================
    # 1. SOURCE METADATA
    # ==========================================================

    if (
        job.remote_status
        and job.remote_status != "UNKNOWN"
        and job.remote_confidence != "UNKNOWN"
    ):
        return job.remote_status

    # ==========================================================
    # 2. TEXT ANALYSIS
    # ==========================================================

    title = normalize_text(job.title)
    description = normalize_text(job.description)
    location = normalize_text(job.location)

    text = f"{title} {description} {location}"

    # ==========================================================
    # FULLY REMOTE
    # ==========================================================

    fully_remote_terms = [
        "fully remote",
        "100% remote",
        "fully-remote",
        "remote only",
        "remote position",
        "remote role",
        "remote job",
        "work from home",
        "work-from-home",
        "home based",
        "home-based",
        "work from anywhere",
        "location independent",
    ]

    if any(term in text for term in fully_remote_terms):
        return "FULLY_REMOTE"

    # ==========================================================
    # REMOTE FIRST
    # ==========================================================

    remote_first_terms = [
        "remote-first",
        "remote first",
        "distributed team",
        "distributed",
        "remote friendly",
        "remote-friendly",
    ]

    if any(term in text for term in remote_first_terms):
        return "REMOTE_FIRST"

    # ==========================================================
    # HYBRID
    # ==========================================================

    hybrid_terms = [
        "hybrid",
        "hybrid working",
        "hybrid role",
        "hybrid position",
        "days in office",
        "days per week in office",
        "office and remote",
    ]

    if any(term in text for term in hybrid_terms):
        return "HYBRID"

    # ==========================================================
    # ONSITE
    # ==========================================================

    onsite_terms = [
        "onsite",
        "on-site",
        "on site",
        "office based",
        "office-based",
        "office based role",
        "office-based role",
        "in office",
        "work from office",
    ]

    if any(term in text for term in onsite_terms):
        return "ONSITE"

    return "UNKNOWN"


def calculate_role_relevance(job: NormalizedJob) -> int:
    """
    Mengukur kedekatan lowongan dengan target career kandidat.

    Ini BUKAN AI Match Score.

    Ini hanya pre-filter sebelum AI.

    Skor:
        0   = tidak relevan
        15+ = kandidat awal
        40+ = cukup relevan
        60+ = sangat relevan
        80+ = sangat kuat
        100 = maksimum
    """

    title = normalize_text(job.title)
    description = normalize_text(job.description)

    score = 0

    # ==========================================================
    # 1. EXACT TARGET ROLES DARI CANDIDATE PROFILE
    # ==========================================================

    for role in CANDIDATE_PROFILE.get(
        "target_roles",
        [],
    ):
        role_text = normalize_text(role)

        if not role_text:
            continue

        if role_text in title:
            score += 40

    # ==========================================================
    # 2. STRONG TITLE KEYWORDS
    # ==========================================================

    strong_title_keywords = {
        "ai automation engineer": 30,
        "ai automation": 28,
        "automation engineer": 28,
        "automation developer": 28,
        "ai engineer": 25,
        "ai developer": 25,
        "python developer": 25,
        "llm engineer": 25,
        "genai engineer": 25,
        "ai workflow": 25,
        "workflow automation": 25,
        "ai solutions builder": 25,
        "ai solutions": 20,
    }

    for keyword, weight in strong_title_keywords.items():

        if keyword in title:
            score += weight

    # ==========================================================
    # 3. SUPPORTING TITLE KEYWORDS
    # ==========================================================

    supporting_title_keywords = {
        "automation": 8,
        "artificial intelligence": 8,
        "ai": 6,
        "python": 6,
        "llm": 8,
        "rag": 8,
        "generative ai": 10,
        "genai": 10,
        "workflow": 6,
        "n8n": 10,
        "ai agent": 10,
        "automation specialist": 15,
        "automation consultant": 15,
        "automation lead": 12,
        "solutions developer": 8,
        "solutions engineer": 10,
    }

    supporting_title_bonus = 0

    for keyword, weight in supporting_title_keywords.items():

        if keyword in title:
            supporting_title_bonus += weight

    # Batasi bonus supaya title generic tidak melonjak.
    supporting_title_bonus = min(
        supporting_title_bonus,
        25,
    )

    score += supporting_title_bonus

    # ==========================================================
    # 4. SUPPORTING EVIDENCE DARI DESCRIPTION
    # ==========================================================

    supporting_terms = {
        "n8n": 4,
        "python": 4,
        "llm": 4,
        "rag": 4,
        "ai agent": 4,
        "workflow automation": 4,
        "generative ai": 4,
        "rest api": 3,
        "automation": 3,
        "machine learning": 3,
        "openai": 3,
        "langchain": 3,
        "webhook": 3,
        "api integration": 3,
    }

    description_bonus = 0

    for term, weight in supporting_terms.items():

        if term in description:
            description_bonus += weight

    # Description hanya supporting evidence.
    description_bonus = min(
        description_bonus,
        20,
    )

    score += description_bonus

    # ==========================================================
    # 5. PENALTI ROLE YANG JAUH DARI TARGET
    # ==========================================================

    for keyword, penalty in UNRELATED_TITLE_TERMS.items():

        if keyword in title:
            score -= penalty

    # ==========================================================
    # 6. SPECIAL CASE:
    # AI + AUTOMATION HARUS DIANGGAP KUAT
    # ==========================================================

    has_ai = (
        "ai" in title
        or "artificial intelligence" in title
    )

    has_automation = (
        "automation" in title
        or "automated" in title
    )

    if has_ai and has_automation:

        # Minimal score untuk kombinasi target utama.
        score = max(
            score,
            40,
        )

    # ==========================================================
    # 7. SPECIAL CASE:
    # AI AUTOMATION ENGINEER
    # ==========================================================

    if "ai automation engineer" in title:
        score = max(
            score,
            80,
        )

    # ==========================================================
    # FINAL BOUND
    # ==========================================================

    return max(
        0,
        min(score, 100),
    )


def calculate_local_relevance(
    job: NormalizedJob,
    role_score: int,
    remote_status: str,
) -> int:
    """
    Menghasilkan local relevance score sebelum AI.

    Ini BUKAN Match Score AI.
    """

    score = role_score

    # ==========================================================
    # 1. REMOTE BONUS
    # ==========================================================

    if remote_status == "FULLY_REMOTE":
        score += 15

    elif remote_status == "REMOTE_FIRST":
        score += 12

    # UNKNOWN tidak diberi bonus.
    # Kita tidak boleh menganggap UNKNOWN sebagai remote.

    # ==========================================================
    # 2. SKILL EVIDENCE
    # ==========================================================

    full_text = normalize_text(
        f"{job.title} "
        f"{job.description} "
        f"{' '.join(job.tags)}"
    )

    skill_terms = {
        "python": 3,
        "n8n": 5,
        "rag": 4,
        "llm": 4,
        "ai agent": 4,
        "rest api": 3,
        "webhooks": 3,
        "webhook": 3,
        "generative ai": 4,
        "automation": 3,
        "openai": 3,
        "langchain": 3,
    }

    skill_bonus = 0

    for skill, weight in skill_terms.items():

        if skill in full_text:
            skill_bonus += weight

    # Batasi bonus.
    score += min(
        skill_bonus,
        20,
    )

    return max(
        0,
        min(score, 100),
    )


def remote_priority(status: str) -> int:
    """
    Prioritas status remote untuk ranking.
    """

    if status == "FULLY_REMOTE":
        return 3

    if status == "REMOTE_FIRST":
        return 2

    if status == "UNKNOWN":
        return 1

    if status == "HYBRID":
        return 0

    if status == "ONSITE":
        return 0

    return 0


def filter_jobs(
    jobs: List[NormalizedJob],
    minimum_role_score: int = 15,
    minimum_local_score: int = 20,
    limit: int = 12,
    include_unknown_remote: bool = True,
) -> List[NormalizedJob]:
    """
    Filter utama sebelum AI.

    Rules:

    - Role relevansi harus cukup.
    - ONSITE dibuang.
    - HYBRID tidak masuk primary remote list.
    - UNKNOWN boleh masuk verification queue.
    - FULLY_REMOTE / REMOTE_FIRST mendapat prioritas tertinggi.
    """

    candidates: List[NormalizedJob] = []

    for job in jobs:

        # ======================================================
        # REMOTE
        # ======================================================

        remote_status = detect_remote_status(
            job
        )

        # ======================================================
        # ROLE SCORE
        # ======================================================

        role_score = calculate_role_relevance(
            job
        )

        # ======================================================
        # ROLE TERLALU JAUH
        # ======================================================

        if role_score < minimum_role_score:
            continue

        # ======================================================
        # ONSITE
        # ======================================================

        if remote_status == "ONSITE":
            continue

        # ======================================================
        # HYBRID
        # ======================================================

        if remote_status == "HYBRID":
            continue

        # ======================================================
        # UNKNOWN REMOTE
        # ======================================================

        if (
            remote_status == "UNKNOWN"
            and not include_unknown_remote
        ):
            continue

        # ======================================================
        # LOCAL SCORE
        # ======================================================

        local_score = calculate_local_relevance(
            job=job,
            role_score=role_score,
            remote_status=remote_status,
        )

        if local_score < minimum_local_score:
            continue

        # ======================================================
        # SAVE SCORING TO OBJECT
        # ======================================================

        job.remote_status = remote_status
        job.relevance_score = local_score

        candidates.append(job)

    # ==========================================================
    # RANKING
    # ==========================================================

    candidates.sort(
        key=lambda job: (
            remote_priority(
                job.remote_status
            ),
            job.relevance_score,
        ),
        reverse=True,
    )

    return candidates[:limit]


if __name__ == "__main__":

    from backend.services.source_search import (
        search_all_sources,
    )

    print(
        "Testing Unified Remote + Role Filter...\n"
    )

    jobs = search_all_sources(
        keyword="AI Automation",
        per_source_limit=10,
    )

    filtered = filter_jobs(
        jobs=jobs,
        minimum_role_score=15,
        minimum_local_score=20,
        limit=12,
        include_unknown_remote=True,
    )

    print("\n" + "=" * 80)
    print("FILTERED JOBS")
    print("=" * 80)

    print(f"Total source jobs : {len(jobs)}")

    print(f"Qualified jobs    : {len(filtered)}")

    for index, job in enumerate(
        filtered,
        start=1,
    ):

        role_score = calculate_role_relevance(
            job
        )

        print()
        print(f"#{index}")
        print("-" * 80)

        print(f"Source      : {job.source}")
        print(f"Title       : {job.title}")
        print(f"Company     : {job.company}")
        print(f"Remote      : {job.remote_status}")
        print(f"Confidence  : {job.remote_confidence}")
        print(f"Role Score  : {role_score}")
        print(f"Relevance   : {job.relevance_score}")
        print(f"URL         : {job.url}")