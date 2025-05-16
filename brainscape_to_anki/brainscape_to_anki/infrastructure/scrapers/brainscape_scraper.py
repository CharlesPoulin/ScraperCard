import asyncio
import re
from typing import Dict, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from brainscape_to_anki.domain.interfaces.scraper import ScraperInterface
from brainscape_to_anki.domain.models.deck import Deck
from brainscape_to_anki.domain.models.flashcard import Flashcard


class BrainscapeScraper(ScraperInterface):
    async def scrape(self, url: str) -> Optional[Deck]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                title = self._extract_title(soup)
                deck_id = self._extract_deck_id(url)

                if not deck_id:
                    return None

                flashcards = await self._extract_flashcards(client, deck_id)

                if not flashcards:
                    return None

                return Deck(
                    title=title,
                    flashcards=flashcards,
                    url=url,
                    source_id=deck_id
                )
            except (httpx.HTTPError, asyncio.TimeoutError):
                return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_element = soup.find("h1", class_="deck-title") or soup.find("title")
        if title_element:
            return title_element.text.strip()
        return "Brainscape Deck"

    def _extract_deck_id(self, url: str) -> Optional[str]:
        pattern = r"brainscape\.com/(?:decks|packs)/(\d+)"
        match = re.search(pattern, url)
        return match.group(1) if match else None

    async def _extract_flashcards(
        self, client: httpx.AsyncClient, deck_id: str
    ) -> List[Flashcard]:
        api_url = f"https://www.brainscape.com/api/decks/{deck_id}/cards"

        try:
            response = await client.get(api_url)
            response.raise_for_status()

            cards_data = response.json()
            return self._parse_cards_data(cards_data)
        except (httpx.HTTPError, asyncio.TimeoutError, ValueError):
            return await self._fallback_extraction(client, deck_id)

    def _parse_cards_data(self, cards_data: List[Dict]) -> List[Flashcard]:
        flashcards = []

        for card in cards_data:
            if "question" in card and "answer" in card:
                front = self._clean_html(card["question"])
                back = self._clean_html(card["answer"])
                flashcards.append(Flashcard(front=front, back=back))

        return flashcards

    async def _fallback_extraction(
        self, client: httpx.AsyncClient, deck_id: str
    ) -> List[Flashcard]:
        study_url = f"https://www.brainscape.com/study?deck_id={deck_id}"

        try:
            response = await client.get(study_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            flashcards = []

            card_elements = soup.find_all("div", class_="card")
            for card in card_elements:
                front_back = self._extract_front_back(card)
                if front_back:
                    front, back = front_back
                    flashcards.append(Flashcard(front=front, back=back))

            return flashcards
        except (httpx.HTTPError, asyncio.TimeoutError):
            return []

    def _extract_front_back(self, card_element) -> Optional[Tuple[str, str]]:
        front_element = card_element.find("div", class_="front") or card_element.find("div", class_="question")
        back_element = card_element.find("div", class_="back") or card_element.find("div", class_="answer")

        if front_element and back_element:
            front = self._clean_html(front_element.text)
            back = self._clean_html(back_element.text)
            return front, back

        return None

    def _clean_html(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text().strip()
