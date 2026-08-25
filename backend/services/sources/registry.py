import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from .adzuna import AdzunaSource
from .base import JobSource
from .remoteok import RemoteOKSource


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


def get_job_sources() -> List[JobSource]:
    """
    Membuat daftar job source yang aktif.

    Adzuna:
    - UK
    - US
    - Canada
    - Australia
    - Germany

    RemoteOK:
    - Global remote feed
    """

    sources: List[JobSource] = []

    adzuna_app_id = os.getenv("ADZUNA_APP_ID")
    adzuna_app_key = os.getenv("ADZUNA_APP_KEY")

    if adzuna_app_id and adzuna_app_key:

        adzuna_countries = [
            "gb",
            "us",
            "ca",
            "au",
            "de",
        ]

        for country in adzuna_countries:
            sources.append(
                AdzunaSource(
                    app_id=adzuna_app_id,
                    app_key=adzuna_app_key,
                    country=country,
                )
            )

    # RemoteOK tidak membutuhkan credential.
    sources.append(
        RemoteOKSource()
    )

    return sources