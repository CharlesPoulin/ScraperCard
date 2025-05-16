from abc import ABC, abstractmethod
from typing import Optional

from brainscape_to_anki.domain.models.deck import Deck


class ScraperInterface(ABC):
    @abstractmethod
    async def scrape(self, url: str) -> Optional[Deck]:
        pass
