import html
import re
from typing import List

import requests

from .base import JobSource
from .models import NormalizedJob


REMOTEOK_API_URL = "https://remoteok.com/api"


def clean_html(text: str) -> str:
    """
    Mengubah HTML sederhana menjadi plain text.
    """

    if not text:
        return ""

    text = html.unescape(text)

    text = re.sub(
        r"<(script|style).*?>.*?</\1>",
        " ",
        text,
        flags=re.I | re.S,
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = " ".join(text.split())

    return text.strip()


def normalize_terms(text: str) -> List[str]:
    """
    Mengubah teks menjadi token sederhana untuk pencarian.
    """

    if not text:
        return []

    return re.findall(
        r"[a-zA-Z0-9+#.]+",
        text.lower(),
    )


def normalize_salary(value):
    """
    Mengubah nilai salary 0 menjadi None.
    """

    if value in (None, "", 0, "0"):
        return None

    return value


class RemoteOKSource(JobSource):
    """
    RemoteOK job source.

    RemoteOK menyediakan JSON feed resmi.
    """

    name = "remoteok"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def _fetch_jobs(self) -> list:
        """
        Mengambil job dari RemoteOK JSON feed.
        """

        headers = {
            "User-Agent": (
                "AI-Career-Copilot/0.1 "
                "(job research application)"
            )
        }

        try:
            response = requests.get(
                REMOTEOK_API_URL,
                headers=headers,
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()

        except requests.RequestException as error:
            raise RuntimeError(
                f"Gagal mengambil data dari RemoteOK: {error}"
            )

        except ValueError as error:
            raise RuntimeError(
                f"Response RemoteOK bukan JSON valid: {error}"
            )

        if isinstance(data, list):
            return [
                item
                for item in data
                if isinstance(item, dict)
                and item.get("id")
            ]

        raise RuntimeError(
            "Format response RemoteOK tidak sesuai."
        )

    def _calculate_relevance(
        self,
        job: dict,
        keyword: str,
    ) -> float:
        """
        Menghitung relevance score untuk job.

        Prioritas evidence:
        1. Exact phrase di title
        2. Term di title
        3. Term di tags
        4. Term di description
        5. Term di company
        """

        query_terms = normalize_terms(keyword)

        if not query_terms:
            return 0.0

        title = (
            job.get("position") or ""
        ).lower()

        title_terms = set(
            normalize_terms(title)
        )

        tag_terms = set(
            normalize_terms(
                " ".join(
                    str(tag)
                    for tag in (
                        job.get("tags") or []
                    )
                )
            )
        )

        company_terms = set(
            normalize_terms(
                job.get("company") or ""
            )
        )

        description_terms = set(
            normalize_terms(
                clean_html(
                    job.get("description") or ""
                )
            )
        )

        score = 0.0
        matched_terms = 0

        for term in query_terms:

            term_score = 0

            if term in title_terms:
                term_score += 10

            if term in tag_terms:
                term_score += 6

            if term in company_terms:
                term_score += 2

            if term in description_terms:
                term_score += 1

            if term_score > 0:
                matched_terms += 1

            score += term_score

        # Bonus jika seluruh query phrase muncul di title.
        if len(query_terms) > 1:

            if keyword.lower().strip() in title:
                score += 15

            # Bonus jika semua term ditemukan.
            if matched_terms == len(query_terms):
                score += 8

        return score

    def _to_normalized_job(
        self,
        job: dict,
    ) -> NormalizedJob:
        """
        Mengubah format RemoteOK menjadi NormalizedJob.
        """

        job_id = job.get("id")

        tags = job.get("tags") or []

        if not isinstance(tags, list):
            tags = []

        tags = [
            str(tag).strip()
            for tag in tags
            if tag
        ]

        return NormalizedJob(
            id=(
                str(job_id)
                if job_id is not None
                else None
            ),

            title=(
                job.get("position") or ""
            ).strip(),

            company=html.unescape(
                (
                    job.get("company")
                    or ""
                ).strip()
            ),

            location=(
                job.get("location") or ""
            ).strip(),

            description=clean_html(
                job.get("description") or ""
            ),

            url=(
                job.get("apply_url")
                or job.get("url")
                or ""
            ).strip(),

            salary_min=normalize_salary(
                job.get("salary_min")
            ),

            salary_max=normalize_salary(
                job.get("salary_max")
            ),

            created=job.get("date"),

            source=self.name,

            source_job_id=(
                str(job_id)
                if job_id is not None
                else None
            ),

            remote_status="FULLY_REMOTE",

            remote_confidence="HIGH",

            tags=tags,
        )

    def search(
        self,
        keyword: str,
        location: str = "",
        limit: int = 20,
    ) -> List[NormalizedJob]:
        """
        Mencari job RemoteOK berdasarkan keyword.
        """

        if not keyword or not keyword.strip():
            raise ValueError(
                "Keyword pekerjaan tidak boleh kosong."
            )

        keyword = keyword.lower().strip()
        location = location.lower().strip()

        jobs = self._fetch_jobs()

        scored_jobs = []

        for job in jobs:

            job_location = (
                job.get("location")
                or ""
            ).lower()

            if (
                location
                and location not in job_location
            ):
                continue

            score = self._calculate_relevance(
                job,
                keyword,
            )

            # Jangan memasukkan job yang sama sekali
            # tidak relevan.
            if score <= 0:
                continue

            scored_jobs.append(
                (
                    score,
                    job,
                )
            )

        # Ranking dari paling relevan.
        scored_jobs.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        results = []

        for score, job in scored_jobs[:limit]:

            normalized = self._to_normalized_job(
                job
            )

            results.append(normalized)

        return results

    def get_job(
        self,
        job_url: str,
    ) -> NormalizedJob:
        """
        Mengambil satu job berdasarkan URL.
        """

        if not job_url:
            raise ValueError(
                "Job URL tidak boleh kosong."
            )

        jobs = self._fetch_jobs()

        target_url = job_url.strip()

        for job in jobs:

            current_url = (
                job.get("apply_url")
                or job.get("url")
                or ""
            ).strip()

            if current_url == target_url:
                return self._to_normalized_job(
                    job
                )

        raise ValueError(
            "Job tidak ditemukan di RemoteOK feed."
        )