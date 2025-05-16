import asyncio
import tkinter as tk
from pathlib import Path
from threading import Thread
from tkinter import filedialog
from typing import Dict, List, Optional

import customtkinter as ctk
from tkinterdnd2 import TkinterDnD

from brainscape_to_anki.application.use_cases.scrape_to_anki import ScrapeToAnkiUseCase
from brainscape_to_anki.presentation.gui.components.simple_drop_zone import DropZone


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
