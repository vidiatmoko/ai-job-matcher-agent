from abc import ABC, abstractmethod
from typing import List

from .models import NormalizedJob


class JobSource(ABC):
    """
    Interface dasar untuk semua job source.
    """

    name: str = "unknown"

    @abstractmethod
    def search(
        self,
        keyword: str,
        location: str = "",
        limit: int = 20,
    ) -> List[NormalizedJob]:
        """
        Mencari job berdasarkan keyword.
        """
        raise NotImplementedError

    @abstractmethod
    def get_job(
        self,
        job_url: str,
    ) -> NormalizedJob:
        """
        Mengambil satu job berdasarkan URL.
        """
        raise NotImplementedError