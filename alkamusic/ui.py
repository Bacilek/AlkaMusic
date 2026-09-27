"""The single application window."""

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from .engine import Engine, Job, parse_input

FONT = "Segoe UI"
BG = "#FFFFFF"
TEXT = "#1F1F1F"
MUTED = "#7A7A7A"
ACCENT = "#2E7D5B"
ACCENT_HOVER = "#256A4C"
ERROR = "#C0392B"
WARN = "#B8860B"

ICONS = {Job.WAITING: "·", Job.SEARCHING: "…", Job.DOWNLOADING: "↓", Job.DONE: "✓", Job.FAILED: "✗"}


class Row:
    """One song in the list. Plain tk labels - they stay fast with hundreds of rows."""

    def __init__(self, parent, job, on_retry):
        self.job = job
        self.on_retry = on_retry
        self.frame = tk.Frame(parent, bg=BG)
        self.frame.pack(fill="x", pady=3)
        self.icon = tk.Label(self.frame, font=(FONT, 16, "bold"), bg=BG, width=2)
        self.icon.pack(side="left")
        self.name = tk.Label(self.frame, font=(FONT, 14), bg=BG, fg=TEXT, anchor="w")
        self.name.pack(side="left", fill="x", expand=True)
        self.info = tk.Label(self.frame, font=(FONT, 13), bg=BG, fg=MUTED)
        self.info.pack(side="right", padx=(8, 4))
        self.retry = None
        self._shown = None

    def refresh(self):
        j = self.job
        shown = (j.state, j.name, int(j.progress * 100), j.note, j.uncertain)
        if shown == self._shown:
            return
        self._shown = shown

        self.icon.config(text=ICONS[j.state], fg={Job.DONE: ACCENT, Job.FAILED: ERROR}.get(j.state, MUTED))
        self.name.config(text=j.name, fg=MUTED if j.state == Job.WAITING else TEXT)
        info = {
            Job.WAITING: "čeká",
            Job.SEARCHING: "hledám",
            Job.DOWNLOADING: f"{j.progress:.0%}",
            Job.DONE: j.note or ("zkontroluj, jestli sedí" if j.uncertain else ""),
            Job.FAILED: j.note,
        }[j.state]
        self.info.config(text=info, fg=WARN if j.state == Job.DONE and j.uncertain and not j.note else MUTED)

        if j.state == Job.FAILED and not self.retry:
            self.retry = ctk.CTkButton(
                self.frame, text="Zkusit znovu", width=110, height=28, font=(FONT, 13),
                fg_color="transparent", border_width=1, border_color=ACCENT, text_color=ACCENT,
                hover_color="#EAF4EF", command=lambda: self.on_retry(self),
            )
            self.retry.pack(side="right")
        elif j.state != Job.FAILED and self.retry:
            self.retry.destroy()
            self.retry = None


class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")
        super().__init__(fg_color=BG)
        self.title("AlkaMusic")
        icon = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent)) / "assets" / "icon.ico"
        if icon.exists():
            self.after(250, lambda: self.iconbitmap(icon))  # CTk overrides an icon set too early
        self.geometry("760x760")
        self.minsize(520, 520)

        self.engine = Engine()
        self.rows = []

        pad = {"padx": 28}
        ctk.CTkLabel(
            self, text="Napiš písničky, odděl je středníkem  ;", font=(FONT, 22, "bold"), text_color=TEXT
        ).pack(anchor="w", pady=(24, 8), **pad)

        self.input = ctk.CTkTextbox(
            self, height=130, font=(FONT, 17), wrap="word", border_width=2,
            border_color="#D0D0D0", fg_color="#FAFAFA", text_color=TEXT, corner_radius=10,
        )
        self.input.pack(fill="x", **pad)
        self.input.bind("<Control-Return>", self._start)
        self.input.focus_set()

        self.button = ctk.CTkButton(
            self, text="Stáhnout", height=52, width=240, font=(FONT, 20, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=10, command=self._start,
        )
        self.button.pack(pady=16)

        self.status = ctk.CTkLabel(self, text="", font=(FONT, 14), text_color=MUTED, wraplength=680)
        self.status.pack(**pad)

        self.list = ctk.CTkScrollableFrame(
            self, fg_color=BG, scrollbar_button_color="#E4E4E4", scrollbar_button_hover_color="#C8C8C8"
        )
        self.list.pack(fill="both", expand=True, pady=(4, 0), **pad)

        bottom = ctk.CTkFrame(self, fg_color=BG)
        bottom.pack(fill="x", pady=(8, 20), **pad)
        self.summary = ctk.CTkLabel(bottom, text="", font=(FONT, 15), text_color=TEXT)
        self.summary.pack(side="left")
        ctk.CTkButton(
            bottom, text="Otevřít složku", height=38, font=(FONT, 15), fg_color="transparent",
            border_width=1, border_color=ACCENT, text_color=ACCENT, hover_color="#EAF4EF",
            command=self._open_folder,
        ).pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.engine.start_setup()
        self._tick()

    def _start(self, _event=None):
        items = parse_input(self.input.get("1.0", "end"))
        if self.engine.setup_failed:
            self.engine.start_setup()
        if not items:
            return "break"
        self.input.delete("1.0", "end")
        for query in items:
            job = Job(query)
            self.rows.append(Row(self.list, job, self._retry))
            self.engine.add(job)
        return "break"

    def _retry(self, row):
        if self.engine.setup_failed:
            self.engine.start_setup()
        self.engine.add(row.job)

    def _tick(self):
        for row in self.rows:
            row.refresh()
        self.status.configure(text=self.engine.status)

        if self.rows:
            jobs = [r.job for r in self.rows]
            finished = sum(j.state in (Job.DONE, Job.FAILED) for j in jobs)
            ok = sum(j.state == Job.DONE for j in jobs)
            if finished < len(jobs):
                self.summary.configure(text=f"Staženo {ok} z {len(jobs)}")
            else:
                self.summary.configure(text=f"Hotovo! {ok} z {len(jobs)} písniček je ve složce Hudba\\AlkaMusic.")
        self.after(250, self._tick)

    def _busy(self):
        return any(r.job.state in (Job.WAITING, Job.SEARCHING, Job.DOWNLOADING) for r in self.rows)

    def _open_folder(self):
        self.engine.out_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(self.engine.out_dir)

    def _close(self):
        if not self._busy() or messagebox.askyesno("AlkaMusic", "Ještě se stahuje. Opravdu zavřít?"):
            self.destroy()
