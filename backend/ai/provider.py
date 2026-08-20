from abc import ABC, abstractmethod
from typing import Any, Dict


class AIProvider(ABC):
    """
    Interface standar untuk semua AI provider.
    """

    name = "unknown"
    model = "unknown"

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
    ) -> Dict[str, Any]:
        """
        Mengirim prompt dan mengembalikan JSON hasil AI.
        """
        raise NotImplementedError