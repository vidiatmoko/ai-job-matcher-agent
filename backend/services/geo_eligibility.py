from typing import Dict, Any


# ============================================================
# GEOGRAPHIC SIGNALS
# ============================================================

# Sinyal kuat bahwa perusahaan menerima kandidat
# secara global / lintas negara.
#
# CATATAN:
# Kata "global" saja TIDAK cukup untuk menyatakan
# kandidat Indonesia eligible.
GLOBAL_REMOTE_TERMS = [
    "worldwide",
    "global remote",
    "remote anywhere",
    "work from anywhere",
    "work anywhere",
    "hire globally",
    "hiring globally",
    "global hiring",
    "global talent",
    "international team",
    "international teams",
    "international operations",
    "globally distributed",
    "distributed workforce",
    "distributed team",
    "around the world",
    "across the world",
    "all over the world",
    "fully remote worldwide",
    "remote worldwide",
    "remote around the world",
    "all locations",
    "multiple countries",
]


# Sinyal yang sangat membantu kandidat Indonesia.
APAC_TERMS = [
    "asia",
    "asia pacific",
    "apac",
    "indonesia",
    "southeast asia",
    "south east asia",
]


# Region yang bukan berarti kandidat Indonesia otomatis eligible,
# tetapi juga bukan hard restriction.
REGION_VERIFICATION_TERMS = [
    "emea",
    "europe",
    "european",
    "latam",
    "latin america",
    "middle east",
    "africa",
    "americas",
    "north america",
]


# Hard restriction eksplisit.
RESTRICTED_TERMS = [
    "us only",
    "usa only",
    "united states only",
    "canada only",
    "uk only",
    "united kingdom only",
    "europe only",
    "eu only",
    "australia only",
    "new zealand only",
    "singapore only",
]


# Country-specific location yang untuk sementara
# diperlakukan sebagai restriction.
RESTRICTED_LOCATION_NAMES = [
    "canada",
    "united states",
    "usa",
    "united kingdom",
    "uk",
    "australia",
    "new zealand",
    "singapore",
]


WORK_AUTH_TERMS = [
    "must be authorized to work",
    "must have authorization to work",
    "right to work required",
    "work authorization required",
    "visa sponsorship unavailable",
    "visa sponsorship not available",
    "without visa sponsorship",
]


# Preference regional bukan restriction.
PREFERENCE_TERMS = [
    "prioritize applications from",
    "we will prioritize applications from",
    "preferred locations",
    "preferred location",
    "priority locations",
    "applications from the following locations",
]


def normalize_text(text: str) -> str:
    return " ".join(
        (text or "").lower().split()
    )


def assess_geo_eligibility(
    job: Dict[str, Any],
) -> Dict[str, str]:
    """
    Geographic eligibility yang konservatif.

    Status:
        LIKELY_ELIGIBLE
        NEEDS_VERIFICATION
        RESTRICTED

    Confidence:
        HIGH
        MEDIUM
        LOW

    Prinsip:
        - Jangan menganggap remote = global.
        - Jangan menganggap region tertentu = Indonesia eligible.
        - Bukti global harus cukup kuat.
        - Jika tidak yakin, VERIFY.
    """

    title = normalize_text(
        job.get("title", "")
    )

    location = normalize_text(
        job.get("location", "")
    )

    description = normalize_text(
        job.get("description", "")
    )

    full_text = " ".join(
        [
            title,
            location,
            description,
        ]
    )

    # ========================================================
    # 1. HARD RESTRICTION DI LOCATION
    # ========================================================

    for country in RESTRICTED_LOCATION_NAMES:

        if location == country:

            return {
                "status": "RESTRICTED",
                "confidence": "HIGH",
                "reason": (
                    f"Job location is restricted to "
                    f"{country}."
                ),
            }

        if location.startswith(
            f"{country},"
        ):

            return {
                "status": "RESTRICTED",
                "confidence": "HIGH",
                "reason": (
                    f"Job location starts with "
                    f"restricted country: {country}."
                ),
            }

    # ========================================================
    # 2. HARD RESTRICTION DI FULL TEXT
    # ========================================================

    for term in RESTRICTED_TERMS:

        if term in full_text:

            return {
                "status": "RESTRICTED",
                "confidence": "HIGH",
                "reason": (
                    f"Explicit geographic restriction: "
                    f"{term}"
                ),
            }

    # ========================================================
    # 3. WORK AUTHORIZATION
    # ========================================================

    for term in WORK_AUTH_TERMS:

        if term in full_text:

            return {
                "status": "NEEDS_VERIFICATION",
                "confidence": "HIGH",
                "reason": (
                    "Work authorization requirement: "
                    f"{term}"
                ),
            }

    # ========================================================
    # 4. EXPLICIT GLOBAL REMOTE EVIDENCE
    # ========================================================
    #
    # HANYA gunakan phrase yang benar-benar menunjukkan
    # penerimaan kandidat lintas negara.
    #
    # Kata "global" saja sengaja tidak dimasukkan.
    # ========================================================

    global_hits = [
        term
        for term in GLOBAL_REMOTE_TERMS
        if term in full_text
    ]

    if global_hits:

        return {
            "status": "LIKELY_ELIGIBLE",
            "confidence": "HIGH",
            "reason": (
                "Global remote hiring evidence found: "
                f"{global_hits[0]}"
            ),
        }

    # ========================================================
    # 5. APAC / ASIA EVIDENCE
    # ========================================================

    for term in APAC_TERMS:

        if term in location:

            return {
                "status": "LIKELY_ELIGIBLE",
                "confidence": "HIGH",
                "reason": (
                    "Compatible Asia/APAC location: "
                    f"{term}"
                ),
            }

    # ========================================================
    # 6. REGIONAL LOCATION
    # ========================================================

    for term in REGION_VERIFICATION_TERMS:

        if term in location:

            return {
                "status": "NEEDS_VERIFICATION",
                "confidence": "MEDIUM",
                "reason": (
                    "Regional scope is specified as "
                    f"{term}, but Indonesia eligibility "
                    "is not explicit."
                ),
            }

    # ========================================================
    # 7. REGIONAL PREFERENCE
    # ========================================================

    preference_hits = [
        term
        for term in PREFERENCE_TERMS
        if term in description
    ]

    if preference_hits:

        return {
            "status": "NEEDS_VERIFICATION",
            "confidence": "MEDIUM",
            "reason": (
                "Regional location preference exists, "
                "but it is not an exclusive restriction."
            ),
        }

    # ========================================================
    # 8. UNKNOWN
    # ========================================================

    return {
        "status": "NEEDS_VERIFICATION",
        "confidence": "LOW",
        "reason": (
            "No sufficiently reliable geographic "
            "eligibility evidence was found."
        ),
    }


def calculate_opportunity_score(
    match_score: float,
    remote_status: str,
    remote_confidence: str,
    geo_status: str,
) -> float:
    """
    Opportunity score lokal.

    BUKAN AI Match Score.
    """

    score = float(
        match_score
    )

    # --------------------------------------------------------
    # Remote
    # --------------------------------------------------------

    if remote_status == "FULLY_REMOTE":

        score += 5

    elif remote_status == "REMOTE_FIRST":

        score += 4

    elif remote_status == "UNKNOWN":

        score -= 3

    elif remote_status == "HYBRID":

        score -= 8

    elif remote_status == "ONSITE":

        score -= 20

    # --------------------------------------------------------
    # Remote confidence
    # --------------------------------------------------------

    if remote_confidence == "HIGH":

        score += 2

    elif remote_confidence == "UNKNOWN":

        score -= 1

    # --------------------------------------------------------
    # Geography
    # --------------------------------------------------------

    if geo_status == "LIKELY_ELIGIBLE":

        score += 5

    elif geo_status == "NEEDS_VERIFICATION":

        score -= 2

    elif geo_status == "RESTRICTED":

        score -= 20

    return max(
        0,
        min(score, 100),
    )


def classify_priority(
    opportunity_score: float,
    match_score: float,
    geo_status: str,
) -> str:

    # Hard block.
    if geo_status == "RESTRICTED":

        return "VERIFY"

    if (
        opportunity_score >= 85
        and match_score >= 75
        and geo_status == "LIKELY_ELIGIBLE"
    ):

        return "HIGH"

    if (
        opportunity_score >= 70
        and match_score >= 65
    ):

        return "MEDIUM"

    if opportunity_score >= 50:

        return "LOW"

    return "VERIFY"


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    sample_jobs = [

        {
            "title": "AI Automation Engineer",
            "location": "Worldwide",
            "description": (
                "Fully remote role."
            ),
        },

        {
            "title": "CX AI & Automation Lead",
            "location": "EMEA",
            "description": (
                "Our team is globally distributed "
                "around the world and all positions "
                "are fully remote. We hire globally."
            ),
        },

        {
            "title": "AI Engineer",
            "location": "Canada",
            "description": (
                "Fully remote."
            ),
        },

        {
            "title": "Python Automation Developer",
            "location": "EMEA",
            "description": (
                "Remote position."
            ),
        },

        {
            "title": "AI Engineer",
            "location": "LATAM",
            "description": (
                "Remote position."
            ),
        },

        {
            "title": "GenAI Engineer",
            "location": "LATAM",
            "description": (
                "We are a global company "
                "with remote teams."
            ),
        },

        {
            "title": "AI Engineer",
            "location": "LATAM",
            "description": (
                "We hire globally and "
                "work fully remote."
            ),
        },
    ]

    for job in sample_jobs:

        geo = assess_geo_eligibility(
            job
        )

        score = calculate_opportunity_score(
            match_score=85,
            remote_status="FULLY_REMOTE",
            remote_confidence="HIGH",
            geo_status=geo["status"],
        )

        priority = classify_priority(
            opportunity_score=score,
            match_score=85,
            geo_status=geo["status"],
        )

        print()
        print(
            job["title"]
        )

        print(
            "Location   :",
            job["location"],
        )

        print(
            "Geo        :",
            geo["status"],
        )

        print(
            "Confidence :",
            geo["confidence"],
        )

        print(
            "Reason     :",
            geo["reason"],
        )

        print(
            "Priority   :",
            priority,
        )

        print(
            "Score      :",
            score,
        )