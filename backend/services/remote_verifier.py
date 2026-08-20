import re
import requests


REMOTE_PATTERNS = [
    "fully remote",
    "100% remote",
    "fully-remote",
    "remote only",
    "remote position",
    "remote role",
    "remote job",
    "work from home",
    "work-from-home",
    "home based",
    "home-based",
    "work from anywhere",
    "location independent",
    "remote-first",
    "remote first",
]

HYBRID_PATTERNS = [
    "hybrid",
    "hybrid working",
    "hybrid role",
    "hybrid position",
    "days in office",
    "days per week in office",
    "office and remote",
]

ONSITE_PATTERNS = [
    "onsite",
    "on-site",
    "on site",
    "office based",
    "office-based",
    "in office",
    "work from office",
]


def clean_html(html: str) -> str:
    """
    Mengubah HTML sederhana menjadi teks agar dapat dicari
    menggunakan keyword tanpa membutuhkan LLM.
    """

    # Hapus script dan style.
    html = re.sub(
        r"<(script|style).*?>.*?</\1>",
        " ",
        html,
        flags=re.I | re.S,
    )

    # Hapus semua HTML tags.
    text = re.sub(r"<[^>]+>", " ", html)

    # Decode basic HTML entities.
    text = re.sub(r"&nbsp;", " ", text, flags=re.I)
    text = re.sub(r"&amp;", "&", text, flags=re.I)

    # Normalisasi whitespace.
    text = " ".join(text.split())

    return text.lower()


def classify_text(text: str) -> str:
    """
    Menentukan status kerja dari teks halaman.
    """

    text = text.lower()

    if any(pattern in text for pattern in REMOTE_PATTERNS):
        return "FULLY_REMOTE"

    if any(pattern in text for pattern in HYBRID_PATTERNS):
        return "HYBRID"

    if any(pattern in text for pattern in ONSITE_PATTERNS):
        return "ONSITE"

    return "UNKNOWN"


def verify_remote_status(
    job_url: str,
    timeout: int = 15,
) -> dict:
    """
    Mengambil halaman sumber dan mencoba memverifikasi
    status remote berdasarkan teks halaman.

    Tidak menggunakan Gemini.
    """

    if not job_url:
        return {
            "status": "UNKNOWN",
            "source_url": None,
            "verification_method": "no_url",
        }

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
            job_url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
        )

        response.raise_for_status()

        text = clean_html(response.text)

        status = classify_text(text)

        return {
            "status": status,
            "source_url": response.url,
            "verification_method": "source_page_text",
            "http_status": response.status_code,
        }

    except requests.RequestException as error:
        return {
            "status": "UNKNOWN",
            "source_url": job_url,
            "verification_method": "request_failed",
            "error": str(error),
        }


if __name__ == "__main__":
    test_url = (
        "https://www.adzuna.co.uk/jobs/land/ad/"
        "5781216462"
    )

    print("Testing Remote Verification...\n")

    result = verify_remote_status(test_url)

    print("Status      :", result["status"])
    print("Source URL  :", result.get("source_url"))
    print("Method      :", result["verification_method"])

    if "error" in result:
        print("Error       :", result["error"])