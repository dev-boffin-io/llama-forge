"""
gui/imatrix_tab.py — Importance Matrix (llama-imatrix) tab (PyQt6).

Generates an imatrix .dat file from a calibration dataset.
The imatrix is then used by llama-quantize for IQ quant types (iq2_xxs, etc.)
for significantly better quality at low bit rates.

Streams output live via QProcess.
"""

from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt, QProcess

from core.llama_detect import models_dir, exe_name, resolve_exe
from gui import make_scrollable, LogConsole, append_log, card


def _default_browse_dir(current: str) -> str:
    if current and os.path.exists(current):
        return os.path.dirname(current)
    return os.path.expanduser("~")


class ImatrixTab(QWidget):
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

        btn_model = QPushButton("📦  Select GGUF model (source, usually f16/f32)")
        btn_model.clicked.connect(self._pick_model)
        f.addWidget(btn_model)

        # Input options
        opts = card("Imatrix Options")
        opts_l = QGridLayout(opts)
        opts_l.setColumnStretch(1, 1)

        self.train_data = QLineEdit()
        self.output     = QLineEdit()
        self.ctx        = QLineEdit("512")
        self.threads    = QLineEdit("2")
        self.n_gpu      = QLineEdit("0")
        self.chunks     = QLineEdit("-1")
        self.ppl_stride = QLineEdit("0")
        self.ppl_out    = QLineEdit("0")

        rows = [
            ("-f  calibration data file", self.train_data, self._browse_train),
            ("-o  output .dat file",       self.output,     self._browse_output),
        ]
        for r, (lbl, widget, browse_fn) in enumerate(rows):
            opts_l.addWidget(QLabel(lbl), r, 0, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, r, 1)
            btn = QPushButton("…")
            btn.setFixedWidth(64)
            btn.clicked.connect(browse_fn)
            opts_l.addWidget(btn, r, 2)

        numeric_rows = [
            ("--ctx-size", self.ctx),
            ("--threads",  self.threads),
            ("-ngl (GPU layers)", self.n_gpu),
            ("--chunks (-1=all)", self.chunks),
            ("--ppl-stride",  self.ppl_stride),
            ("--ppl-output-type", self.ppl_out),
        ]
        base_r = len(rows)
        for i, (lbl, widget) in enumerate(numeric_rows):
            r = base_r + i // 2
            c = (i % 2) * 2
            opts_l.addWidget(QLabel(lbl), r, c, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, r, c + 1)

        f.addWidget(opts)

        # Bool flags
        bf = card("Flags")
        bf_l = QGridLayout(bf)
        self.cb_save_freq = QCheckBox("--save-freq (save every N chunks)")
        self.save_freq    = QLineEdit("0")
        self.save_freq.setPlaceholderText("0 = disabled")
        self.cb_process_output = QCheckBox("--process-output")
        self.cb_no_ppl   = QCheckBox("--no-ppl")
        bf_l.addWidget(self.cb_save_freq,      0, 0)
        bf_l.addWidget(self.save_freq,         0, 1)
        bf_l.addWidget(self.cb_process_output, 1, 0)
        bf_l.addWidget(self.cb_no_ppl,         1, 1)
        f.addWidget(bf)

        # Extra args
        ef = QHBoxLayout()
        ef.addWidget(QLabel("Extra args:"))
        self.extra_args = QLineEdit()
        ef.addWidget(self.extra_args)
        f.addLayout(ef)

        btn_row = QHBoxLayout()
        self._run_btn = QPushButton("▶  Generate Imatrix")
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
        self._log("🧮 llama-imatrix — generates importance matrix for IQ quants")
        self._log("   Tip: output .dat file → use in Quantize tab → --imatrix field")

    def _log(self, msg: str):
        append_log(self.logbox, msg)

    def _pick_bin_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select llama.cpp build/bin",
            self.app.bin_dir or os.path.expanduser("~"),
        )
        if not d:
            return
        if os.path.isfile(os.path.join(d, exe_name("llama-imatrix"))):
            self.app.bin_dir = d
            self.app.save()
            self._log(f"✔ bin dir: {d}")
        else:
            QMessageBox.critical(self, "Error",
                f"{exe_name('llama-imatrix')} not found!")

    def _pick_model(self):
        initial = _default_browse_dir(getattr(self.app, "imatrix_model", "")) or models_dir()
        p, _ = QFileDialog.getOpenFileName(
            self, "Select GGUF model", initial, "GGUF (*.gguf)"
        )
        if p:
            self.app.imatrix_model = p
            self.app.save()
            self._log(f"✔ Model: {p}")

    def _browse_train(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "Select calibration data file",
            models_dir(), "Text/Data files (*.txt *.dat *.bin);;All Files (*)"
        )
        if p:
            self.train_data.setText(p)

    def _browse_output(self):
        p, _ = QFileDialog.getSaveFileName(
            self, "Save imatrix output", models_dir(),
            "Imatrix (*.dat);;All Files (*)"
        )
        if p:
            self.output.setText(p)

    def _run(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        if not getattr(self.app, "imatrix_model", ""):
            QMessageBox.critical(self, "Error", "Select a GGUF model first!")
            return

        exe = resolve_exe("llama-imatrix", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error",
                f"{exe_name('llama-imatrix')} not found!\n{exe}")
            return

        cmd = [exe, "-m", self.app.imatrix_model]

        train = self.train_data.text().strip()
        if not train:
            QMessageBox.critical(self, "Error", "Calibration data file is required!")
            return
        cmd += ["-f", train]

        out = self.output.text().strip()
        if out:
            cmd += ["-o", out]

        for flag, widget, default in [
            ("--ctx-size",        self.ctx,        "512"),
            ("--threads",         self.threads,     "2"),
            ("-ngl",              self.n_gpu,       "0"),
            ("--chunks",          self.chunks,      "-1"),
            ("--ppl-stride",      self.ppl_stride,  "0"),
            ("--ppl-output-type", self.ppl_out,     "0"),
        ]:
            val = widget.text().strip()
            if val and val != default:
                cmd += [flag, val]

        if self.cb_process_output.isChecked():
            cmd.append("--process-output")
        if self.cb_no_ppl.isChecked():
            cmd.append("--no-ppl")
        if self.cb_save_freq.isChecked():
            sf = self.save_freq.text().strip()
            if sf and sf != "0":
                cmd += ["--save-freq", sf]

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
        self._log(f"\n{'✅ Imatrix done!' if code == 0 else f'⚠ Exited (code {code})'}")
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
