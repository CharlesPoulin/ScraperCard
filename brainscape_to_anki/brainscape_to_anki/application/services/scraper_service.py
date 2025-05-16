from typing import Optional

from brainscape_to_anki.domain.interfaces.scraper import ScraperInterface
from brainscape_to_anki.domain.models.deck import Deck


class ScraperService:
    def __init__(self, scraper: ScraperInterface):
        self.scraper = scraper

    async def scrape_deck(self, url: str) -> Optional[Deck]:
        return await self.scraper.scrape(url)
