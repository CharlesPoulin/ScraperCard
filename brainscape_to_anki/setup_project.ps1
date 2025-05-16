# Create the full directory structure and move files to correct locations

# Create all required directories
$Directories = @(
    "brainscape_to_anki",
    "brainscape_to_anki\domain",
    "brainscape_to_anki\domain\interfaces",
    "brainscape_to_anki\domain\models",
    "brainscape_to_anki\application",
    "brainscape_to_anki\application\services",
    "brainscape_to_anki\application\use_cases",
    "brainscape_to_anki\infrastructure",
    "brainscape_to_anki\infrastructure\scrapers",
    "brainscape_to_anki\infrastructure\exporters",
    "brainscape_to_anki\presentation",
    "brainscape_to_anki\presentation\gui",
    "brainscape_to_anki\presentation\gui\components"
)

foreach ($Directory in $Directories) {
    New-Item -ItemType Directory -Path $Directory -Force
    Write-Host "Created directory: $Directory"
}

# Create empty __init__.py files in each directory
foreach ($Directory in $Directories) {
    $InitPath = Join-Path -Path $Directory -ChildPath "__init__.py"
    New-Item -ItemType File -Path $InitPath -Force
    Write-Host "Created file: $InitPath"
}

# Define file mappings (source to destination)
$FileMappings = @{
    "brainscape_to_anki\domain\models\deck.py" = @"
from dataclasses import dataclass
from typing import List, Optional

from brainscape_to_anki.domain.models.flashcard import Flashcard


@dataclass
class Deck:
    title: str
    flashcards: List[Flashcard]
    url: str
    source_id: Optional[str] = None
"@

    "brainscape_to_anki\domain\models\flashcard.py" = @"
from dataclasses import dataclass


@dataclass(frozen=True)
class Flashcard:
    front: str
    back: str
"@

    "brainscape_to_anki\domain\interfaces\scraper.py" = @"
from abc import ABC, abstractmethod
from typing import Optional

from brainscape_to_anki.domain.models.deck import Deck


class ScraperInterface(ABC):
    @abstractmethod
    async def scrape(self, url: str) -> Optional[Deck]:
        pass
"@

    "brainscape_to_anki\domain\interfaces\exporter.py" = @"
from abc import ABC, abstractmethod
from pathlib import Path

from brainscape_to_anki.domain.models.deck import Deck


class ExporterInterface(ABC):
    @abstractmethod
    def export(self, deck: Deck, output_path: Path) -> Path:
        pass
"@

    "brainscape_to_anki\application\services\export_service.py" = @"
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
"@

    "brainscape_to_anki\application\services\scraper_service.py" = @"
from typing import Optional

from brainscape_to_anki.domain.interfaces.scraper import ScraperInterface
from brainscape_to_anki.domain.models.deck import Deck


class ScraperService:
    def __init__(self, scraper: ScraperInterface):
        self.scraper = scraper

    async def scrape_deck(self, url: str) -> Optional[Deck]:
        return await self.scraper.scrape(url)
"@

    "brainscape_to_anki\application\use_cases\scrape_to_anki.py" = @"
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
"@

    "brainscape_to_anki\presentation\gui\components\drop_zone.py" = @"
import tkinter as tk
from typing import Callable, List

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD


class DropZone(ctk.CTkFrame):
    def __init__(self, master: TkinterDnD.Tk, on_drop: Callable[[List[str]], None], **kwargs):
        super().__init__(master, **kwargs)

        self.on_drop = on_drop

        self.configure(width=400, height=200, border_width=2)

        self.label = ctk.CTkLabel(
            self,
            text="Drop Brainscape links here",
            font=("Arial", 14)
        )
        self.label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self._on_drop)

    def _on_drop(self, event):
        data = event.data
        links = [link.strip() for link in data.split('\n') if link.strip()]
        valid_links = [
            link for link in links
            if "brainscape.com" in link and link.startswith(("http://", "https://"))
        ]

        if valid_links:
            self.on_drop(valid_links)
"@

    "brainscape_to_anki\presentation\gui\main_window.py" = @"
import asyncio
import tkinter as tk
from pathlib import Path
from threading import Thread
from tkinter import filedialog
from typing import Dict, List, Optional

import customtkinter as ctk
from tkinterdnd2 import TkinterDnD

from brainscape_to_anki.application.use_cases.scrape_to_anki import ScrapeToAnkiUseCase
from brainscape_to_anki.presentation.gui.components.drop_zone import DropZone


class MainWindow(TkinterDnD.Tk):
    def __init__(self, use_case: ScrapeToAnkiUseCase):
        super().__init__()

        self.use_case = use_case
        self.output_dir = Path.home() / "Downloads"
        self.active_tasks: Dict[str, Dict] = {}

        self.title("Brainscape to Anki Converter")
        self.geometry("600x500")
        self.minsize(600, 500)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self._create_header()
        self._create_drop_zone()
        self._create_progress_area()
        self._create_status_bar()

    def _create_header(self):
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        title_label = ctk.CTkLabel(
            header_frame,
            text="Brainscape to Anki Converter",
            font=("Arial", 18, "bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        output_button = ctk.CTkButton(
            header_frame,
            text="Select Output Directory",
            command=self._select_output_dir
        )
        output_button.grid(row=0, column=1, padx=10, pady=10, sticky="e")

    def _create_drop_zone(self):
        self.drop_zone = DropZone(
            self,
            on_drop=self._process_links,
            fg_color=("gray85", "gray25"),
            corner_radius=10
        )
        self.drop_zone.grid(
            row=1, column=0, padx=20, pady=10, sticky="nsew"
        )

    def _create_progress_area(self):
        self.progress_frame = ctk.CTkScrollableFrame(self)
        self.progress_frame.grid(
            row=2, column=0, padx=10, pady=10, sticky="nsew"
        )
        self.progress_frame.configure(height=150)

    def _create_status_bar(self):
        self.status_bar = ctk.CTkLabel(
            self, text="Ready", anchor="w", padx=10
        )
        self.status_bar.grid(
            row=3, column=0, padx=10, pady=(0, 10), sticky="ew"
        )

    def _select_output_dir(self):
        directory = filedialog.askdirectory(
            initialdir=self.output_dir,
            title="Select Output Directory"
        )

        if directory:
            self.output_dir = Path(directory)
            self.status_bar.configure(
                text=f"Output directory: {self.output_dir}"
            )

    def _process_links(self, links: List[str]):
        for link in links:
            if link not in self.active_tasks:
                task_frame = self._create_task_frame(link)
                self.active_tasks[link] = {
                    "frame": task_frame,
                    "status": "pending"
                }

                thread = Thread(
                    target=self._run_scraping_task,
                    args=(link,),
                    daemon=True
                )
                thread.start()

    def _create_task_frame(self, link: str) -> ctk.CTkFrame:
        task_frame = ctk.CTkFrame(self.progress_frame)
        task_frame.pack(fill="x", padx=5, pady=5, expand=True)

        task_frame.grid_columnconfigure(0, weight=1)
        task_frame.grid_columnconfigure(1, weight=0)

        link_label = ctk.CTkLabel(
            task_frame,
            text=self._truncate_link(link),
            anchor="w"
        )
        link_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        status_label = ctk.CTkLabel(
            task_frame,
            text="Pending",
            text_color="orange"
        )
        status_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")

        progress_bar = ctk.CTkProgressBar(task_frame)
        progress_bar.grid(
            row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew"
        )
        progress_bar.set(0)

        self.active_tasks[link] = {
            "frame": task_frame,
            "status_label": status_label,
            "progress_bar": progress_bar,
            "status": "pending"
        }

        return task_frame

    def _truncate_link(self, link: str, max_length: int = 50) -> str:
        if len(link) <= max_length:
            return link

        return link[:max_length - 3] + "..."

    def _run_scraping_task(self, link: str):
        if link not in self.active_tasks:
            return

        self.active_tasks[link]["status"] = "processing"
        self._update_task_status(link, "Processing", "blue", 0.2)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                self.use_case.execute(link, self.output_dir)
            )

            deck, output_path = result

            if deck and output_path:
                self.active_tasks[link]["status"] = "completed"
                self._update_task_status(
                    link,
                    f"Completed: {len(deck.flashcards)} cards",
                    "green",
                    1.0
                )
            else:
                self.active_tasks[link]["status"] = "failed"
                self._update_task_status(
                    link, "Failed to scrape", "red", 0.0
                )
        except Exception as e:
            self.active_tasks[link]["status"] = "error"
            self._update_task_status(
                link, f"Error: {str(e)[:20]}...", "red", 0.0
            )
        finally:
            loop.close()

    def _update_task_status(
        self, link: str, status_text: str, status_color: str, progress: float
    ):
        if link not in self.active_tasks:
            return

        task_data = self.active_tasks[link]

        def update():
            if "status_label" in task_data:
                task_data["status_label"].configure(
                    text=status_text, text_color=status_color
                )

            if "progress_bar" in task_data:
                task_data["progress_bar"].set(progress)

        self.after(0, update)
"@

    "brainscape_to_anki\presentation\main.py" = @"
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD

from brainscape_to_anki.application.services.export_service import ExportService
from brainscape_to_anki.application.services.scraper_service import ScraperService
from brainscape_to_anki.application.use_cases.scrape_to_anki import ScrapeToAnkiUseCase
from brainscape_to_anki.infrastructure.exporters.anki_exporter import AnkiExporter
from brainscape_to_anki.infrastructure.scrapers.brainscape_scraper import BrainscapeScraper
from brainscape_to_anki.presentation.gui.main_window import MainWindow

import os
import sys


def check_package_structure():
    """Verify all necessary directories and files exist."""
    required_dirs = [
        'brainscape_to_anki',
        'brainscape_to_anki/domain',
        'brainscape_to_anki/domain/interfaces',
        'brainscape_to_anki/domain/models',
        'brainscape_to_anki/application',
        'brainscape_to_anki/application/services',
        'brainscape_to_anki/application/use_cases',
        'brainscape_to_anki/infrastructure',
        'brainscape_to_anki/infrastructure/scrapers',
        'brainscape_to_anki/infrastructure/exporters',
        'brainscape_to_anki/presentation',
        'brainscape_to_anki/presentation/gui',
        'brainscape_to_anki/presentation/gui/components',
    ]

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    missing_dirs = []
    for directory in required_dirs:
        dir_path = os.path.join(base_dir, *directory.split('/'))
        if not os.path.isdir(dir_path):
            missing_dirs.append(directory)

    required_init_files = [f"{d}/__init__.py" for d in required_dirs]

    missing_inits = []
    for init_file in required_init_files:
        file_path = os.path.join(base_dir, *init_file.split('/'))
        if not os.path.isfile(file_path):
            missing_inits.append(init_file)

    if missing_dirs or missing_inits:
        print("Error: Missing required directories or __init__.py files:")
        for d in missing_dirs:
            print(f"- Missing directory: {d}")
        for f in missing_inits:
            print(f"- Missing file: {f}")
        print("\nPlease create these directories and files before running the application.")
        sys.exit(1)


def setup_dependency_injection():
    scraper = BrainscapeScraper()
    exporter = AnkiExporter()

    scraper_service = ScraperService(scraper)
    export_service = ExportService(exporter)

    use_case = ScrapeToAnkiUseCase(scraper_service, export_service)

    return use_case


def main():
    try:
        # Verify package structure first
        check_package_structure()

        # Setup dependencies
        use_case = setup_dependency_injection()

        # Configure customtkinter
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Start the application
        app = MainWindow(use_case)
        app.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
"@

    "brainscape_to_anki\infrastructure\scrapers\brainscape_scraper.py" = @"
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
"@

    "brainscape_to_anki\infrastructure\exporters\anki_exporter.py" = @"
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
"@
}

# Create all Python files with content
foreach ($FilePath in $FileMappings.Keys) {
    $Content = $FileMappings[$FilePath]
    New-Item -ItemType File -Path $FilePath -Force
    Set-Content -Path $FilePath -Value $Content
    Write-Host "Created file with content: $FilePath"
}

# Create pyproject.toml in the root
$PyprojectToml = @"
[tool.poetry]
name = "brainscape-to-anki"
version = "0.1.0"
description = "Convert Brainscape flashcards to Anki format"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
packages = [{include = "brainscape_to_anki"}]

[tool.poetry.dependencies]
python = "^3.10"
httpx = "^0.27.0"
beautifulsoup4 = "^4.12.2"
customtkinter = "^5.2.2"
tkinterdnd2 = "^0.3.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
black = "^24.1.0"
isort = "^5.13.2"
mypy = "^1.8.0"
pytest-cov = "^4.1.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.poetry.scripts]
brainscape-to-anki = "brainscape_to_anki.presentation.main:main"

[tool.black]
line-length = 88
target-version = ["py310"]

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
"@

New-Item -ItemType File -Path "pyproject.toml" -Force
Set-Content -Path "pyproject.toml" -Value $PyprojectToml
Write-Host "Created file: pyproject.toml"

# Create README.md in the root
$ReadmeMd = @"
# Brainscape to Anki Converter

A Python application that scrapes flashcards from Brainscape websites and converts them to Anki format (.csv).

## Features

- Scrape flashcards from Brainscape decks
- Convert to Anki-compatible CSV format
- Drag and drop multiple Brainscape links
- Simple and intuitive GUI
- One CSV file generated per link

## Requirements

- Python 3.10 or higher
- Poetry for dependency management

## Installation

1. Clone this repository
2. Install dependencies with Poetry:

```shell
poetry install
```

3. Install TkinterDnD2 (required for drag and drop functionality):

```shell
pip install git+https://github.com/pmgagne/tkinterdnd2.git
```

## Usage

1. Run the application:

```shell
poetry run brainscape-to-anki
```

2. Drag and drop Brainscape deck links into the app
3. CSV files will be created in the selected output directory (default: Downloads folder)

## Architecture

The application follows Clean Architecture principles:

- **Domain Layer**: Core business logic and entities
- **Application Layer**: Use cases and services
- **Infrastructure Layer**: Implementation details (scrapers, exporters)
- **Presentation Layer**: User interface

## License

MIT
"@

New-Item -ItemType File -Path "README.md" -Force
Set-Content -Path "README.md" -Value $ReadmeMd
Write-Host "Created file: README.md"

# Final installation instructions
Write-Host "================================================================"
Write-Host "Project structure created successfully!"
Write-Host "Next steps:"
Write-Host "1. Install project dependencies: poetry install"
Write-Host "2. Install TkinterDnD2: pip install git+https://github.com/pmgagne/tkinterdnd2.git"
Write-Host "3. Run the application: poetry run brainscape-to-anki"
Write-Host "================================================================"