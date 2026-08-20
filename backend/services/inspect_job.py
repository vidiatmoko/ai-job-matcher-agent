from backend.services.job_search import prepare_jobs


jobs = prepare_jobs(
    keyword="AI Automation",
    country="gb",
    results_per_page=20,
)

for job in jobs:
    if "RSM UK" in job.get("company", ""):
        print("=" * 80)
        print("TITLE   :", job["title"])
        print("COMPANY :", job["company"])
        print("LOCATION:", job["location"])
        print("\nDESCRIPTION:\n")
        print(job["description"][:3000])
        print()