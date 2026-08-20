from backend.services.sources.remoteok import RemoteOKSource



def test_search(keyword):
    source = RemoteOKSource()

    jobs = source.search(
        keyword=keyword,
        limit=5,
    )

    print()
    print("=" * 70)
    print(f"QUERY: {keyword}")
    print(f"RemoteOK ditemukan: {len(jobs)} job")
    print("=" * 70)

    for index, job in enumerate(jobs, start=1):

        print()
        print(f"JOB #{index}")
        print("-" * 70)
        print("ID                 :", job.id)
        print("Title              :", job.title)
        print("Company            :", job.company)
        print("Location           :", job.location)
        print("Source             :", job.source)
        print("Remote status      :", job.remote_status)
        print("Remote confidence  :", job.remote_confidence)
        print("Salary             :", job.salary_min, "-", job.salary_max)
        print("Tags               :", ", ".join(job.tags))
        print("URL                :", job.url)


def main():
    queries = [
        "AI",
        "AI Automation",
        "Python",
        "Automation",
        "LLM",
    ]

    for query in queries:
        test_search(query)


if __name__ == "__main__":
    main()

