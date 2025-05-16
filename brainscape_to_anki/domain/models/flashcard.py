from dataclasses import dataclass


@dataclass(frozen=True)
class Flashcard:
    front: str
    back: str
