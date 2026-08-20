from typing import Any, Dict, List

from backend.ai.router import AIRouter
from backend.profile_formatter import format_candidate_profile


# ============================================================
# AI ROUTER
# ============================================================

ai_router = AIRouter()


# ============================================================
# HELPERS
# ============================================================

def get_candidate_profile() -> str:
    """
    Mengambil candidate profile terstruktur.
    """
    return format_candidate_profile()


def evaluate_single_prompt(
    prompt: str,
) -> Dict[str, Any]:
    """
    Mengirim prompt melalui AI Router.

    Router akan mencoba:
        Gemini -> Groq -> OpenRouter
    """

    provider_name, result = ai_router.generate_json(
        prompt
    )

    provider_model = getattr(
        ai_router,
        "last_model",
        "unknown",
    )

    if isinstance(result, dict):
        result["_ai_provider"] = provider_name
        result["_ai_model"] = provider_model

    return result


# ============================================================
# SINGLE JOB EVALUATION
# ============================================================

def evaluate_job(
    job_title: str,
    job_description: str,
) -> dict:
    """
    Mengevaluasi satu lowongan.

    Cocok untuk:
    - LinkedIn manual analysis
    - Upwork manual analysis
    - Wellfound manual analysis
    - single job analysis
    """

    candidate_profile = get_candidate_profile()

    prompt = f"""
You are an expert AI Technical Recruiter.

Evaluate the fit between the candidate and the job posting.

IMPORTANT RULES:

1. Only use skills, experience, projects, and certifications
   explicitly supported by the candidate profile.

2. Never invent candidate experience.

3. Missing evidence must be treated as a gap.

4. Do not inflate the score.

5. Consider the candidate's transition into AI and Automation.

6. Prioritize actual career relevance over keyword overlap.

7. Consider seniority carefully.

8. If the job requires domain-specific experience that is not
   documented in the candidate profile, identify it as a gap.

9. The recommendation must consider both strengths and gaps.

--- CANDIDATE PROFILE ---

{candidate_profile}

--- JOB DETAILS ---

Title:
{job_title}

Description:
{job_description}

--- OUTPUT ---

Return ONLY valid JSON with this exact structure:

{{
    "match_score": 0,
    "fit_summary": "",
    "key_pros": [],
    "key_gaps": [],
    "recommended_action": "Apply with tailored CV",
    "draft_outreach": ""
}}

Rules:

recommended_action must be exactly one of:

- Apply Immediately
- Apply with tailored CV
- Skip

draft_outreach should only be populated
when match_score >= 70.
"""

    try:
        return evaluate_single_prompt(prompt)

    except Exception as error:
        return {
            "error": (
                f"Failed to evaluate job: {error}"
            )
        }


# ============================================================
# BATCH EVALUATION
# ============================================================

def evaluate_jobs_batch(
    jobs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Mengevaluasi banyak job menggunakan SATU request AI.

    Provider dan model yang berhasil digunakan akan
    ditempelkan ke setiap hasil:
        _ai_provider
        _ai_model
    """

    if not jobs:
        return []

    candidate_profile = get_candidate_profile()

    job_blocks = []

    for index, job in enumerate(
        jobs,
        start=1,
    ):
        job_blocks.append(
            f"""
JOB {index}

ID:
{job.get("id", "")}

Title:
{job.get("title", "")}

Company:
{job.get("company", "")}

Location:
{job.get("location", "")}

Description:
{job.get("description", "")}
"""
        )

    jobs_text = "\n".join(job_blocks)

    prompt = f"""
You are an expert AI Technical Recruiter.

Evaluate ALL jobs below against the SAME candidate profile.

IMPORTANT RULES:

1. Evaluate EVERY input job.
2. Return exactly ONE result for every input job.
3. Preserve each input job ID exactly.
4. Only use skills, experience, projects, and certifications
   explicitly supported by the candidate profile.
5. Never invent candidate experience.
6. Missing evidence must be treated as a gap.
7. Do not inflate scores.
8. Evaluate each job independently.
9. Consider actual career relevance, seniority,
   technical requirements, and evidence.
10. The candidate is targeting:
    - AI Automation
    - AI Engineering
    - Python
    - LLM
    - RAG
    - Workflow Automation
    - AI Agents
    - Backend Python
    - Remote engineering roles
11. If a job requires highly specific technologies,
    certifications, language skills, cloud platforms,
    or domain experience that are not supported,
    lower the score accordingly.

--- CANDIDATE PROFILE ---

{candidate_profile}

--- JOBS ---

{jobs_text}

--- OUTPUT ---

Return ONLY valid JSON:

{{
    "jobs": [
        {{
            "job_id": "",
            "match_score": 0,
            "fit_summary": "",
            "key_pros": [],
            "key_gaps": [],
            "recommended_action": "Apply with tailored CV",
            "draft_outreach": ""
        }}
    ]
}}

Rules:

- Include EVERY input job.
- Preserve job_id exactly.
- recommended_action must be exactly one of:
  "Apply Immediately"
  "Apply with tailored CV"
  "Skip"
- draft_outreach should only be populated when
  match_score >= 70.
"""

    try:
        provider_name, result = ai_router.generate_json(
            prompt
        )

        provider_model = getattr(
            ai_router,
            "last_model",
            "unknown",
        )

        batch_results = result.get(
            "jobs",
            [],
        )

        if not isinstance(
            batch_results,
            list,
        ):
            raise ValueError(
                "AI batch response tidak memiliki "
                "array 'jobs'."
            )

        # Pastikan metadata provider/model tersedia
        # pada setiap hasil.
        enriched_results = []

        for item in batch_results:
            if not isinstance(item, dict):
                continue

            item["_ai_provider"] = provider_name
            item["_ai_model"] = provider_model

            enriched_results.append(item)

        return enriched_results

    except Exception as error:

        return [
            {
                "job_id": job.get("id"),
                "error": (
                    f"Batch evaluation failed: "
                    f"{error}"
                ),
            }
            for job in jobs
        ]


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print("AI Evaluator loaded successfully.")

    print(
        "Available providers:"
    )

    for provider in ai_router.available_providers():
        print(
            f"- {provider}"
        )

    print(
        f"Current last provider: "
        f"{ai_router.last_provider}"
    )

    print(
        f"Current last model: "
        f"{ai_router.last_model}"
    )