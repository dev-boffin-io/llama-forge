#!/usr/bin/env python3
"""
app.py — llama.cpp Tools GUI entry point (PyQt6 edition).

Project-root aware:
  • Script inside llama.cpp tree  → walks up to find root
  • PyInstaller onefile binary     → placed at llama.cpp root
  • Config persisted to ~/.llama_cpp_gui.json
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QPushButton, QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from core.llama_detect import (
    LLAMA_ROOT, BIN_DIR_DEFAULT,
    bin_dir_valid, load_config, save_config,
)
from gui import STYLE_SHEET
from gui.chat_tab import ChatTab
from gui.quant_tab import QuantTab
from gui.server_tab import ServerTab
from gui.converter import ConverterDialog

APP_TITLE = "llama.cpp Tools GUI  (llama-forge 2025)"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1600, 1000)
        self.setMinimumSize(1200, 700)

        # ── Config ───────────────────────────────────────────────────────
        cfg = load_config()
        saved_bin = cfg.get("bin_dir", "")
        self.bin_dir = saved_bin if bin_dir_valid(saved_bin) \
            else (BIN_DIR_DEFAULT if bin_dir_valid(BIN_DIR_DEFAULT) else "")
        self.chat_model   = cfg.get("chat_model",   "")
        self.quant_gguf   = cfg.get("quant_gguf",   "")
        self.server_model = cfg.get("server_model", "")

        # ── Tabs ─────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self._chat_tab   = ChatTab(self)
        self._quant_tab  = QuantTab(self)
        self._server_tab = ServerTab(self)

        self.tabs.addTab(self._chat_tab,   "💬  Chat (SAFE)")
        self.tabs.addTab(self._quant_tab,  "🧪  Quantize")
        self.tabs.addTab(self._server_tab, "🖥  Server")

        # "Convert Tools" button in the tab bar's top-right corner
        convert_btn = QPushButton("🔄  Convert Tools")
        convert_btn.setObjectName("PrimaryButton")
        convert_btn.clicked.connect(self._open_converter)
        self.tabs.setCornerWidget(convert_btn, Qt.Corner.TopRightCorner)

        self.setCentralWidget(self.tabs)

        self._startup_info()

    # ── helpers ──────────────────────────────────────────────────────────

    def save(self):
        save_config({
            "bin_dir":      self.bin_dir,
            "chat_model":   self.chat_model,
            "quant_gguf":   self.quant_gguf,
            "server_model": self.server_model,
        })

    def _open_converter(self):
        dlg = ConverterDialog(self)
        dlg.exec()

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

    def closeEvent(self, event):
        # Give the server tab a chance to warn about / clean up live servers.
        self._server_tab.on_app_close()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("llama-forge GUI")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE_SHEET)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
