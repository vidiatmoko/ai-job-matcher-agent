from backend.db.database import get_connection


def main():
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, title, company, source
            FROM jobs
            WHERE url = 'https://example.com/job'
               OR company = 'Example Company'
            """
        )

        rows = cursor.fetchall()

        if not rows:
            print("No test data found.")
            return

        for row in rows:
            job_id = row["id"]

            cursor.execute(
                """
                DELETE FROM opportunity_assessments
                WHERE job_id = ?
                """,
                (job_id,),
            )

            cursor.execute(
                """
                DELETE FROM ai_evaluations
                WHERE job_id = ?
                """,
                (job_id,),
            )

            cursor.execute(
                """
                DELETE FROM jobs
                WHERE id = ?
                """,
                (job_id,),
            )

            print(
                f"Deleted test job: "
                f"{row['title']} | "
                f"{row['company']} | "
                f"{row['source']}"
            )

    print("Test data cleanup complete.")


if __name__ == "__main__":
    main()