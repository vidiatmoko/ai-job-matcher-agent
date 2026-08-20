from backend.db.database import get_connection


def main():
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT COUNT(*) AS n FROM jobs"
        )
        jobs_count = cursor.fetchone()["n"]

        cursor.execute(
            "SELECT COUNT(*) AS n FROM ai_evaluations"
        )
        evaluations_count = cursor.fetchone()["n"]

        cursor.execute(
            """
            SELECT
                provider,
                model,
                COUNT(*) AS n
            FROM ai_evaluations
            GROUP BY provider, model
            ORDER BY n DESC
            """
        )

        providers = [
            dict(row)
            for row in cursor.fetchall()
        ]

    print("JOBS:", jobs_count)
    print("AI EVALUATIONS:", evaluations_count)
    print("PROVIDERS:")

    for item in providers:
        print(
            f"  {item['provider']} | "
            f"{item['model']} | "
            f"{item['n']}"
        )


if __name__ == "__main__":
    main()
