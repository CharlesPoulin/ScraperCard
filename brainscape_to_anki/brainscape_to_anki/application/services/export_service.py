from pathlib import Path
from typing import Optional

from brainscape_to_anki.domain.interfaces.exporter import ExporterInterface
from brainscape_to_anki.domain.models.deck import Deck


class ExportService:
    def __init__(self, exporter: ExporterInterface):
        self.exporter = exporter

    def export_deck(self, deck: Deck, output_dir: Path) -> Optional[Path]:
        try:
            return self.exporter.export(deck, output_dir)
        except Exception:
            return None
