#!/usr/bin/env python3
"""
app.py — llama.cpp Tools GUI entry point.

Project-root aware:
  • Script inside llama.cpp tree  → walks up to find root
  • PyInstaller onefile binary     → placed at llama.cpp root
  • Config persisted to ~/.llama_cpp_gui.json
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, font as tkfont

from core.llama_detect import (
    LLAMA_ROOT, BIN_DIR_DEFAULT,
    bin_dir_valid, load_config, save_config
)
from gui import scale_font
from gui.chat_tab   import ChatTab
from gui.quant_tab  import QuantTab
from gui.server_tab import ServerTab
from gui.converter  import ConverterManager

APP_TITLE = "llama.cpp Tools GUI"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1920x900")
        self.minsize(1400, 700)

        # ── Styles & fonts ────────────────────────────────────────────
        style = ttk.Style(self)
        style.theme_use("clam")

        base_ui   = scale_font(28)
        base_mono = scale_font(26)

        df = tkfont.nametofont("TkDefaultFont")
        df.configure(size=base_ui, family="DejaVu Sans")
        self.option_add("*Font", df)

        dialog_font = tkfont.Font(family="DejaVu Sans", size=base_ui)
        self.option_add("*TkFDialog*Font",     dialog_font)
        self.option_add("*TkChooseDir*Font",   dialog_font)
        self.option_add("*Dialog*Font",        dialog_font)
        self.option_add("*Entry*Font",         dialog_font)
        self.option_add("*Listbox*Font",       dialog_font)
        self.option_add("*Label*Font",         dialog_font)
        self.option_add("*Button*Font",        dialog_font)

        self.log_font = tkfont.Font(family="DejaVu Sans Mono", size=base_mono)

        style.configure("TButton",       padding=20)
        style.configure("TNotebook",     padding=10)
        style.configure("TNotebook.Tab", padding=(20, 10))
        style.configure("TFrame",        padding=14)

        # ── Config ────────────────────────────────────────────────────
        cfg = load_config()
        saved_bin = cfg.get("bin_dir", "")
        self.bin_dir      = saved_bin if bin_dir_valid(saved_bin) \
                            else (BIN_DIR_DEFAULT if bin_dir_valid(BIN_DIR_DEFAULT) else "")
        self.chat_model   = cfg.get("chat_model",   "")
        self.quant_gguf   = cfg.get("quant_gguf",   "")
        self.server_model = cfg.get("server_model", "")

        # ── Build UI ──────────────────────────────────────────────────
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._chat_tab   = ChatTab(nb, self)
        self._quant_tab  = QuantTab(nb, self)
        self._server_tab = ServerTab(nb, self)

        # Convert Tools button (top-right, outside notebook)
        ttk.Button(self, text="Convert Tools",
                   command=self._open_converter).place(
            relx=1.0, rely=0.0, anchor="ne", x=-10, y=10
        )

        self._startup_info()

    # ── helpers ───────────────────────────────────────────────────────────

    def save(self):
        save_config({
            "bin_dir":      self.bin_dir,
            "chat_model":   self.chat_model,
            "quant_gguf":   self.quant_gguf,
            "server_model": self.server_model,
        })

    def _open_converter(self):
        ConverterManager(self)

    def _startup_info(self):
        info = f"📁 Project root: {LLAMA_ROOT}"
        self._chat_tab.startup_log(info)
        self._quant_tab.startup_log(info)
        self._server_tab.startup_log(info)
        if self.bin_dir:
            msg = f"✔ bin dir auto-set: {self.bin_dir}"
            self._chat_tab.startup_log(msg)
            self._quant_tab.startup_log(msg)
            self._server_tab.startup_log(msg)
        else:
            warn = f"⚠ build/bin not found at {BIN_DIR_DEFAULT} — select manually"
            self._chat_tab.startup_log(warn)
            self._server_tab.startup_log(warn)
        if self.chat_model:
            self._chat_tab.startup_log(f"✔ Last model: {self.chat_model}")
        if self.quant_gguf:
            self._quant_tab.startup_log(f"✔ Last GGUF: {self.quant_gguf}")
        if self.server_model:
            self._server_tab.startup_log(f"✔ Last server model: {self.server_model}")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
