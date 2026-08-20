import re
import html
import requests
from typing import List
from .base import JobSource
from .models import NormalizedJob


REMOTE_COM_URL = "https://remote.com/jobs"


def clean_html(text: str) -> str:
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


def normalize_text(text: str) -> str:
    return " ".join(
        (text or "").lower().split()
    )


class RemoteComSource(JobSource):

    name = "remotecom"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

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

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/142.0 Safari/537.36"
            )
        }

        try:
            response = requests.get(
                REMOTE_COM_URL,
                headers=headers,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except requests.RequestException as error:
            raise RuntimeError(
                f"Gagal mengambil Remote.com: {error}"
            )

        text = response.text

        print(
            f"[Remote.com] HTTP {response.status_code}"
        )

        # Untuk tahap pertama kita hanya memastikan
        # halaman dapat diakses.
        if not text:
            return []

        # Cari pola URL job publik.
        urls = re.findall(
            r'https?://remote\.com/(?:openings|jobs)/[^\s"<>]+',
            text,
            flags=re.I,
        )

        # Hilangkan duplikat.
        unique_urls = []

        for url in urls:
            url = html.unescape(url)

            if url not in unique_urls:
                unique_urls.append(url)

        results = []

        keyword_terms = set(
            normalize_text(keyword).split()
        )

        for url in unique_urls:

            slug = url.rstrip("/").split("/")[-1]

            title = (
                slug.replace("-", " ")
                .replace("_", " ")
            )

            title = " ".join(
                title.split()
            ).strip()

            title_lower = normalize_text(title)

            relevance = 0

            for term in keyword_terms:
                if term in title_lower:
                    relevance += 1

            # Jangan memasukkan URL yang sama sekali
            # tidak berkaitan dengan keyword.
            if keyword_terms and relevance == 0:
                continue

            results.append(
                NormalizedJob(
                    id=slug,
                    title=title,
                    company="",
                    location=location,
                    description="",
                    url=url,
                    salary_min=None,
                    salary_max=None,
                    created=None,
                    source=self.name,
                    source_job_id=slug,
                    remote_status="FULLY_REMOTE",
                    remote_confidence="HIGH",
                    tags=[],
                )
            )

            if len(results) >= limit:
                break

        return results


if __name__ == "__main__":

    print("=" * 70)
    print("Testing Remote.com Source")
    print("=" * 70)

    source = RemoteComSource()

    jobs = source.search(
        keyword="AI Automation",
        limit=10,
    )

    print(
        f"\nRemote.com ditemukan: "
        f"{len(jobs)} job\n"
    )

    for index, job in enumerate(
        jobs,
        start=1,
    ):

        print(f"JOB #{index}")
        print("-" * 70)
        print(f"ID       : {job.id}")
        print(f"Title    : {job.title}")
        print(f"Company  : {job.company}")
        print(f"Remote   : {job.remote_status}")
        print(f"URL      : {job.url}")
        print()