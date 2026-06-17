#!/usr/bin/env python3
"""
app.py — llama.cpp Tools GUI entry point (PyQt6 edition).

Tabs:
  💬 Chat (SAFE)     — llama-cli interactive
  🧪 Quantize        — llama-quantize
  🖥 Server          — llama-server (background)
  📊 Benchmark       — llama-bench
  🧮 Imatrix         — llama-imatrix
  📐 Perplexity      — llama-perplexity
  🗂 GGUF Tools      — llama-gguf-split / llama-gguf-hash / llama-gguf
  🔗 LoRA & CVector  — llama-export-lora / llama-cvector-generator
  🛠 Extra Tools     — TTS / Multimodal / RPC / Tokenize / Speculative
  🔄 Convert Tools   — convert_hf_to_gguf / convert_lora / convert_ggml (dialog)
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QPushButton, QWidget,
    QToolBar,
)
from PyQt6.QtCore import Qt

from core.llama_detect import (
    LLAMA_ROOT, BIN_DIR_DEFAULT,
    bin_dir_valid, load_config, save_config,
)
from gui import STYLE_SHEET
from gui.chat_tab       import ChatTab
from gui.quant_tab      import QuantTab
from gui.server_tab     import ServerTab
from gui.bench_tab      import BenchTab
from gui.imatrix_tab    import ImatrixTab
from gui.perplexity_tab import PerplexityTab
from gui.gguf_tools_tab import GgufToolsTab
from gui.lora_tab       import LoraTab
from gui.extra_tools_tab import ExtraToolsTab
from gui.converter      import ConverterDialog

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
        self.bin_dir      = saved_bin if bin_dir_valid(saved_bin) \
            else (BIN_DIR_DEFAULT if bin_dir_valid(BIN_DIR_DEFAULT) else "")
        self.chat_model   = cfg.get("chat_model",    "")
        self.quant_gguf   = cfg.get("quant_gguf",    "")
        self.server_model = cfg.get("server_model",  "")
        self.bench_model  = cfg.get("bench_model",   "")
        self.imatrix_model = cfg.get("imatrix_model", "")
        self.ppl_model    = cfg.get("ppl_model",     "")

        # ── Toolbar (Convert Tools button) ───────────────────────────────
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        # stretch spacer
        spacer = QWidget()
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy(),
            spacer.sizePolicy().verticalPolicy(),
        )
        from PyQt6.QtWidgets import QSizePolicy
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        convert_btn = QPushButton("🔄  Convert Tools")
        convert_btn.setObjectName("PrimaryButton")
        convert_btn.clicked.connect(self._open_converter)
        toolbar.addWidget(convert_btn)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # ── Tabs ─────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)
        self.tabs.tabBar().setUsesScrollButtons(True)
        self.tabs.tabBar().setExpanding(False)

        self._chat_tab       = ChatTab(self)
        self._quant_tab      = QuantTab(self)
        self._server_tab     = ServerTab(self)
        self._bench_tab      = BenchTab(self)
        self._imatrix_tab    = ImatrixTab(self)
        self._perplexity_tab = PerplexityTab(self)
        self._gguf_tools_tab = GgufToolsTab(self)
        self._lora_tab       = LoraTab(self)
        self._extra_tab      = ExtraToolsTab(self)

        # ট্যাব নাম সংক্ষিপ্ত রাখা হয়েছে যাতে সব একলাইনে দেখা যায়
        self.tabs.addTab(self._chat_tab,       "💬 Chat")
        self.tabs.addTab(self._quant_tab,      "🧪 Quantize")
        self.tabs.addTab(self._server_tab,     "🖥 Server")
        self.tabs.addTab(self._bench_tab,      "📊 Bench")
        self.tabs.addTab(self._imatrix_tab,    "🧮 Imatrix")
        self.tabs.addTab(self._perplexity_tab, "📐 Perplexity")
        self.tabs.addTab(self._gguf_tools_tab, "🗂 GGUF Tools")
        self.tabs.addTab(self._lora_tab,       "🔗 LoRA")
        self.tabs.addTab(self._extra_tab,      "🛠 Extra")

        self.setCentralWidget(self.tabs)
        self._startup_info()

    # ── helpers ──────────────────────────────────────────────────────────

    def save(self):
        save_config({
            "bin_dir":       self.bin_dir,
            "chat_model":    self.chat_model,
            "quant_gguf":    self.quant_gguf,
            "server_model":  self.server_model,
            "bench_model":   self.bench_model,
            "imatrix_model": self.imatrix_model,
            "ppl_model":     self.ppl_model,
        })

    def _open_converter(self):
        dlg = ConverterDialog(self)
        dlg.exec()

    def _startup_info(self):
        info = f"📁 Project root: {LLAMA_ROOT}"
        all_tabs = [
            self._chat_tab, self._quant_tab, self._server_tab,
            self._bench_tab, self._imatrix_tab, self._perplexity_tab,
            self._gguf_tools_tab, self._lora_tab, self._extra_tab,
        ]
        for tab in all_tabs:
            tab.startup_log(info)

        if self.bin_dir:
            msg = f"✔ bin dir auto-set: {self.bin_dir}"
            for tab in all_tabs:
                tab.startup_log(msg)
        else:
            warn = f"⚠ build/bin not found at {BIN_DIR_DEFAULT} — select manually"
            for tab in all_tabs:
                tab.startup_log(warn)

        if self.chat_model:
            self._chat_tab.startup_log(f"✔ Last model: {self.chat_model}")
        if self.quant_gguf:
            self._quant_tab.startup_log(f"✔ Last GGUF: {self.quant_gguf}")
        if self.server_model:
            self._server_tab.startup_log(f"✔ Last server model: {self.server_model}")
        if self.bench_model:
            self._bench_tab.startup_log(f"✔ Last bench model: {self.bench_model}")
        if self.imatrix_model:
            self._imatrix_tab.startup_log(f"✔ Last imatrix model: {self.imatrix_model}")
        if self.ppl_model:
            self._perplexity_tab.startup_log(f"✔ Last PPL model: {self.ppl_model}")

    def closeEvent(self, event):
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
