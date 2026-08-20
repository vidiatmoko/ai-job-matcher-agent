from typing import List

import requests

from .base import JobSource
from .models import NormalizedJob


ADZUNA_API_URL = "https://api.adzuna.com/v1/api/jobs"


class AdzunaSource(JobSource):
    """
    Adzuna job source.

    Mengambil lowongan dari Adzuna dan mengubahnya
    ke format NormalizedJob.
    """

    name = "adzuna"

    def __init__(
        self,
        app_id: str,
        app_key: str,
        country: str = "gb",
        timeout: int = 30,
    ):
        if not app_id:
            raise ValueError("ADZUNA_APP_ID tidak boleh kosong.")

        if not app_key:
            raise ValueError("ADZUNA_APP_KEY tidak boleh kosong.")

        self.app_id = app_id
        self.app_key = app_key
        self.country = country
        self.timeout = timeout

    def _fetch_jobs(
        self,
        keyword: str,
        location: str = "",
        page: int = 1,
        limit: int = 20,
    ) -> list:
        """
        Mengambil raw jobs dari Adzuna.
        """

        url = (
            f"{ADZUNA_API_URL}/"
            f"{self.country}/search/{page}"
        )

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": limit,
            "what": keyword.strip(),
            "content-type": "application/json",
        }

        if location:
            params["where"] = location.strip()

        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()

        except requests.RequestException as error:
            raise RuntimeError(
                f"Gagal mengambil data dari Adzuna: {error}"
            )

        except ValueError as error:
            raise RuntimeError(
                f"Response Adzuna bukan JSON valid: {error}"
            )

        results = data.get("results", [])

        if not isinstance(results, list):
            raise RuntimeError(
                "Format response Adzuna tidak sesuai."
            )

        return results

    def _to_normalized_job(
        self,
        job: dict,
    ) -> NormalizedJob:
        """
        Mengubah raw Adzuna job menjadi NormalizedJob.
        """

        job_id = job.get("id")

        company = (
            job.get("company", {})
            if isinstance(job.get("company"), dict)
            else {}
        )

        location = (
            job.get("location", {})
            if isinstance(job.get("location"), dict)
            else {}
        )

        return NormalizedJob(
            id=(
                str(job_id)
                if job_id is not None
                else None
            ),

            title=(
                job.get("title") or ""
            ).strip(),

            company=(
                company.get("display_name") or ""
            ).strip(),

            location=(
                location.get("display_name") or ""
            ).strip(),

            description=(
                job.get("description") or ""
            ).strip(),

            salary_min=job.get("salary_min"),

            salary_max=job.get("salary_max"),

            created=job.get("created"),

            url=(
                job.get("redirect_url") or ""
            ).strip(),

            source=self.name,

            source_job_id=(
                str(job_id)
                if job_id is not None
                else None
            ),

            remote_status="UNKNOWN",

            remote_confidence="UNKNOWN",

            tags=[],
        )

    def search(
        self,
        keyword: str,
        location: str = "",
        limit: int = 20,
    ) -> List[NormalizedJob]:
        """
        Mencari lowongan Adzuna dan mengembalikan
        list NormalizedJob.
        """

        if not keyword or not keyword.strip():
            raise ValueError(
                "Keyword pekerjaan tidak boleh kosong."
            )

        raw_jobs = self._fetch_jobs(
            keyword=keyword,
            location=location,
            page=1,
            limit=limit,
        )

        results = []

        for raw_job in raw_jobs:
            normalized = self._to_normalized_job(
                raw_job
            )

            if not normalized.id:
                continue

            results.append(normalized)

        return results

    def get_job(
        self,
        job_url: str,
    ) -> NormalizedJob:
        """
        Adzuna tidak kita gunakan untuk fetch detail URL
        karena sebelumnya endpoint detail mengembalikan 403.

        Method ini dipertahankan agar sesuai interface JobSource.
        """

        raise NotImplementedError(
            "Adzuna detail-page verification tidak digunakan "
            "karena URL detail dapat mengembalikan HTTP 403."
        )