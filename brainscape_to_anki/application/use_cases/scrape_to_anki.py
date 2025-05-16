from pathlib import Path
from typing import Optional, Tuple

from brainscape_to_anki.application.services.export_service import ExportService
from brainscape_to_anki.application.services.scraper_service import ScraperService
from brainscape_to_anki.domain.models.deck import Deck


class ScrapeToAnkiUseCase:
    def __init__(self, scraper_service: ScraperService, export_service: ExportService):
        self.scraper_service = scraper_service
        self.export_service = export_service
    
    async def execute(self, url: str, output_dir: Path) -> Tuple[Optional[Deck], Optional[Path]]:
        deck = await self.scraper_service.scrape_deck(url)
        
        if not deck:
            return None, None
        
        output_path = self.export_service.export_deck(deck, output_dir)
        
        return deck, output_path
