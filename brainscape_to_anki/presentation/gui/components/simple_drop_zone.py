import tkinter as tk
from typing import Callable, List

import customtkinter as ctk


class SimpleDropZone(ctk.CTkFrame):
    """Alternative to DropZone that uses paste instead of drag-and-drop."""

    def __init__(self, master, on_drop: Callable[[List[str]], None], **kwargs):
        super().__init__(master, **kwargs)

        self.on_drop = on_drop

        self.configure(width=400, height=200, border_width=2)

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text="Paste Brainscape link here",
            width=300
        )
        self.entry.place(relx=0.5, rely=0.4, anchor=tk.CENTER)

        self.button = ctk.CTkButton(
            self,
            text="Add Link",
            command=self._on_button_click
        )
        self.button.place(relx=0.5, rely=0.6, anchor=tk.CENTER)

        self.label = ctk.CTkLabel(
            self,
            text="Enter Brainscape links",
            font=("Arial", 14)
        )
        self.label.place(relx=0.5, rely=0.2, anchor=tk.CENTER)

        # Handle paste event
        self.entry.bind("<Control-v>", self._on_paste)

    def _on_button_click(self):
        text = self.entry.get().strip()
        if text:
            self._process_links([text])
            self.entry.delete(0, tk.END)

    def _on_paste(self, event=None):
        # This will be called on Ctrl+V, but we'll let the Entry handle the paste
        # and then process the links after a short delay
        self.after(100, self._check_pasted_content)

    def _check_pasted_content(self):
        text = self.entry.get().strip()
        if text and "brainscape.com" in text:
            self._process_links([text])
            self.entry.delete(0, tk.END)

    def _process_links(self, links):
        valid_links = [
            link for link in links
            if "brainscape.com" in link and link.startswith(("http://", "https://"))
        ]

        if valid_links:
            self.on_drop(valid_links)