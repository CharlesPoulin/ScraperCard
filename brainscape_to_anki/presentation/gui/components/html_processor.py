import asyncio
import logging
import os
import re
import tkinter as tk
from pathlib import Path
from threading import Thread
from tkinter import filedialog
from typing import Dict, List, Optional, Tuple

import customtkinter as ctk
import httpx
from bs4 import BeautifulSoup

from brainscape_to_anki.domain.models.deck import Deck
from brainscape_to_anki.domain.models.flashcard import Flashcard


class DirectHtmlProcessor:
    """Utility class to directly process HTML content from Brainscape pages."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_flashcards_from_html(self, html_content: str) -> Tuple[str, List[Flashcard]]:
        """
        Extract flashcards directly from HTML content.

        Args:
            html_content: Raw HTML string from a Brainscape page

        Returns:
            A tuple containing (deck_title, list_of_flashcards)
        """
        self.logger.info("Starting direct HTML extraction...")

        # Parse HTML
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract title
        title = self._extract_title(soup)
        self.logger.info(f"Extracted title: {title}")

        # Extract flashcards
        flashcards = self._extract_flashcards_from_html(soup)
        self.logger.info(f"Extracted {len(flashcards)} flashcards")

        return title, flashcards

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

    def _extract_flashcards_from_html(self, soup: BeautifulSoup) -> List[Flashcard]:
        flashcards = []

        # Look for flashcard rows
        flashcard_rows = soup.find_all("div", class_="flashcard-row")
        self.logger.info(f"Found {len(flashcard_rows)} flashcard rows in HTML")

        for i, row in enumerate(flashcard_rows):
            self.logger.info(f"Processing HTML card {i + 1}/{len(flashcard_rows)}")

            # Try to extract from full card layout
            if "full-card" in row.get("class", []):
                # Print the raw HTML of this card for debugging
                self.logger.debug(f"Card HTML: {row}")

                # Method 1: Check for question-contents and answer-contents
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
                        self.logger.debug(f"Method 1 succeeded - Front: {front[:30]}... Back: {back[:30]}...")
                        continue

                # Method 2: Look for scf-face divs within main-fields-container
                scf_faces = row.find_all("div", class_="scf-face")
                if len(scf_faces) >= 2:
                    front = self._clean_html(scf_faces[0].get_text())
                    back = self._clean_html(scf_faces[1].get_text())
                    flashcards.append(Flashcard(front=front, back=back))
                    self.logger.debug(f"Method 2 succeeded - Front: {front[:30]}... Back: {back[:30]}...")
                    continue

                # Method 3: Look for preview-html divs
                preview_html_divs = row.find_all("div", class_="preview-html")
                if len(preview_html_divs) >= 2:
                    front = self._clean_html(preview_html_divs[0].get_text())
                    back = self._clean_html(preview_html_divs[1].get_text())
                    flashcards.append(Flashcard(front=front, back=back))
                    self.logger.debug(f"Method 3 succeeded - Front: {front[:30]}... Back: {back[:30]}...")
                    continue

            # Method 4: card-face classes
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
                    self.logger.debug(f"Method 4a succeeded - Front: {front[:30]}... Back: {back[:30]}...")
                else:
                    # Or directly from the card-face
                    front = self._clean_html(question.get_text())
                    back = self._clean_html(answer.get_text())
                    flashcards.append(Flashcard(front=front, back=back))
                    self.logger.debug(f"Method 4b succeeded - Front: {front[:30]}... Back: {back[:30]}...")
                continue

            # Method 5: Look for blurrable cards
            if "is-blurrable" in row.get("class", []):
                question = row.find("div", class_="card-face question")
                answer = row.find("div", class_="card-face answer")
                if question and answer:
                    front = self._clean_html(question.get_text())

                    # For blurred answers, we might need to look deeper
                    a_content = answer.find("div", class_="answer-content")
                    if a_content:
                        # Remove any subscription links
                        for link in a_content.find_all("a"):
                            link.decompose()
                        back = self._clean_html(a_content.get_text())
                    else:
                        back = self._clean_html(answer.get_text())

                    flashcards.append(Flashcard(front=front, back=back))
                    self.logger.debug(f"Method 5 succeeded - Front: {front[:30]}... Back: {back[:30]}...")
                    continue

            self.logger.warning(f"All methods failed for card {i + 1}")

        return flashcards

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

        # Remove common UI elements text
        text = re.sub(r'How well did you know this\?', '', text)
        text = re.sub(r'Not at all.*?Perfectly', '', text)

        # Clean up lettered options (A., B., C., etc.)
        text = re.sub(r'([A-G]\.)\s+', '', text)

        return text.strip()


class HtmlImportWindow(ctk.CTkToplevel):
    """A window for importing flashcards directly from HTML content."""

    def __init__(self, master, on_process_html):
        super().__init__(master)

        self.on_process_html = on_process_html
        self.logger = logging.getLogger(__name__)

        self.title("Import HTML Content")
        self.geometry("600x500")
        self.minsize(600, 500)

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        title_label = ctk.CTkLabel(
            header_frame,
            text="Paste Brainscape HTML Content",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)

        # Text area for HTML content
        self.html_text = ctk.CTkTextbox(self)
        self.html_text.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        load_file_button = ctk.CTkButton(
            button_frame,
            text="Load from File",
            command=self._load_from_file
        )
        load_file_button.pack(side="left", padx=10, pady=10)

        process_button = ctk.CTkButton(
            button_frame,
            text="Process HTML",
            command=self._process_html
        )
        process_button.pack(side="right", padx=10, pady=10)

    def _load_from_file(self):
        file_path = filedialog.askopenfilename(
            title="Select HTML File",
            filetypes=(
                ("HTML files", "*.html;*.htm"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            )
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.html_text.delete("1.0", tk.END)
                    self.html_text.insert("1.0", content)
                    self.logger.info(f"Loaded HTML from {file_path}")
            except Exception as e:
                self.logger.error(f"Error loading file: {str(e)}")

    def _process_html(self):
        html_content = self.html_text.get("1.0", tk.END)

        if not html_content or html_content.strip() == "":
            self.logger.warning("No HTML content to process")
            return

        self.logger.info(f"Processing HTML content ({len(html_content)} characters)")
        self.on_process_html(html_content)
        self.destroy()