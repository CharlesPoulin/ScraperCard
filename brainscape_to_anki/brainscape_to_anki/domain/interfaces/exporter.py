from abc import ABC, abstractmethod
from pathlib import Path

from brainscape_to_anki.domain.models.deck import Deck


class ExporterInterface(ABC):
    @abstractmethod
    def export(self, deck: Deck, output_path: Path) -> Path:
        pass
