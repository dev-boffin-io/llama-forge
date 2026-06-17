"""
gui/lora_tab.py — LoRA & Control Vector tab (PyQt6).

Two sub-tools:
  1. 📤 Export LoRA  — llama-export-lora: merge LoRA adapter into base model
  2. 🎛  CVector      — llama-cvector-generator: generate control vectors

Both run via terminal (interactive progress display).
"""

from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QTabWidget,
    QComboBox,
)
from PyQt6.QtCore import Qt

from core.llama_detect import models_dir, exe_name, resolve_exe
from utils.terminal import TERMINAL, launch_in_terminal, shell_quote_list
from gui import make_scrollable, LogConsole, append_log, card


def _default_browse_dir(current: str) -> str:
    if current and os.path.exists(current):
        return os.path.dirname(current)
    return os.path.expanduser("~")


# ── Export LoRA sub-tab ───────────────────────────────────────────────────────

class _ExportLoraWidget(QWidget):
    def __init__(self, app, logbox: LogConsole):
        super().__init__()
        self.app = app
        self.logbox = logbox
        self._build()

    def _log(self, msg: str):
        append_log(self.logbox, msg)

    def _build(self):
        f = QVBoxLayout(self)
        f.setContentsMargins(10, 10, 10, 10)
        f.setSpacing(8)

        opts = card("Export LoRA → Merge into Base Model")
        opts_l = QGridLayout(opts)
        opts_l.setColumnStretch(1, 1)

        self.model_path  = QLineEdit()
        self.lora_path   = QLineEdit()
        self.output_path = QLineEdit()
        self.lora_scale  = QLineEdit("1.0")
        self.threads     = QLineEdit("2")

        rows = [
            ("Base model GGUF", self.model_path,  self._browse_model),
            ("LoRA adapter GGUF", self.lora_path, self._browse_lora),
            ("Output GGUF",      self.output_path, self._browse_out),
        ]
        for r, (lbl, widget, fn) in enumerate(rows):
            opts_l.addWidget(QLabel(lbl), r, 0, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, r, 1)
            btn = QPushButton("…")
            btn.setFixedWidth(64)
            btn.clicked.connect(fn)
            opts_l.addWidget(btn, r, 2)

        opts_l.addWidget(QLabel("--lora-scaled (scale factor)"), 3, 0, Qt.AlignmentFlag.AlignRight)
        opts_l.addWidget(self.lora_scale, 3, 1)
        opts_l.addWidget(QLabel("--threads"), 4, 0, Qt.AlignmentFlag.AlignRight)
        opts_l.addWidget(self.threads, 4, 1)
        f.addWidget(opts)

        ef = QHBoxLayout()
        ef.addWidget(QLabel("Extra args:"))
        self.extra_args = QLineEdit()
        ef.addWidget(self.extra_args)
        f.addLayout(ef)

        run_btn = QPushButton("▶  Export / Merge LoRA")
        run_btn.setObjectName("PrimaryButton")
        run_btn.clicked.connect(self._run)
        f.addWidget(run_btn)
        f.addStretch(1)

    def _browse_model(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select base model", models_dir(), "GGUF (*.gguf)")
        if p:
            self.model_path.setText(p)

    def _browse_lora(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select LoRA GGUF", models_dir(), "GGUF (*.gguf)")
        if p:
            self.lora_path.setText(p)

    def _browse_out(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save output GGUF", models_dir(), "GGUF (*.gguf)")
        if p:
            self.output_path.setText(p)

    def _run(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return

        exe = resolve_exe("llama-export-lora", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error", f"{exe_name('llama-export-lora')} not found!")
            return

        model = self.model_path.text().strip()
        lora  = self.lora_path.text().strip()
        out   = self.output_path.text().strip()
        if not model or not lora or not out:
            QMessageBox.critical(self, "Error", "Base model, LoRA, and output are required!")
            return

        cmd = [exe, "-m", model, "--lora", lora, "-o", out]
        scale = self.lora_scale.text().strip()
        if scale and scale != "1.0":
            cmd += ["--lora-scaled", lora, scale]
        threads = self.threads.text().strip()
        if threads and threads != "2":
            cmd += ["--threads", threads]

        extra = self.extra_args.text().strip()
        if extra:
            import shlex
            cmd += shlex.split(extra)

        shell_cmd = shell_quote_list(cmd)
        self._log(f"▶ {shell_cmd}")
        if not launch_in_terminal(shell_cmd, title="llama-export-lora"):
            QMessageBox.critical(self, "Error", "No terminal found!")


# ── CVector sub-tab ───────────────────────────────────────────────────────────

class _CVectorWidget(QWidget):
    def __init__(self, app, logbox: LogConsole):
        super().__init__()
        self.app = app
        self.logbox = logbox
        self._build()

    def _log(self, msg: str):
        append_log(self.logbox, msg)

    def _build(self):
        f = QVBoxLayout(self)
        f.setContentsMargins(10, 10, 10, 10)
        f.setSpacing(8)

        opts = card("Control Vector Generator")
        opts_l = QGridLayout(opts)
        opts_l.setColumnStretch(1, 1)

        self.model_path    = QLineEdit()
        self.output_path   = QLineEdit()
        self.positive_file = QLineEdit()
        self.negative_file = QLineEdit()
        self.n_gpu   = QLineEdit("0")
        self.threads = QLineEdit("2")
        self.n_pca   = QLineEdit("1")

        rows = [
            ("Model GGUF",         self.model_path,    self._browse_model),
            ("Output (.gguf)",     self.output_path,   self._browse_out),
            ("Positive prompts file", self.positive_file, self._browse_pos),
            ("Negative prompts file", self.negative_file, self._browse_neg),
        ]
        for r, (lbl, widget, fn) in enumerate(rows):
            opts_l.addWidget(QLabel(lbl), r, 0, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, r, 1)
            btn = QPushButton("…")
            btn.setFixedWidth(64)
            btn.clicked.connect(fn)
            opts_l.addWidget(btn, r, 2)

        numeric = [
            ("-ngl (GPU layers)", self.n_gpu),
            ("--threads",         self.threads),
            ("--n-pca-iterations", self.n_pca),
        ]
        for i, (lbl, widget) in enumerate(numeric):
            opts_l.addWidget(QLabel(lbl), len(rows) + i, 0, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, len(rows) + i, 1)
        f.addWidget(opts)

        # Method
        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("--pca-batch (PCA method):"))
        self.pca_method = QComboBox()
        self.pca_method.addItems(["pca (default)", "mean"])
        method_row.addWidget(self.pca_method)
        method_row.addStretch(1)
        f.addLayout(method_row)

        ef = QHBoxLayout()
        ef.addWidget(QLabel("Extra args:"))
        self.extra_args = QLineEdit()
        ef.addWidget(self.extra_args)
        f.addLayout(ef)

        run_btn = QPushButton("▶  Generate Control Vector")
        run_btn.setObjectName("PrimaryButton")
        run_btn.clicked.connect(self._run)
        f.addWidget(run_btn)

        self._log("🎛 Control vectors steer model behaviour (tone, style, etc.)")
        self._log("   Use positive.txt / negative.txt from tools/cvector-generator/ as examples")
        f.addStretch(1)

    def _browse_model(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select model", models_dir(), "GGUF (*.gguf)")
        if p:
            self.model_path.setText(p)

    def _browse_out(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save output", models_dir(), "GGUF (*.gguf)")
        if p:
            self.output_path.setText(p)

    def _browse_pos(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select positive prompts", models_dir(), "Text (*.txt);;All (*)")
        if p:
            self.positive_file.setText(p)

    def _browse_neg(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select negative prompts", models_dir(), "Text (*.txt);;All (*)")
        if p:
            self.negative_file.setText(p)

    def _run(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return

        exe = resolve_exe("llama-cvector-generator", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error", f"{exe_name('llama-cvector-generator')} not found!")
            return

        model = self.model_path.text().strip()
        out   = self.output_path.text().strip()
        if not model or not out:
            QMessageBox.critical(self, "Error", "Model and output paths are required!")
            return

        cmd = [exe, "-m", model, "--outfile", out]

        pos = self.positive_file.text().strip()
        neg = self.negative_file.text().strip()
        if pos:
            cmd += ["--positive-file", pos]
        if neg:
            cmd += ["--negative-file", neg]

        for flag, widget, default in [
            ("-ngl",              self.n_gpu,   "0"),
            ("--threads",         self.threads,  "2"),
            ("--n-pca-iterations", self.n_pca,  "1"),
        ]:
            val = widget.text().strip()
            if val and val != default:
                cmd += [flag, val]

        method = self.pca_method.currentText()
        if "mean" in method:
            cmd.append("--method mean")

        extra = self.extra_args.text().strip()
        if extra:
            import shlex
            cmd += shlex.split(extra)

        shell_cmd = shell_quote_list(cmd)
        self._log(f"▶ {shell_cmd}")
        if not launch_in_terminal(shell_cmd, title="llama-cvector-generator"):
            QMessageBox.critical(self, "Error", "No terminal found!")


# ── Main LoraTab ──────────────────────────────────────────────────────────────

class LoraTab(QWidget):
    def __init__(self, app: QWidget):
        super().__init__()
        self.app = app
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        # Shared bin button at top
        btn_bin = QPushButton("📂  Select llama.cpp build/bin (Shared)")
        btn_bin.clicked.connect(self._pick_bin_dir)
        outer.addWidget(btn_bin)

        inner_tabs = QTabWidget()
        inner_tabs.setDocumentMode(True)

        self.logbox = LogConsole(height=220)

        self._export_w  = _ExportLoraWidget(self.app, self.logbox)
        self._cvector_w = _CVectorWidget(self.app, self.logbox)

        inner_tabs.addTab(make_scrollable(self._export_w),  "📤  Export LoRA")
        inner_tabs.addTab(make_scrollable(self._cvector_w), "🎛  Control Vector")

        outer.addWidget(inner_tabs, 1)
        outer.addWidget(self.logbox)

        if TERMINAL:
            append_log(self.logbox, f"✔ Terminal: {TERMINAL}")
        else:
            append_log(self.logbox, "❌ No terminal found — launch will fail")

    def _pick_bin_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select llama.cpp build/bin",
            self.app.bin_dir or os.path.expanduser("~"),
        )
        if not d:
            return
        self.app.bin_dir = d
        self.app.save()
        append_log(self.logbox, f"✔ bin dir: {d}")

    def startup_log(self, msg: str):
        append_log(self.logbox, msg)
