"""
gui/bench_tab.py — llama-bench tab (PyQt6).

Runs llama-bench in the background via QProcess and streams output
directly into the log console. Supports all major llama-bench flags:
  -m / -p / -n / -ngl / -t / -b / -ub / -r / -o / --numa / -fa / -mmp / -nkvo
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


class BenchTab(QWidget):
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

        btn_model = QPushButton("📦  Select GGUF model (for Bench)")
        btn_model.clicked.connect(self._pick_model)
        f.addWidget(btn_model)

        # Core args
        core = card("Benchmark Parameters")
        core_l = QGridLayout(core)
        for c in (1, 3, 5):
            core_l.setColumnStretch(c, 1)

        self.pp       = QLineEdit("512")
        self.tg       = QLineEdit("128")
        self.n_gpu    = QLineEdit("0")
        self.threads  = QLineEdit("2")
        self.batch    = QLineEdit("512")
        self.ubatch   = QLineEdit("512")
        self.reps     = QLineEdit("5")

        rows = [
            [("-p (prompt tokens)",  self.pp),
             ("-n (gen tokens)",     self.tg),
             ("-ngl (GPU layers)",   self.n_gpu)],
            [("-t (threads)",        self.threads),
             ("-b (batch)",          self.batch),
             ("-ub (ubatch)",        self.ubatch)],
            [("-r (repetitions)",    self.reps),
             ("", None), ("", None)],
        ]
        for r, items in enumerate(rows):
            for c, (lbl, widget) in enumerate(items):
                if widget is None:
                    continue
                core_l.addWidget(QLabel(lbl), r, c * 2, Qt.AlignmentFlag.AlignRight)
                core_l.addWidget(widget, r, c * 2 + 1)
        f.addWidget(core)

        # Output format
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("-o (output format):"))
        self.out_fmt = QComboBox()
        self.out_fmt.addItems(["md", "json", "jsonl", "csv", "sql"])
        fmt_row.addWidget(self.out_fmt)
        fmt_row.addStretch(1)
        f.addLayout(fmt_row)

        # Bool flags
        bf = card("Flags")
        bf_l = QGridLayout(bf)
        self._flags: dict[str, QCheckBox] = {}
        flag_names = [
            "-fa (flash-attn)",
            "-mmp (mmap)",
            "-nkvo (no-kv-offload)",
            "--numa (NUMA)",
        ]
        for i, flag in enumerate(flag_names):
            cb = QCheckBox(flag)
            self._flags[flag] = cb
            bf_l.addWidget(cb, i // 3, i % 3)
        f.addWidget(bf)

        # Extra args
        ef = QHBoxLayout()
        ef.addWidget(QLabel("Extra args:"))
        self.extra_args = QLineEdit()
        ef.addWidget(self.extra_args)
        f.addLayout(ef)

        # Buttons
        btn_row = QHBoxLayout()
        self._run_btn = QPushButton("▶  Run Benchmark")
        self._run_btn.setObjectName("PrimaryButton")
        self._run_btn.clicked.connect(self._run_bench)
        self._stop_btn = QPushButton("⏹  Stop")
        self._stop_btn.setObjectName("StopButton")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_bench)
        btn_row.addWidget(self._run_btn)
        btn_row.addWidget(self._stop_btn)
        f.addLayout(btn_row)

        f.addStretch(1)
        outer.addWidget(make_scrollable(content), 1)

        self.logbox = LogConsole(height=280)
        outer.addWidget(self.logbox)
        self._log("📊 llama-bench — runs in background, output streams here")

    def _log(self, msg: str):
        append_log(self.logbox, msg)

    def _pick_bin_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select llama.cpp build/bin",
            self.app.bin_dir or os.path.expanduser("~"),
        )
        if not d:
            return
        if os.path.isfile(os.path.join(d, exe_name("llama-bench"))):
            self.app.bin_dir = d
            self.app.save()
            self._log(f"✔ bin dir: {d}")
        else:
            QMessageBox.critical(self, "Error",
                f"{exe_name('llama-bench')} not found in selected directory!")

    def _pick_model(self):
        initial = _default_browse_dir(getattr(self.app, "bench_model", "")) or models_dir()
        p, _ = QFileDialog.getOpenFileName(
            self, "Select GGUF model", initial, "GGUF (*.gguf)"
        )
        if p:
            self.app.bench_model = p
            self.app.save()
            self._log(f"✔ Model: {p}")

    def _run_bench(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        if not getattr(self.app, "bench_model", ""):
            QMessageBox.critical(self, "Error", "Select a GGUF model first!")
            return

        exe = resolve_exe("llama-bench", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error",
                f"{exe_name('llama-bench')} not found!\n{exe}")
            return

        cmd = [exe, "-m", self.app.bench_model]

        for flag, widget, default in [
            ("-p", self.pp,      "512"),
            ("-n", self.tg,      "128"),
            ("-ngl", self.n_gpu, "0"),
            ("-t", self.threads, "2"),
            ("-b", self.batch,   "512"),
            ("-ub", self.ubatch, "512"),
            ("-r", self.reps,    "5"),
        ]:
            val = widget.text().strip()
            if val and val != default:
                cmd += [flag, val]

        fmt = self.out_fmt.currentText()
        if fmt != "md":
            cmd += ["-o", fmt]

        # Bool flags — strip the description part after space
        for raw_flag, cb in self._flags.items():
            if cb.isChecked():
                actual = raw_flag.split()[0]
                cmd.append(actual)

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

    def _stop_bench(self):
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.terminate()
            self._log("⏹ Stopped.")

    def startup_log(self, msg: str):
        self._log(msg)
