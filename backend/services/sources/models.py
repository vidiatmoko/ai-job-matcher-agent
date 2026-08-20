from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NormalizedJob:
    """
    Format internal standar untuk semua job source.
    """

    id: Optional[str]
    title: str
    company: str
    location: str
    description: str
    url: str

    source: str
    source_job_id: Optional[str] = None

    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    created: Optional[str] = None
    deadline: Optional[str] = None

    remote_status: str = "UNKNOWN"
    remote_confidence: str = "UNKNOWN"
    relevance_score: float = 0.0

    tags: List[str] = field(default_factory=list)

    def dedup_key(self) -> str:
        """
        Key yang digunakan untuk deduplication.
        """

        if self.source and self.source_job_id:
            return f"{self.source}:{self.source_job_id}"

        if self.url:
            return self.url

        return (
            f"{self.title.lower().strip()}:"
            f"{self.company.lower().strip()}"
        )