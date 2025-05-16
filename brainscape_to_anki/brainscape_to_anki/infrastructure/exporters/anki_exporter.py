import csv
import re
from pathlib import Path

from brainscape_to_anki.domain.interfaces.exporter import ExporterInterface
from brainscape_to_anki.domain.models.deck import Deck


class AnkiExporter(ExporterInterface):
    def export(self, deck: Deck, output_path: Path) -> Path:
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)

        sanitized_title = self._sanitize_filename(deck.title)
        file_path = output_path / f"{sanitized_title}.csv"

        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

            for flashcard in deck.flashcards:
                writer.writerow([flashcard.front, flashcard.back])

        return file_path

    def _sanitize_filename(self, filename: str) -> str:
        sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)
        return sanitized
