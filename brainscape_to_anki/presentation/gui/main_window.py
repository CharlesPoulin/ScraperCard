import asyncio
import logging
import tkinter as tk
from pathlib import Path
from threading import Thread
from tkinter import filedialog
from typing import Dict, List, Optional

import customtkinter as ctk

from brainscape_to_anki.application.use_cases.scrape_to_anki import ScrapeToAnkiUseCase
from brainscape_to_anki.domain.models.deck import Deck
from brainscape_to_anki.infrastructure.exporters.anki_exporter import AnkiExporter
from brainscape_to_anki.presentation.gui.components.simple_drop_zone import SimpleDropZone
from brainscape_to_anki.presentation.gui.components.html_processor import DirectHtmlProcessor, HtmlImportWindow


class MainWindow(tk.Tk):
    def __init__(self, use_case: ScrapeToAnkiUseCase):
        super().__init__()

        self.logger = logging.getLogger(__name__)
        self.use_case = use_case
        self.output_dir = Path.home() / "Downloads"
        self.active_tasks: Dict[str, Dict] = {}
        self.html_processor = DirectHtmlProcessor()
        self.exporter = AnkiExporter()

        self.title("Brainscape to Anki Converter")
        self.geometry("600x500")
        self.minsize(600, 500)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self._setup_ui()
        self.logger.info("Main window initialized")

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
        header_frame.grid_columnconfigure(2, weight=0)

        title_label = ctk.CTkLabel(
            header_frame,
            text="Brainscape to Anki Converter",
            font=("Arial", 18, "bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        html_button = ctk.CTkButton(
            header_frame,
            text="Import HTML",
            command=self._open_html_import
        )
        html_button.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        output_button = ctk.CTkButton(
            header_frame,
            text="Select Output Directory",
            command=self._select_output_dir
        )
        output_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")

    def _create_drop_zone(self):
        self.drop_zone = SimpleDropZone(
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
            self.logger.info(f"Output directory set to: {self.output_dir}")

    def _open_html_import(self):
        self.logger.info("Opening HTML import window")
        import_window = HtmlImportWindow(self, self._process_html)
        import_window.focus()

    def _process_html(self, html_content: str):
        self.logger.info("Processing HTML content")

        # Create a unique identifier for this HTML content
        content_id = f"html-{len(html_content)}-{id(html_content)}"

        # Create a task frame
        task_frame = self._create_task_frame(content_id, "HTML Import")
        self.active_tasks[content_id] = {
            "frame": task_frame,
            "status": "pending"
        }

        # Process in a separate thread
        thread = Thread(
            target=self._process_html_thread,
            args=(content_id, html_content),
            daemon=True
        )
        thread.start()

    def _process_html_thread(self, content_id: str, html_content: str):
        try:
            # Force UI update to "Processing" status
            self.update_idletasks()
            self._update_task_status_force(content_id, "Processing HTML", "blue", 0.2)

            # Extract flashcards from HTML
            title, flashcards = self.html_processor.extract_flashcards_from_html(html_content)

            if not flashcards:
                self._update_task_status_force(content_id, "No flashcards found", "red", 0.0)
                return

            # Create a deck
            deck = Deck(
                title=title,
                flashcards=flashcards,
                url="direct-html-import",
                source_id=content_id
            )

            # Export the deck
            self._update_task_status_force(content_id, "Exporting to CSV", "blue", 0.7)
            output_path = self.exporter.export(deck, self.output_dir)

            # Update status
            self._update_task_status_force(
                content_id,
                f"Completed: {len(flashcards)} cards",
                "green",
                1.0
            )

            # Log completion and update status bar
            message = f"Exported {len(flashcards)} cards to {output_path}"
            self.logger.info(message)
            self._update_status_bar(message)

        except Exception as e:
            self.logger.error(f"Error processing HTML: {str(e)}")
            self._update_task_status_force(
                content_id,
                f"Error: {str(e)[:20]}...",
                "red",
                0.0
            )

    def _update_status_bar(self, message):
        # Update the status bar with the given message
        def update():
            self.status_bar.configure(text=message)

        self.after(0, update)
        self.update_idletasks()  # Force UI update

    def _process_links(self, links: List[str]):
        for link in links:
            if link not in self.active_tasks:
                self.logger.info(f"Processing link: {link}")
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

    def _create_task_frame(self, identifier: str, display_text: str = None) -> ctk.CTkFrame:
        if display_text is None:
            display_text = self._truncate_link(identifier)

        task_frame = ctk.CTkFrame(self.progress_frame)
        task_frame.pack(fill="x", padx=5, pady=5, expand=True)

        task_frame.grid_columnconfigure(0, weight=1)
        task_frame.grid_columnconfigure(1, weight=0)

        link_label = ctk.CTkLabel(
            task_frame,
            text=display_text,
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

        self.active_tasks[identifier] = {
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
        self._update_task_status_force(link, "Processing", "blue", 0.2)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            self.logger.info(f"Executing scraping task for: {link}")
            result = loop.run_until_complete(
                self.use_case.execute(link, self.output_dir)
            )

            deck, output_path = result

            if deck and output_path:
                self.active_tasks[link]["status"] = "completed"
                self._update_task_status_force(
                    link,
                    f"Completed: {len(deck.flashcards)} cards",
                    "green",
                    1.0
                )
                message = f"Task completed: {len(deck.flashcards)} cards exported to {output_path}"
                self.logger.info(message)
                self._update_status_bar(message)
            else:
                self.active_tasks[link]["status"] = "failed"
                self._update_task_status_force(
                    link, "Failed to scrape", "red", 0.0
                )
                self.logger.error(f"Task failed: Could not scrape {link}")
        except Exception as e:
            self.active_tasks[link]["status"] = "error"
            self._update_task_status_force(
                link, f"Error: {str(e)[:20]}...", "red", 0.0
            )
            self.logger.exception(f"Error during scraping task: {str(e)}")
        finally:
            loop.close()

    def _update_task_status(
            self, identifier: str, status_text: str, status_color: str, progress: float
    ):
        """Regular update method using after() - can be unreliable"""
        if identifier not in self.active_tasks:
            return

        task_data = self.active_tasks[identifier]

        def update():
            if "status_label" in task_data:
                task_data["status_label"].configure(
                    text=status_text, text_color=status_color
                )

            if "progress_bar" in task_data:
                task_data["progress_bar"].set(progress)

        self.after(0, update)

    def _update_task_status_force(
            self, identifier: str, status_text: str, status_color: str, progress: float
    ):
        """Enhanced update method using direct updates and forced refresh"""
        if identifier not in self.active_tasks:
            self.logger.warning(f"Tried to update unknown task: {identifier}")
            return

        task_data = self.active_tasks[identifier]
        self.logger.info(f"Updating task {identifier} to status: {status_text}")

        # Update in main thread directly
        def update():
            if "status_label" in task_data:
                task_data["status_label"].configure(
                    text=status_text, text_color=status_color
                )
            else:
                self.logger.warning(f"No status_label for task: {identifier}")

            if "progress_bar" in task_data:
                task_data["progress_bar"].set(progress)
            else:
                self.logger.warning(f"No progress_bar for task: {identifier}")

            # Force UI refresh
            self.update_idletasks()

        # Schedule in mainloop and force update
        self.after(0, update)
        self.update_idletasks()  # Force UI update immediately