from backend.db.database import get_connection


def main():
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                applications.id,
                applications.job_id
            FROM applications
            WHERE applications.ai_evaluation_id IS NULL
            """
        )

        rows = cursor.fetchall()

        if not rows:
            print("No application records need repair.")
            return

        repaired = 0

        for row in rows:
            application_id = row["id"]
            job_id = row["job_id"]

            cursor.execute(
                """
                SELECT id
                FROM ai_evaluations
                WHERE job_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (job_id,),
            )

            evaluation = cursor.fetchone()

            if evaluation is None:
                print(
                    f"Application {application_id}: "
                    f"no AI evaluation found."
                )
                continue

            evaluation_id = evaluation["id"]

            cursor.execute(
                """
                UPDATE applications
                SET ai_evaluation_id = ?
                WHERE id = ?
                """,
                (
                    evaluation_id,
                    application_id,
                ),
            )

            repaired += 1

            print(
                f"Repaired application {application_id} "
                f"→ AI evaluation {evaluation_id}"
            )

        print(
            f"Repair complete. Records repaired: {repaired}"
        )


if __name__ == "__main__":
    main()