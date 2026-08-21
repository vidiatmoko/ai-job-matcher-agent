import sqlite3
from pathlib import Path
from contextlib import contextmanager


BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
DATABASE_FILE = DATA_DIR / "career_copilot.db"


def ensure_data_directory():
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


@contextmanager
def get_connection():
    ensure_data_directory()

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def initialize_database():

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_job_id TEXT,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                description TEXT,
                url TEXT,
                salary_min REAL,
                salary_max REAL,
                created_at TEXT,
                deadline TEXT,
                remote_status TEXT DEFAULT 'UNKNOWN',
                remote_confidence TEXT DEFAULT 'UNKNOWN',
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                UNIQUE(source, source_job_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                model TEXT,
                profile_version TEXT DEFAULT 'v1',
                match_score REAL,
                fit_summary TEXT,
                key_pros TEXT,
                key_gaps TEXT,
                recommended_action TEXT,
                draft_outreach TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(job_id)
                    REFERENCES jobs(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS opportunity_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL UNIQUE,
                geo_status TEXT NOT NULL,
                geo_confidence TEXT DEFAULT 'LOW',
                geo_reason TEXT,
                opportunity_score REAL,
                priority TEXT,
                final_action TEXT DEFAULT 'REVIEW',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(job_id)
                    REFERENCES jobs(id)
            )
            """
        )

        # -----------------------------------------------------
        # SAFE MIGRATION - opportunity_assessments
        # -----------------------------------------------------

        cursor.execute(
            "PRAGMA table_info(opportunity_assessments)"
        )

        columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        if "geo_confidence" not in columns:
            cursor.execute(
                """
                ALTER TABLE opportunity_assessments
                ADD COLUMN geo_confidence TEXT
                DEFAULT 'LOW'
                """
            )

        if "final_action" not in columns:
            cursor.execute(
                """
                ALTER TABLE opportunity_assessments
                ADD COLUMN final_action TEXT
                DEFAULT 'REVIEW'
                """
            )

        # -----------------------------------------------------
        # APPLICATIONS
        # -----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                ai_evaluation_id INTEGER,
                application_channel TEXT,
                cv_version TEXT,
                status TEXT NOT NULL DEFAULT 'SAVED',
                applied_at TEXT,
                last_updated_at TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY(job_id)
                    REFERENCES jobs(id),
                FOREIGN KEY(ai_evaluation_id)
                    REFERENCES ai_evaluations(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS application_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_date TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY(application_id)
                    REFERENCES applications(id)
            )
            """
        )

        # -----------------------------------------------------
        # SAFE MIGRATION - jobs
        # -----------------------------------------------------

        cursor.execute(
            "PRAGMA table_info(jobs)"
                )

        job_columns = {
            row["name"]
        for row in cursor.fetchall()
            }

        if "deadline" not in job_columns:
            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN deadline TEXT
                """
        )   

        # -----------------------------------------------------
        # INDEXES
        # -----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_jobs_source
            ON jobs(source)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_jobs_company
            ON jobs(company)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_jobs_title
            ON jobs(title)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_applications_status
            ON applications(status)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_opportunity_priority
            ON opportunity_assessments(priority)
            """
        )


if __name__ == "__main__":

    initialize_database()

    print(
        "Database initialized successfully."
    )

    print(
        f"Database file: {DATABASE_FILE}"
    )
