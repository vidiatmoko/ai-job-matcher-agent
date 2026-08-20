from backend.candidate_profile import CANDIDATE_PROFILE


def format_candidate_profile() -> str:
    profile = CANDIDATE_PROFILE

    lines = []

    positioning = profile["professional_positioning"]

    lines.append("CANDIDATE PROFILE")
    lines.append("=" * 60)
    lines.append(f"Target Role: {positioning['current_target']}")
    lines.append(f"Background: {positioning['background']}")
    lines.append(f"Experience: {positioning['experience_years']}")
    lines.append(f"Remote Ready: {positioning['remote_ready']}")

    lines.append("\nTARGET ROLES")
    for role in profile["target_roles"]:
        lines.append(f"- {role}")

    lines.append("\nCORE SKILLS")

    for category, skills in profile["core_skills"].items():
        lines.append(f"\n[{category}]")
        for skill in skills:
            lines.append(f"- {skill}")

    lines.append("\nPORTFOLIO")

    for project in profile["portfolio"]:
        lines.append(f"\n{project['name']}")
        lines.append(f"Skills: {', '.join(project['skills'])}")
        lines.append(f"Evidence: {project['evidence']}")

    lines.append("\nWORK EXPERIENCE")

    for job in profile["work_experience"]:
        lines.append(
            f"\n{job['role']} | {job['company']} | {job['period']}"
        )

        lines.append(
            f"Skills: {', '.join(job['skills'])}"
        )

        if job.get("evidence"):
            lines.append(f"Evidence: {job['evidence']}")

    lines.append("\nCERTIFICATIONS")

    for certification in profile["certifications"]:
        lines.append(f"- {certification}")

    lines.append("\nJOB PREFERENCES")

    preferences = profile["job_preferences"]

    lines.append(
        f"Employment Types: "
        f"{', '.join(preferences['employment_types'])}"
    )

    lines.append(
        f"Location Types: "
        f"{', '.join(preferences['location_type'])}"
    )

    lines.append(
        f"Preferred Regions: "
        f"{', '.join(preferences['preferred_regions'])}"
    )

    return "\n".join(lines)


if __name__ == "__main__":
    print(format_candidate_profile())