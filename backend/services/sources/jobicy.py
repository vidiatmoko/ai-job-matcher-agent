import html
import re
from typing import List

import requests

from .base import JobSource
from .models import NormalizedJob


JOBICY_API_URL = "https://jobicy.com/api/v2/remote-jobs"


def clean_html(text: str) -> str:
    """Mengubah HTML menjadi plain text."""

    if not text:
        return ""

    text = html.unescape(text)

    text = re.sub(
        r"<(script|style).*?>.*?</\1>",
        " ",
        text,
        flags=re.I | re.S,
    )

    text = re.sub(r"<[^>]+>", " ", text)

    return " ".join(text.split()).strip()


class JobicySource(JobSource):
    """
    Jobicy remote job source.

    Jobicy menyediakan public API untuk remote jobs.
    """

    name = "jobicy"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def _fetch_jobs(
        self,
        keyword: str,
        location: str = "",
        limit: int = 20,
    ) -> list:
        params = {
            "count": min(limit, 100),
            "tag": keyword.strip(),
        }

        # Jobicy menggunakan geo sebagai filter.
        # Untuk tahap awal kita biarkan kosong agar global.
        if location:
            params["geo"] = location.strip().lower()

        headers = {
            "User-Agent": (
                "AI-Career-Copilot/0.1 "
                "(job research application)"
            )
        }

        try:
            response = requests.get(
                JOBICY_API_URL,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()

        except requests.RequestException as error:
            raise RuntimeError(
                f"Gagal mengambil data dari Jobicy: {error}"
            )

        except ValueError as error:
            raise RuntimeError(
                f"Response Jobicy bukan JSON valid: {error}"
            )

        jobs = data.get("jobs", [])

        if not isinstance(jobs, list):
            raise RuntimeError(
                "Format response Jobicy tidak sesuai."
            )

        return jobs

    def _to_normalized_job(
        self,
        job: dict,
    ) -> NormalizedJob:
        job_id = job.get("id")

        return NormalizedJob(
            id=(
                str(job_id)
                if job_id is not None
                else None
            ),

            title=(
                job.get("jobTitle") or ""
            ).strip(),

            company=(
                job.get("companyName") or ""
            ).strip(),

            location=(
                job.get("jobGeo") or ""
            ).strip(),

            description=clean_html(
                job.get("jobDescription") or ""
            ),

            url=(
                job.get("url") or ""
            ).strip(),

            salary_min=job.get("salaryMin"),

            salary_max=job.get("salaryMax"),

            created=job.get("pubDate"),

            source=self.name,

            source_job_id=(
                str(job_id)
                if job_id is not None
                else None
            ),

            remote_status="FULLY_REMOTE",

            remote_confidence="HIGH",

            tags=[
                str(job.get("jobIndustry") or "").strip(),
                str(job.get("jobType") or "").strip(),
                str(job.get("jobLevel") or "").strip(),
            ],
        )

    def search(
        self,
        keyword: str,
        location: str = "",
        limit: int = 20,
    ) -> List[NormalizedJob]:

        if not keyword or not keyword.strip():
            raise ValueError(
                "Keyword pekerjaan tidak boleh kosong."
            )

        raw_jobs = self._fetch_jobs(
            keyword=keyword,
            location=location,
            limit=limit,
        )

        results = []

        for raw_job in raw_jobs:
            normalized = self._to_normalized_job(
                raw_job
            )

            if not normalized.id:
                continue

            if not normalized.title:
                continue

            if not normalized.description:
                continue

            results.append(normalized)

        return results

    def get_job(
        self,
        job_url: str,
    ) -> NormalizedJob:

        if not job_url:
            raise ValueError(
                "Job URL tidak boleh kosong."
            )

        # Jobicy API tidak menyediakan endpoint detail
        # yang kita butuhkan untuk MVP ini.
        # Cari berdasarkan URL dari feed.
        jobs = self._fetch_jobs(
            keyword="",
            limit=100,
        )

        for raw_job in jobs:
            if (
                raw_job.get("url") or ""
            ).strip() == job_url.strip():

                return self._to_normalized_job(
                    raw_job
                )

        raise ValueError(
            "Job tidak ditemukan di Jobicy feed."
        )