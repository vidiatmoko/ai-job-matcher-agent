import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional


CACHE_DIR = (
    Path(__file__).resolve().parent.parent / "cache"
)

CACHE_FILE = CACHE_DIR / "ai_results.json"


def ensure_cache():
    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not CACHE_FILE.exists():
        CACHE_FILE.write_text(
            "{}",
            encoding="utf-8",
        )


def load_cache() -> Dict[str, Any]:
    ensure_cache()

    try:
        return json.loads(
            CACHE_FILE.read_text(
                encoding="utf-8"
            )
        )

    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(cache: Dict[str, Any]):
    ensure_cache()

    CACHE_FILE.write_text(
        json.dumps(
            cache,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def build_cache_key(
    job_id: Optional[str],
    title: str,
    description: str,
) -> str:
    """
    Membuat hash stabil berdasarkan identitas job
    dan isi job description.
    """

    raw = "|".join(
        [
            str(job_id or ""),
            title.strip().lower(),
            description.strip().lower(),
        ]
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def get_cached_result(
    cache_key: str,
) -> Optional[Dict[str, Any]]:
    cache = load_cache()

    return cache.get(cache_key)


def set_cached_result(
    cache_key: str,
    result: Dict[str, Any],
):
    cache = load_cache()

    cache[cache_key] = result

    save_cache(cache)