"""
gui/gguf_tools_tab.py — GGUF Tools tab (PyQt6).

Three sub-tools in one tab via inner QTabWidget:
  1. 🔀 Split     — llama-gguf-split (shard / merge)
  2. #️⃣  Hash      — llama-gguf-hash  (SHA256 / xxHash integrity check)
  3. 🏷  Metadata  — llama-gguf       (read / edit KV metadata)

All run via QProcess, streaming output to the shared log console.
"""

from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QFileDialog,
    QMessageBox, QTabWidget,
)
from PyQt6.QtCore import Qt, QProcess

from core.llama_detect import models_dir, exe_name, resolve_exe
from gui import make_scrollable, LogConsole, append_log, card


def _default_browse_dir(current: str) -> str:
    if current and os.path.exists(current):
        return os.path.dirname(current)
    return os.path.expanduser("~")


# ── Split sub-tab ─────────────────────────────────────────────────────────────

class _SplitWidget(QWidget):
    def __init__(self, app, logbox: LogConsole):
        super().__init__()
        self.app = app
        self.logbox = logbox
        self._proc: QProcess | None = None
        self._build()

    def _log(self, msg: str):
        append_log(self.logbox, msg)

    def _build(self):
        f = QVBoxLayout(self)
        f.setContentsMargins(10, 10, 10, 10)
        f.setSpacing(8)

        opts = card("Split / Merge Options")
        opts_l = QGridLayout(opts)
        opts_l.setColumnStretch(1, 1)

        self.input_path  = QLineEdit()
        self.output_dir  = QLineEdit()
        self.split_size  = QLineEdit()
        self.split_count = QLineEdit()

        rows = [
            ("Input GGUF file",    self.input_path,  self._browse_input),
            ("Output dir / prefix", self.output_dir, self._browse_output),
        ]
        for r, (lbl, widget, fn) in enumerate(rows):
            opts_l.addWidget(QLabel(lbl), r, 0, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, r, 1)
            btn = QPushButton("…")
            btn.setFixedWidth(64)
            btn.clicked.connect(fn)
            opts_l.addWidget(btn, r, 2)

        opts_l.addWidget(QLabel("--split-max-size (e.g. 5G)"), 2, 0, Qt.AlignmentFlag.AlignRight)
        opts_l.addWidget(self.split_size, 2, 1)
        opts_l.addWidget(QLabel("--split-max-tensors"), 3, 0, Qt.AlignmentFlag.AlignRight)
        opts_l.addWidget(self.split_count, 3, 1)
        f.addWidget(opts)

        # Merge mode
        bf = card("Mode")
        bf_l = QGridLayout(bf)
        self.cb_merge    = QCheckBox("--merge (merge shards back into one GGUF)")
        self.cb_no_tensor_first = QCheckBox("--no-tensor-first-split")
        bf_l.addWidget(self.cb_merge, 0, 0)
        bf_l.addWidget(self.cb_no_tensor_first, 1, 0)
        f.addWidget(bf)

        btn_row = QHBoxLayout()
        self._run_btn = QPushButton("▶  Run Split/Merge")
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

    def _browse_input(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "Select GGUF file", models_dir(), "GGUF (*.gguf)"
        )
        if p:
            self.input_path.setText(p)
            if not self.output_dir.text():
                self.output_dir.setText(os.path.dirname(p))

    def _browse_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select output directory", models_dir())
        if d:
            self.output_dir.setText(d)

    def _run(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        inp = self.input_path.text().strip()
        if not inp:
            QMessageBox.critical(self, "Error", "Input GGUF file is required!")
            return

        exe = resolve_exe("llama-gguf-split", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error", f"{exe_name('llama-gguf-split')} not found!")
            return

        cmd = [exe]
        if self.cb_merge.isChecked():
            cmd.append("--merge")
        if self.cb_no_tensor_first.isChecked():
            cmd.append("--no-tensor-first-split")

        sz = self.split_size.text().strip()
        if sz:
            cmd += ["--split-max-size", sz]
        cnt = self.split_count.text().strip()
        if cnt:
            cmd += ["--split-max-tensors", cnt]

        cmd.append(inp)
        out = self.output_dir.text().strip()
        if out:
            prefix = os.path.join(out, os.path.basename(inp).replace(".gguf", ""))
            cmd.append(prefix)

        self._log(f"\n▶ {' '.join(cmd)}\n")
        self._launch(cmd)

    def _launch(self, cmd: list[str]):
        proc = QProcess(self)
        proc.setProgram(cmd[0])
        proc.setArguments(cmd[1:])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(self._on_read)
        proc.finished.connect(self._on_done)
        proc.errorOccurred.connect(self._on_err)
        proc.start()
        if not proc.waitForStarted(3000):
            QMessageBox.critical(self, "Error", "Failed to start process!")
            return
        self._proc = proc
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

    def _on_read(self):
        if self._proc is None:
            return
        data = self._proc.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            if line:
                self._log(line)

    def _on_done(self, code: int, _):
        self._log(f"\n{'✅ Done!' if code == 0 else f'⚠ Exited ({code})'}")
        self._proc = None
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _on_err(self, err):
        self._log(f"❌ Error: {err}")
        self._proc = None
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _stop(self):
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.terminate()
            self._log("⏹ Stopped.")


# ── Hash sub-tab ──────────────────────────────────────────────────────────────

class _HashWidget(QWidget):
    def __init__(self, app, logbox: LogConsole):
        super().__init__()
        self.app = app
        self.logbox = logbox
        self._proc: QProcess | None = None
        self._build()

    def _log(self, msg: str):
        append_log(self.logbox, msg)

    def _build(self):
        f = QVBoxLayout(self)
        f.setContentsMargins(10, 10, 10, 10)
        f.setSpacing(8)

        opts = card("Hash Options")
        opts_l = QGridLayout(opts)
        opts_l.setColumnStretch(1, 1)

        self.input_path = QLineEdit()
        opts_l.addWidget(QLabel("GGUF file"), 0, 0, Qt.AlignmentFlag.AlignRight)
        opts_l.addWidget(self.input_path, 0, 1)
        btn = QPushButton("…")
        btn.setFixedWidth(64)
        btn.clicked.connect(self._browse)
        opts_l.addWidget(btn, 0, 2)
        f.addWidget(opts)

        algo_row = QHBoxLayout()
        algo_row.addWidget(QLabel("Hash algorithm:"))
        self.algo = QComboBox()
        self.algo.addItems(["sha256 (default)", "sha1", "uuid", "xxhash"])
        algo_row.addWidget(self.algo)
        algo_row.addStretch(1)
        f.addLayout(algo_row)

        btn_row = QHBoxLayout()
        self._run_btn = QPushButton("▶  Compute Hash")
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

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "Select GGUF file", models_dir(), "GGUF (*.gguf)"
        )
        if p:
            self.input_path.setText(p)

    def _run(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        inp = self.input_path.text().strip()
        if not inp:
            QMessageBox.critical(self, "Error", "GGUF file is required!")
            return

        exe = resolve_exe("llama-gguf-hash", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error", f"{exe_name('llama-gguf-hash')} not found!")
            return

        algo = self.algo.currentText().split()[0]
        cmd = [exe]
        if algo != "sha256":
            cmd += [f"--{algo}"]
        cmd.append(inp)

        self._log(f"\n▶ {' '.join(cmd)}\n")

        proc = QProcess(self)
        proc.setProgram(cmd[0])
        proc.setArguments(cmd[1:])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(self._on_read)
        proc.finished.connect(self._on_done)
        proc.errorOccurred.connect(self._on_err)
        proc.start()
        if not proc.waitForStarted(3000):
            QMessageBox.critical(self, "Error", "Failed to start process!")
            return
        self._proc = proc
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

    def _on_read(self):
        if self._proc is None:
            return
        data = self._proc.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            if line:
                self._log(line)

    def _on_done(self, code: int, _):
        self._log(f"\n{'✅ Done!' if code == 0 else f'⚠ Exited ({code})'}")
        self._proc = None
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _on_err(self, err):
        self._log(f"❌ Error: {err}")
        self._proc = None
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _stop(self):
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.terminate()
            self._log("⏹ Stopped.")


# ── Metadata sub-tab ──────────────────────────────────────────────────────────

class _MetadataWidget(QWidget):
    def __init__(self, app, logbox: LogConsole):
        super().__init__()
        self.app = app
        self.logbox = logbox
        self._proc: QProcess | None = None
        self._build()

    def _log(self, msg: str):
        append_log(self.logbox, msg)

    def _build(self):
        f = QVBoxLayout(self)
        f.setContentsMargins(10, 10, 10, 10)
        f.setSpacing(8)

        opts = card("GGUF Metadata Viewer / Editor")
        opts_l = QGridLayout(opts)
        opts_l.setColumnStretch(1, 1)

        self.input_path  = QLineEdit()
        self.output_path = QLineEdit()
        opts_l.addWidget(QLabel("Input GGUF file"), 0, 0, Qt.AlignmentFlag.AlignRight)
        opts_l.addWidget(self.input_path, 0, 1)
        b1 = QPushButton("…"); b1.setFixedWidth(64); b1.clicked.connect(self._browse_in)
        opts_l.addWidget(b1, 0, 2)

        opts_l.addWidget(QLabel("Output GGUF (for write ops)"), 1, 0, Qt.AlignmentFlag.AlignRight)
        opts_l.addWidget(self.output_path, 1, 1)
        b2 = QPushButton("…"); b2.setFixedWidth(64); b2.clicked.connect(self._browse_out)
        opts_l.addWidget(b2, 1, 2)

        # KV set
        self.kv_key   = QLineEdit()
        self.kv_key.setPlaceholderText("e.g. general.name")
        self.kv_val   = QLineEdit()
        self.kv_val.setPlaceholderText("value to write")
        opts_l.addWidget(QLabel("--set key"), 2, 0, Qt.AlignmentFlag.AlignRight)
        opts_l.addWidget(self.kv_key, 2, 1)
        opts_l.addWidget(QLabel("value"), 3, 0, Qt.AlignmentFlag.AlignRight)
        opts_l.addWidget(self.kv_val, 3, 1)
        f.addWidget(opts)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Operation:"))
        self.op = QComboBox()
        self.op.addItems(["read (dump info)", "write (set KV)", "remove KV"])
        mode_row.addWidget(self.op)
        mode_row.addStretch(1)
        f.addLayout(mode_row)

        self.extra_args = QLineEdit()
        ea_row = QHBoxLayout()
        ea_row.addWidget(QLabel("Extra args:"))
        ea_row.addWidget(self.extra_args)
        f.addLayout(ea_row)

        btn_row = QHBoxLayout()
        self._run_btn = QPushButton("▶  Run")
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

    def _browse_in(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "Select GGUF file", models_dir(), "GGUF (*.gguf)"
        )
        if p:
            self.input_path.setText(p)

    def _browse_out(self):
        p, _ = QFileDialog.getSaveFileName(
            self, "Save GGUF output", models_dir(), "GGUF (*.gguf)"
        )
        if p:
            self.output_path.setText(p)

    def _run(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        inp = self.input_path.text().strip()
        if not inp:
            QMessageBox.critical(self, "Error", "Input GGUF file is required!")
            return

        exe = resolve_exe("llama-gguf", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error", f"{exe_name('llama-gguf')} not found!")
            return

        cmd = [exe, inp]
        op = self.op.currentText()
        if "write" in op:
            key = self.kv_key.text().strip()
            val = self.kv_val.text().strip()
            out = self.output_path.text().strip()
            if not key:
                QMessageBox.critical(self, "Error", "KV key is required for write!")
                return
            if not out:
                QMessageBox.critical(self, "Error", "Output GGUF file is required for write!")
                return
            cmd += ["--set", key, val, out]
        elif "remove" in op:
            key = self.kv_key.text().strip()
            out = self.output_path.text().strip()
            if not key:
                QMessageBox.critical(self, "Error", "KV key is required for remove!")
                return
            cmd += ["--rm", key, out]

        extra = self.extra_args.text().strip()
        if extra:
            import shlex
            cmd += shlex.split(extra)

        self._log(f"\n▶ {' '.join(cmd)}\n")

        proc = QProcess(self)
        proc.setProgram(cmd[0])
        proc.setArguments(cmd[1:])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(self._on_read)
        proc.finished.connect(self._on_done)
        proc.errorOccurred.connect(self._on_err)
        proc.start()
        if not proc.waitForStarted(3000):
            QMessageBox.critical(self, "Error", "Failed to start process!")
            return
        self._proc = proc
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

    def _on_read(self):
        if self._proc is None:
            return
        data = self._proc.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            if line:
                self._log(line)

    def _on_done(self, code: int, _):
        self._log(f"\n{'✅ Done!' if code == 0 else f'⚠ Exited ({code})'}")
        self._proc = None
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _on_err(self, err):
        self._log(f"❌ Error: {err}")
        self._proc = None
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _stop(self):
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.terminate()
            self._log("⏹ Stopped.")


# ── Main GgufToolsTab ─────────────────────────────────────────────────────────

class GgufToolsTab(QWidget):
    def __init__(self, app: QWidget):
        super().__init__()
        self.app = app
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        inner_tabs = QTabWidget()
        inner_tabs.setDocumentMode(True)

        # Shared log console
        self.logbox = LogConsole(height=260)

        self._split_w = _SplitWidget(self.app, self.logbox)
        self._hash_w  = _HashWidget(self.app, self.logbox)
        self._meta_w  = _MetadataWidget(self.app, self.logbox)

        inner_tabs.addTab(make_scrollable(self._split_w), "🔀  Split / Merge")
        inner_tabs.addTab(make_scrollable(self._hash_w),  "#️⃣  Hash")
        inner_tabs.addTab(make_scrollable(self._meta_w),  "🏷  Metadata")

        outer.addWidget(inner_tabs, 1)
        outer.addWidget(self.logbox)

        append_log(self.logbox, "🗂 GGUF Tools — Split, Hash, Metadata")

    def startup_log(self, msg: str):
        append_log(self.logbox, msg)
