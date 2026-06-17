"""
gui/perplexity_tab.py — Perplexity (llama-perplexity) tab (PyQt6).

Measures model quality via perplexity (PPL) on a text dataset.
Useful for comparing quality before/after quantization.

Runs llama-perplexity in background via QProcess, streams output live.
"""

from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QProcess

from core.llama_detect import models_dir, exe_name, resolve_exe
from gui import make_scrollable, LogConsole, append_log, card


def _default_browse_dir(current: str) -> str:
    if current and os.path.exists(current):
        return os.path.dirname(current)
    return os.path.expanduser("~")


class PerplexityTab(QWidget):
    def __init__(self, app: QWidget):
        super().__init__()
        self.app = app
        self._proc: QProcess | None = None
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        content = QWidget()
        f = QVBoxLayout(content)
        f.setContentsMargins(14, 14, 14, 14)
        f.setSpacing(10)

        btn_bin = QPushButton("📂  Select llama.cpp build/bin (Shared)")
        btn_bin.clicked.connect(self._pick_bin_dir)
        f.addWidget(btn_bin)

        btn_model = QPushButton("📦  Select GGUF model")
        btn_model.clicked.connect(self._pick_model)
        f.addWidget(btn_model)

        # Options
        opts = card("Perplexity Options")
        opts_l = QGridLayout(opts)
        opts_l.setColumnStretch(1, 1)

        self.train_data = QLineEdit()
        opts_l.addWidget(QLabel("-f  test data file"), 0, 0, Qt.AlignmentFlag.AlignRight)
        opts_l.addWidget(self.train_data, 0, 1)
        btn_td = QPushButton("…")
        btn_td.setFixedWidth(64)
        btn_td.clicked.connect(self._browse_data)
        opts_l.addWidget(btn_td, 0, 2)

        self.ctx     = QLineEdit("512")
        self.threads = QLineEdit("2")
        self.n_gpu   = QLineEdit("0")
        self.chunks  = QLineEdit("-1")
        self.ppl_stride = QLineEdit("0")

        numeric = [
            ("--ctx-size",   self.ctx),
            ("--threads",    self.threads),
            ("-ngl (GPU)",   self.n_gpu),
            ("--chunks",     self.chunks),
            ("--ppl-stride", self.ppl_stride),
        ]
        for i, (lbl, widget) in enumerate(numeric):
            r = 1 + i // 2
            c = (i % 2) * 2
            opts_l.addWidget(QLabel(lbl), r, c, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, r, c + 1)

        f.addWidget(opts)

        # Mode selector
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self.mode = QComboBox()
        self.mode.addItems([
            "perplexity (default)",
            "hellaswag",
            "winogrande",
            "multiple-choice",
            "kl-divergence",
        ])
        mode_row.addWidget(self.mode)
        mode_row.addStretch(1)
        f.addLayout(mode_row)

        # KL divergence options
        kl = card("KL-Divergence Options (only for kl-divergence mode)")
        kl_l = QGridLayout(kl)
        kl_l.setColumnStretch(1, 1)
        self.kl_logits = QLineEdit()
        kl_l.addWidget(QLabel("--kl-divergence-base (logits file)"), 0, 0, Qt.AlignmentFlag.AlignRight)
        kl_l.addWidget(self.kl_logits, 0, 1)
        btn_kl = QPushButton("…")
        btn_kl.setFixedWidth(64)
        btn_kl.clicked.connect(self._browse_kl)
        kl_l.addWidget(btn_kl, 0, 2)
        f.addWidget(kl)

        # Bool flags
        bf = card("Flags")
        bf_l = QGridLayout(bf)
        self.cb_save_logits = QCheckBox("--save-all-logits (save logits for KL-div base)")
        bf_l.addWidget(self.cb_save_logits, 0, 0)
        f.addWidget(bf)

        # Extra
        ef = QHBoxLayout()
        ef.addWidget(QLabel("Extra args:"))
        self.extra_args = QLineEdit()
        ef.addWidget(self.extra_args)
        f.addLayout(ef)

        btn_row = QHBoxLayout()
        self._run_btn = QPushButton("▶  Run Perplexity")
        self._run_btn.setObjectName("PrimaryButton")
        self._run_btn.clicked.connect(self._run)
        self._stop_btn = QPushButton("⏹  Stop")
        self._stop_btn.setObjectName("StopButton")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop)
        btn_row.addWidget(self._run_btn)
        btn_row.addWidget(self._stop_btn)
        f.addLayout(btn_row)

        f.addStretch(1)
        outer.addWidget(make_scrollable(content), 1)

        self.logbox = LogConsole(height=280)
        outer.addWidget(self.logbox)
        self._log("📐 llama-perplexity — measures model quality (lower PPL = better)")
        self._log("   Use wikitext-2 or wikitext-103 as test data for standard benchmarks")

    def _log(self, msg: str):
        append_log(self.logbox, msg)

    def _pick_bin_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select llama.cpp build/bin",
            self.app.bin_dir or os.path.expanduser("~"),
        )
        if not d:
            return
        if os.path.isfile(os.path.join(d, exe_name("llama-perplexity"))):
            self.app.bin_dir = d
            self.app.save()
            self._log(f"✔ bin dir: {d}")
        else:
            QMessageBox.critical(self, "Error",
                f"{exe_name('llama-perplexity')} not found!")

    def _pick_model(self):
        initial = _default_browse_dir(getattr(self.app, "ppl_model", "")) or models_dir()
        p, _ = QFileDialog.getOpenFileName(
            self, "Select GGUF model", initial, "GGUF (*.gguf)"
        )
        if p:
            self.app.ppl_model = p
            self.app.save()
            self._log(f"✔ Model: {p}")

    def _browse_data(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "Select test data file", models_dir(),
            "Text files (*.txt *.bin);;All Files (*)"
        )
        if p:
            self.train_data.setText(p)

    def _browse_kl(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "Select logits file", models_dir(),
            "Logits (*.logits *.bin);;All Files (*)"
        )
        if p:
            self.kl_logits.setText(p)

    def _run(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        if not getattr(self.app, "ppl_model", ""):
            QMessageBox.critical(self, "Error", "Select a GGUF model first!")
            return

        exe = resolve_exe("llama-perplexity", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error",
                f"{exe_name('llama-perplexity')} not found!\n{exe}")
            return

        cmd = [exe, "-m", self.app.ppl_model]

        data = self.train_data.text().strip()
        if not data:
            QMessageBox.critical(self, "Error", "Test data file is required!")
            return
        cmd += ["-f", data]

        mode_text = self.mode.currentText()
        if "hellaswag" in mode_text:
            cmd.append("--hellaswag")
        elif "winogrande" in mode_text:
            cmd.append("--winogrande")
        elif "multiple-choice" in mode_text:
            cmd.append("--multiple-choice")
        elif "kl-divergence" in mode_text:
            kl = self.kl_logits.text().strip()
            if kl:
                cmd += ["--kl-divergence-base", kl]
            cmd.append("--kl-divergence")

        for flag, widget, default in [
            ("--ctx-size",   self.ctx,        "512"),
            ("--threads",    self.threads,     "2"),
            ("-ngl",         self.n_gpu,       "0"),
            ("--chunks",     self.chunks,      "-1"),
            ("--ppl-stride", self.ppl_stride,  "0"),
        ]:
            val = widget.text().strip()
            if val and val != default:
                cmd += [flag, val]

        if self.cb_save_logits.isChecked():
            cmd.append("--save-all-logits")

        extra = self.extra_args.text().strip()
        if extra:
            import shlex
            cmd += shlex.split(extra)

        self._log(f"\n▶ {' '.join(cmd)}\n")

        proc = QProcess(self)
        proc.setProgram(cmd[0])
        proc.setArguments(cmd[1:])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(self._on_ready_read)
        proc.finished.connect(self._on_finished)
        proc.errorOccurred.connect(self._on_error)
        proc.start()

        if not proc.waitForStarted(3000):
            QMessageBox.critical(self, "Error", f"Failed to start {exe}")
            return

        self._proc = proc
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

    def _on_ready_read(self):
        if self._proc is None:
            return
        data = self._proc.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            if line:
                self._log(line)

    def _on_finished(self, code: int, _status):
        self._log(f"\n{'✅ Done!' if code == 0 else f'⚠ Exited (code {code})'}")
        self._proc = None
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _on_error(self, error):
        self._log(f"❌ Process error: {error}")
        self._proc = None
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _stop(self):
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.terminate()
            self._log("⏹ Stopped.")

    def startup_log(self, msg: str):
        self._log(msg)
