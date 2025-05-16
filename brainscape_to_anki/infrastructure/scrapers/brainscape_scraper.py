import asyncio
import re
from typing import Dict, List, Optional, Tuple
import logging

import httpx
from bs4 import BeautifulSoup

from brainscape_to_anki.domain.interfaces.scraper import ScraperInterface
from brainscape_to_anki.domain.models.deck import Deck
from brainscape_to_anki.domain.models.flashcard import Flashcard


class BrainscapeScraper(ScraperInterface):
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    async def scrape(self, url: str) -> Optional[Deck]:
        self.logger.info(f"Starting to scrape URL: {url}")

        async with httpx.AsyncClient() as client:
            try:
                self.logger.info("Sending HTTP request...")
                response = await client.get(url)
                response.raise_for_status()

                self.logger.info("Request successful, parsing HTML...")
                soup = BeautifulSoup(response.text, "html.parser")

                title = self._extract_title(soup)
                self.logger.info(f"Extracted title: {title}")

                deck_id = self._extract_deck_id(url)
                self.logger.info(f"Extracted deck ID: {deck_id}")

                if not deck_id:
                    self.logger.error("Failed to extract deck ID")
                    return None

                flashcards = await self._extract_flashcards(client, deck_id, soup)

                if not flashcards:
                    self.logger.error("Failed to extract flashcards")
                    return None

                self.logger.info(f"Successfully extracted {len(flashcards)} flashcards")

                return Deck(
                    title=title,
                    flashcards=flashcards,
                    url=url,
                    source_id=deck_id
                )
            except (httpx.HTTPError, asyncio.TimeoutError) as e:
                self.logger.error(f"HTTP error occurred: {str(e)}")
                return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        # Try different potential title elements
        title_element = (
                soup.find("h1", class_="deck-title") or
                soup.find("h1") or
                soup.find("title") or
                soup.find("meta", property="og:title")
        )

        if title_element:
            if title_element.get("content"):  # For meta tags
                return title_element["content"].strip()
            return title_element.text.strip()

        self.logger.warning("Could not find title, using default")
        return "Brainscape Deck"

    def _extract_deck_id(self, url: str) -> Optional[str]:
        # Try multiple patterns to match deck IDs
        patterns = [
            r"brainscape\.com/(?:decks|packs)/(\d+)",
            r"brainscape\.com/learn/(\d+)",
            r"brainscape\.com/flashcards/([^/]+)",
            r"id=(\d+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        self.logger.warning("Could not extract deck ID from URL")
        # If we can't extract an ID, we'll use a timestamp as a fallback
        return f"unknown-{asyncio.get_event_loop().time()}"

    async def _extract_flashcards(
            self, client: httpx.AsyncClient, deck_id: str, soup: BeautifulSoup = None
    ) -> List[Flashcard]:
        self.logger.info("Attempting to extract flashcards...")

        # First try to use API if available
        try:
            self.logger.info(f"Trying API extraction for deck {deck_id}")
            api_url = f"https://www.brainscape.com/api/decks/{deck_id}/cards"
            response = await client.get(api_url)
            response.raise_for_status()

            cards_data = response.json()
            self.logger.info(f"API returned {len(cards_data)} cards")
            return self._parse_cards_data(cards_data)
        except (httpx.HTTPError, asyncio.TimeoutError, ValueError) as e:
            self.logger.warning(f"API extraction failed: {str(e)}, trying fallback...")

        # If API fails or soup is provided, use HTML extraction
        if soup:
            self.logger.info("Attempting HTML extraction")
            return self._extract_flashcards_from_html(soup)
        else:
            self.logger.info("Attempting fallback extraction by loading study page")
            return await self._fallback_extraction(client, deck_id)

    def _parse_cards_data(self, cards_data: List[Dict]) -> List[Flashcard]:
        flashcards = []

        for i, card in enumerate(cards_data):
            self.logger.info(f"Processing API card {i + 1}/{len(cards_data)}")
            if "question" in card and "answer" in card:
                front = self._clean_html(card["question"])
                back = self._clean_html(card["answer"])
                flashcards.append(Flashcard(front=front, back=back))
            else:
                self.logger.warning(f"Card {i + 1} missing question or answer: {card.keys()}")

        return flashcards

    def _extract_flashcards_from_html(self, soup: BeautifulSoup) -> List[Flashcard]:
        flashcards = []

        # Look for flashcard rows
        flashcard_rows = soup.find_all("div", class_="flashcard-row")
        self.logger.info(f"Found {len(flashcard_rows)} flashcard rows in HTML")

        for i, row in enumerate(flashcard_rows):
            self.logger.info(f"Processing HTML card {i + 1}/{len(flashcard_rows)}")

            # Try to extract from full card layout
            if "full-card" in row.get("class", []):
                # First method: Check for question-contents and answer-contents
                question_div = row.find("div", class_="question-contents")
                answer_div = row.find("div", class_="answer-contents")

                if question_div and answer_div:
                    # If found, extract from main-fields-container
                    q_container = question_div.find("div", class_="main-fields-container")
                    a_container = answer_div.find("div", class_="main-fields-container")

                    if q_container and a_container:
                        front = self._clean_html(q_container.get_text())
                        back = self._clean_html(a_container.get_text())
                        flashcards.append(Flashcard(front=front, back=back))
                        continue

            # Alternative method: card-face classes
            question = row.find("div", class_="card-face question")
            answer = row.find("div", class_="card-face answer")

            if question and answer:
                # Try to extract from answer-content/question-content
                q_content = question.find("div", class_="question-content")
                a_content = answer.find("div", class_="answer-content")

                if q_content and a_content:
                    front = self._clean_html(q_content.get_text())
                    back = self._clean_html(a_content.get_text())
                    flashcards.append(Flashcard(front=front, back=back))
                else:
                    # Or directly from the card-face
                    front = self._clean_html(question.get_text())
                    back = self._clean_html(answer.get_text())
                    flashcards.append(Flashcard(front=front, back=back))
            else:
                # Try to find questions and answers by looking for Q/A indicators
                q_indicator = row.find("div", class_="flashcard-type-indicator", text="Q")
                a_indicator = row.find("div", class_="flashcard-type-indicator", text="A")

                if q_indicator and a_indicator:
                    # Navigate up to the parent container then find the content
                    q_header = q_indicator.parent
                    a_header = a_indicator.parent

                    if q_header and a_header:
                        q_content = q_header.find_next_sibling("div", class_="main-fields-container")
                        a_content = a_header.find_next_sibling("div", class_="main-fields-container")

                        if q_content and a_content:
                            front = self._clean_html(q_content.get_text())
                            back = self._clean_html(a_content.get_text())
                            flashcards.append(Flashcard(front=front, back=back))

            # If we still haven't found a card, look for scf-face divs
            if not (question and answer):
                scf_faces = row.find_all("div", class_="scf-face")
                if len(scf_faces) >= 2:
                    front = self._clean_html(scf_faces[0].get_text())
                    back = self._clean_html(scf_faces[1].get_text())
                    flashcards.append(Flashcard(front=front, back=back))

        self.logger.info(f"Extracted {len(flashcards)} flashcards from HTML")
        return flashcards

    async def _fallback_extraction(
            self, client: httpx.AsyncClient, deck_id: str
    ) -> List[Flashcard]:
        self.logger.info(f"Performing fallback extraction for deck {deck_id}")

        try:
            # Try study page
            study_url = f"https://www.brainscape.com/study?deck_id={deck_id}"
            self.logger.info(f"Accessing study URL: {study_url}")

            response = await client.get(study_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            return self._extract_flashcards_from_html(soup)
        except (httpx.HTTPError, asyncio.TimeoutError) as e:
            self.logger.error(f"Fallback extraction failed: {str(e)}")
            return []

    def _extract_front_back(self, card_element) -> Optional[Tuple[str, str]]:
        # Try multiple selector patterns to find question/answer content
        front_element = (
                card_element.find("div", class_="front") or
                card_element.find("div", class_="question") or
                card_element.find("div", class_="question-content") or
                card_element.find("div", class_="card-face question")
        )

        back_element = (
                card_element.find("div", class_="back") or
                card_element.find("div", class_="answer") or
                card_element.find("div", class_="answer-content") or
                card_element.find("div", class_="card-face answer")
        )

        if front_element and back_element:
            front = self._clean_html(front_element.text)
            back = self._clean_html(back_element.text)
            return front, back

        return None

    def _clean_html(self, html_content: str) -> str:
        # Clean HTML content to get plain text
        if not html_content:
            return ""

        # First parse with BeautifulSoup if it's HTML
        if "<" in html_content and ">" in html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            text = soup.get_text()
        else:
            text = html_content

        # Clean up whitespace and line breaks
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text