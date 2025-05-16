import csv
import re
import logging
from pathlib import Path

from brainscape_to_anki.domain.interfaces.exporter import ExporterInterface
from brainscape_to_anki.domain.models.deck import Deck


class AnkiExporter(ExporterInterface):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def export(self, deck: Deck, output_path: Path) -> Path:
        self.logger.info(f"Exporting deck '{deck.title}' with {len(deck.flashcards)} cards to {output_path}")

        if not output_path.exists():
            self.logger.info(f"Creating output directory: {output_path}")
            output_path.mkdir(parents=True, exist_ok=True)

        sanitized_title = self._sanitize_filename(deck.title)
        file_path = output_path / f"{sanitized_title}.csv"

        self.logger.info(f"Writing to file: {file_path}")

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

                # Write header row
                writer.writerow(["Front", "Back"])

                # Write flashcards
                for i, flashcard in enumerate(deck.flashcards):
                    self.logger.debug(
                        f"Writing card {i + 1}: Front: {flashcard.front[:30]}... Back: {flashcard.back[:30]}...")
                    writer.writerow([flashcard.front, flashcard.back])

            self.logger.info(f"Successfully exported {len(deck.flashcards)} cards to {file_path}")
            return file_path

        except Exception as e:
            self.logger.error(f"Error exporting deck: {str(e)}")
            raise

    def _sanitize_filename(self, filename: str) -> str:
        # Replace invalid filename characters with underscores
        sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)

        # Limit filename length
        if len(sanitized) > 100:
            sanitized = sanitized[:97] + "..."

        return sanitized