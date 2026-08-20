from backend.evaluator import evaluate_jobs_batch


def main():

    jobs = [
        {
            "id": "TEST-001",
            "title": "AI Automation Engineer",
            "company": "Example Company",
            "location": "Remote",
            "description": """
            We are looking for an AI Automation Engineer
            with Python, n8n, REST APIs, LLM integrations,
            RAG and AI workflow automation experience.
            """
        },
        {
            "id": "TEST-002",
            "title": "Senior Data Engineer",
            "company": "Example Data",
            "location": "Remote",
            "description": """
            Requires deep expertise in Spark, Scala,
            Databricks and large scale data engineering.
            """
        }
    ]

    results = evaluate_jobs_batch(jobs)

    print("\nBATCH RESULTS")
    print("=" * 70)

    for result in results:
        print(result)


if __name__ == "__main__":
    main()