from dataclasses import dataclass
from typing import List, Optional

from brainscape_to_anki.domain.models.flashcard import Flashcard


@dataclass
class Deck:
    title: str
    flashcards: List[Flashcard]
    url: str
    source_id: Optional[str] = None
