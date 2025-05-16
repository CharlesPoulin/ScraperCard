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
