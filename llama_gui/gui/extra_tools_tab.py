"""
gui/extra_tools_tab.py — Extra Tools tab (PyQt6).

Five sub-tools in one tab:
  1. 🔊 TTS            — llama-tts (text-to-speech via OuteTTS)
  2. 🖼  Multimodal     — llama-mtmd-cli (vision/audio chat)
  3. 🌐 RPC Server     — llama-rpc-server (remote GPU offload)
  4. 🔢 Tokenize       — llama-tokenize (token count / IDs)
  5. ⚡ Speculative     — llama-speculative (draft model decoding)
"""

from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QFileDialog,
    QMessageBox, QTabWidget, QPlainTextEdit,
)
from PyQt6.QtCore import Qt, QProcess

from core.llama_detect import models_dir, exe_name, resolve_exe
from utils.terminal import TERMINAL, launch_in_terminal, shell_quote_list
from gui import make_scrollable, LogConsole, append_log, card


def _browse_gguf(parent, title="Select GGUF") -> str:
    p, _ = QFileDialog.getOpenFileName(parent, title, models_dir(), "GGUF (*.gguf)")
    return p or ""


def _browse_file(parent, title="Select file", filt="All Files (*)") -> str:
    p, _ = QFileDialog.getOpenFileName(parent, title, models_dir(), filt)
    return p or ""


# ── TTS ───────────────────────────────────────────────────────────────────────

class _TtsWidget(QWidget):
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

        opts = card("TTS Options (llama-tts)")
        opts_l = QGridLayout(opts)
        opts_l.setColumnStretch(1, 1)

        self.model_path    = QLineEdit()
        self.vocoder_path  = QLineEdit()
        self.output_file   = QLineEdit("output.wav")
        self.speaker_file  = QLineEdit()
        self.n_gpu         = QLineEdit("0")
        self.threads       = QLineEdit("2")

        rows = [
            ("TTS model GGUF",    self.model_path,   lambda: self.model_path.setText(_browse_gguf(self, "Select TTS model"))),
            ("Vocoder GGUF",      self.vocoder_path, lambda: self.vocoder_path.setText(_browse_gguf(self, "Select vocoder"))),
            ("Speaker file",      self.speaker_file, lambda: self.speaker_file.setText(_browse_file(self, "Select speaker", "Speaker (*.json *.bin);;All (*)"))),
            ("Output WAV file",   self.output_file,  lambda: None),  # manual entry
        ]
        for r, (lbl, widget, fn) in enumerate(rows):
            opts_l.addWidget(QLabel(lbl), r, 0, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, r, 1)
            if fn:
                btn = QPushButton("…"); btn.setFixedWidth(64); btn.clicked.connect(fn)
                opts_l.addWidget(btn, r, 2)
        for i, (lbl, widget) in enumerate([("-ngl", self.n_gpu), ("--threads", self.threads)]):
            opts_l.addWidget(QLabel(lbl), len(rows) + i, 0, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, len(rows) + i, 1)
        f.addWidget(opts)

        self.prompt_box = QPlainTextEdit()
        self.prompt_box.setPlaceholderText("Enter text to synthesize…")
        self.prompt_box.setMaximumHeight(120)
        f.addWidget(QLabel("Text to synthesize:"))
        f.addWidget(self.prompt_box)

        ef = QHBoxLayout()
        ef.addWidget(QLabel("Extra args:"))
        self.extra_args = QLineEdit()
        ef.addWidget(self.extra_args)
        f.addLayout(ef)

        run_btn = QPushButton("▶  Synthesize Speech")
        run_btn.setObjectName("PrimaryButton")
        run_btn.clicked.connect(self._run)
        f.addWidget(run_btn)
        f.addStretch(1)

    def _run(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        exe = resolve_exe("llama-tts", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error", f"{exe_name('llama-tts')} not found!")
            return
        model = self.model_path.text().strip()
        if not model:
            QMessageBox.critical(self, "Error", "TTS model is required!")
            return
        text = self.prompt_box.toPlainText().strip()
        if not text:
            QMessageBox.critical(self, "Error", "Enter text to synthesize!")
            return
        cmd = [exe, "-m", model]
        vocoder = self.vocoder_path.text().strip()
        if vocoder:
            cmd += ["--vocoder-model", vocoder]
        speaker = self.speaker_file.text().strip()
        if speaker:
            cmd += ["--speaker-file", speaker]
        out = self.output_file.text().strip()
        if out:
            cmd += ["-o", out]
        for flag, widget, default in [("-ngl", self.n_gpu, "0"), ("--threads", self.threads, "2")]:
            val = widget.text().strip()
            if val and val != default:
                cmd += [flag, val]
        cmd += ["--prompt", text]
        extra = self.extra_args.text().strip()
        if extra:
            import shlex
            cmd += shlex.split(extra)
        shell_cmd = shell_quote_list(cmd)
        self._log(f"▶ {shell_cmd}")
        if not launch_in_terminal(shell_cmd, title="llama-tts"):
            QMessageBox.critical(self, "Error", "No terminal found!")


# ── Multimodal ────────────────────────────────────────────────────────────────

class _MultimodalWidget(QWidget):
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

        opts = card("Multimodal Chat (llama-mtmd-cli)")
        opts_l = QGridLayout(opts)
        opts_l.setColumnStretch(1, 1)

        self.model_path  = QLineEdit()
        self.mmproj_path = QLineEdit()
        self.image_path  = QLineEdit()
        self.ctx         = QLineEdit("4096")
        self.n_gpu       = QLineEdit("0")
        self.threads     = QLineEdit("2")

        rows = [
            ("LLM model GGUF",        self.model_path,  lambda: self.model_path.setText(_browse_gguf(self, "Select LLM model"))),
            ("Multimodal projector GGUF", self.mmproj_path, lambda: self.mmproj_path.setText(_browse_gguf(self, "Select mmproj"))),
            ("Image / audio file",    self.image_path,  lambda: self.image_path.setText(_browse_file(self, "Select media", "Images & Audio (*.jpg *.jpeg *.png *.gif *.mp3 *.wav);;All (*)"))),
        ]
        for r, (lbl, widget, fn) in enumerate(rows):
            opts_l.addWidget(QLabel(lbl), r, 0, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, r, 1)
            btn = QPushButton("…"); btn.setFixedWidth(64); btn.clicked.connect(fn)
            opts_l.addWidget(btn, r, 2)
        for i, (lbl, widget) in enumerate([("--ctx-size", self.ctx), ("-ngl", self.n_gpu), ("--threads", self.threads)]):
            opts_l.addWidget(QLabel(lbl), len(rows) + i, 0, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, len(rows) + i, 1)
        f.addWidget(opts)

        self.prompt_box = QPlainTextEdit()
        self.prompt_box.setPlaceholderText("Enter prompt (e.g. 'What is in this image?')…")
        self.prompt_box.setMaximumHeight(100)
        f.addWidget(QLabel("Prompt:"))
        f.addWidget(self.prompt_box)

        bf = card("Flags")
        bf_l = QGridLayout(bf)
        self.cb_interactive = QCheckBox("--interactive")
        self.cb_single      = QCheckBox("--image (single image mode)")
        bf_l.addWidget(self.cb_interactive, 0, 0)
        bf_l.addWidget(self.cb_single, 0, 1)
        f.addWidget(bf)

        ef = QHBoxLayout()
        ef.addWidget(QLabel("Extra args:"))
        self.extra_args = QLineEdit()
        ef.addWidget(self.extra_args)
        f.addLayout(ef)

        run_btn = QPushButton("▶  Start Multimodal Chat")
        run_btn.setObjectName("PrimaryButton")
        run_btn.clicked.connect(self._run)
        f.addWidget(run_btn)

        self._log("🖼 Supports: LLaVA, Qwen2-VL, Gemma4V, InternVL, Pixtral, MiniCPM-V, etc.")
        f.addStretch(1)

    def _run(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        exe = resolve_exe("llama-mtmd-cli", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error", f"{exe_name('llama-mtmd-cli')} not found!")
            return
        model = self.model_path.text().strip()
        if not model:
            QMessageBox.critical(self, "Error", "LLM model is required!")
            return
        cmd = [exe, "-m", model]
        mmproj = self.mmproj_path.text().strip()
        if mmproj:
            cmd += ["--mmproj", mmproj]
        img = self.image_path.text().strip()
        if img:
            cmd += ["--image", img]
        for flag, widget, default in [("--ctx-size", self.ctx, "4096"), ("-ngl", self.n_gpu, "0"), ("--threads", self.threads, "2")]:
            val = widget.text().strip()
            if val and val != default:
                cmd += [flag, val]
        if self.cb_interactive.isChecked():
            cmd.append("--interactive")
        prompt = self.prompt_box.toPlainText().strip()
        if prompt:
            cmd += ["-p", prompt]
        extra = self.extra_args.text().strip()
        if extra:
            import shlex
            cmd += shlex.split(extra)
        shell_cmd = shell_quote_list(cmd)
        self._log(f"▶ {shell_cmd}")
        if not launch_in_terminal(shell_cmd, title="llama-mtmd-cli"):
            QMessageBox.critical(self, "Error", "No terminal found!")


# ── RPC Server ────────────────────────────────────────────────────────────────

class _RpcWidget(QWidget):
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

        opts = card("RPC Server (llama-rpc-server)")
        opts_l = QGridLayout(opts)
        opts_l.setColumnStretch(1, 1)
        self.host    = QLineEdit("0.0.0.0")
        self.port    = QLineEdit("50052")
        self.mem_gb  = QLineEdit("0")
        opts_l.addWidget(QLabel("--host"), 0, 0, Qt.AlignmentFlag.AlignRight); opts_l.addWidget(self.host, 0, 1)
        opts_l.addWidget(QLabel("--port"), 1, 0, Qt.AlignmentFlag.AlignRight); opts_l.addWidget(self.port, 1, 1)
        opts_l.addWidget(QLabel("--mem (GB, 0=auto)"), 2, 0, Qt.AlignmentFlag.AlignRight); opts_l.addWidget(self.mem_gb, 2, 1)
        f.addWidget(opts)

        self._log("🌐 RPC server allows offloading GPU layers to remote machines.")
        self._log("   On main machine: use -rpc <host>:<port> flag with llama-server/cli")

        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("▶  Start RPC Server")
        self._start_btn.setObjectName("PrimaryButton")
        self._start_btn.clicked.connect(self._run)
        self._stop_btn = QPushButton("⏹  Stop")
        self._stop_btn.setObjectName("StopButton")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop)
        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._stop_btn)
        f.addLayout(btn_row)
        f.addStretch(1)

    def _run(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        exe = resolve_exe("llama-rpc-server", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error", f"{exe_name('llama-rpc-server')} not found!")
            return
        cmd = [exe, "--host", self.host.text().strip(), "--port", self.port.text().strip()]
        mem = self.mem_gb.text().strip()
        if mem and mem != "0":
            cmd += ["--mem", mem]
        self._log(f"\n▶ {' '.join(cmd)}\n")
        proc = QProcess(self)
        proc.setProgram(cmd[0]); proc.setArguments(cmd[1:])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(self._on_read)
        proc.finished.connect(self._on_done)
        proc.errorOccurred.connect(self._on_err)
        proc.start()
        if not proc.waitForStarted(3000):
            QMessageBox.critical(self, "Error", "Failed to start RPC server!"); return
        self._proc = proc
        self._start_btn.setEnabled(False); self._stop_btn.setEnabled(True)

    def _on_read(self):
        if self._proc is None: return
        data = self._proc.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            if line: self._log(line)

    def _on_done(self, code, _):
        self._log(f"⏹ RPC server stopped (code {code})")
        self._proc = None; self._start_btn.setEnabled(True); self._stop_btn.setEnabled(False)

    def _on_err(self, err):
        self._log(f"❌ Error: {err}")
        self._proc = None; self._start_btn.setEnabled(True); self._stop_btn.setEnabled(False)

    def _stop(self):
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.terminate(); self._log("⏹ Stopped.")


# ── Tokenize ──────────────────────────────────────────────────────────────────

class _TokenizeWidget(QWidget):
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

        opts = card("Tokenizer (llama-tokenize)")
        opts_l = QGridLayout(opts)
        opts_l.setColumnStretch(1, 1)
        self.model_path = QLineEdit()
        opts_l.addWidget(QLabel("Model GGUF"), 0, 0, Qt.AlignmentFlag.AlignRight)
        opts_l.addWidget(self.model_path, 0, 1)
        btn = QPushButton("…"); btn.setFixedWidth(64)
        btn.clicked.connect(lambda: self.model_path.setText(_browse_gguf(self)))
        opts_l.addWidget(btn, 0, 2)
        f.addWidget(opts)

        self.prompt_box = QPlainTextEdit()
        self.prompt_box.setPlaceholderText("Enter text to tokenize…")
        self.prompt_box.setMaximumHeight(120)
        f.addWidget(QLabel("Input text:"))
        f.addWidget(self.prompt_box)

        bf = card("Options")
        bf_l = QGridLayout(bf)
        self.cb_ids   = QCheckBox("--ids (show token IDs)")
        self.cb_count = QCheckBox("--count (count only)")
        self.cb_no_bos = QCheckBox("--no-bos")
        bf_l.addWidget(self.cb_ids, 0, 0)
        bf_l.addWidget(self.cb_count, 0, 1)
        bf_l.addWidget(self.cb_no_bos, 0, 2)
        f.addWidget(bf)

        btn_row = QHBoxLayout()
        self._run_btn = QPushButton("▶  Tokenize")
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

    def _run(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        exe = resolve_exe("llama-tokenize", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error", f"{exe_name('llama-tokenize')} not found!")
            return
        model = self.model_path.text().strip()
        if not model:
            QMessageBox.critical(self, "Error", "Model is required!")
            return
        text = self.prompt_box.toPlainText().strip()
        if not text:
            QMessageBox.critical(self, "Error", "Input text is required!")
            return
        cmd = [exe, "-m", model, "--prompt", text]
        if self.cb_ids.isChecked():   cmd.append("--ids")
        if self.cb_count.isChecked(): cmd.append("--count")
        if self.cb_no_bos.isChecked(): cmd.append("--no-bos")
        self._log(f"\n▶ {' '.join(cmd)}\n")
        proc = QProcess(self)
        proc.setProgram(cmd[0]); proc.setArguments(cmd[1:])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(self._on_read)
        proc.finished.connect(self._on_done)
        proc.errorOccurred.connect(self._on_err)
        proc.start()
        if not proc.waitForStarted(3000):
            QMessageBox.critical(self, "Error", "Failed to start!"); return
        self._proc = proc
        self._run_btn.setEnabled(False); self._stop_btn.setEnabled(True)

    def _on_read(self):
        if self._proc is None: return
        data = self._proc.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            if line: self._log(line)

    def _on_done(self, code, _):
        self._log(f"\n{'✅ Done!' if code == 0 else f'⚠ Exited ({code})'}")
        self._proc = None; self._run_btn.setEnabled(True); self._stop_btn.setEnabled(False)

    def _on_err(self, err):
        self._log(f"❌ Error: {err}")
        self._proc = None; self._run_btn.setEnabled(True); self._stop_btn.setEnabled(False)

    def _stop(self):
        if self._proc and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.terminate(); self._log("⏹ Stopped.")


# ── Speculative ───────────────────────────────────────────────────────────────

class _SpeculativeWidget(QWidget):
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

        opts = card("Speculative Decoding (llama-speculative)")
        opts_l = QGridLayout(opts)
        opts_l.setColumnStretch(1, 1)

        self.target_model = QLineEdit()
        self.draft_model  = QLineEdit()
        self.ctx          = QLineEdit("2048")
        self.n_predict    = QLineEdit("512")
        self.n_gpu        = QLineEdit("0")
        self.threads      = QLineEdit("2")
        self.n_draft      = QLineEdit("16")

        rows = [
            ("Target model GGUF", self.target_model, lambda: self.target_model.setText(_browse_gguf(self, "Select target model"))),
            ("Draft model GGUF",  self.draft_model,  lambda: self.draft_model.setText(_browse_gguf(self, "Select draft model"))),
        ]
        for r, (lbl, widget, fn) in enumerate(rows):
            opts_l.addWidget(QLabel(lbl), r, 0, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, r, 1)
            btn = QPushButton("…"); btn.setFixedWidth(64); btn.clicked.connect(fn)
            opts_l.addWidget(btn, r, 2)
        numeric = [
            ("--ctx-size",   self.ctx),
            ("--n-predict",  self.n_predict),
            ("-ngl",         self.n_gpu),
            ("--threads",    self.threads),
            ("--draft (tokens)", self.n_draft),
        ]
        for i, (lbl, widget) in enumerate(numeric):
            opts_l.addWidget(QLabel(lbl), len(rows) + i, 0, Qt.AlignmentFlag.AlignRight)
            opts_l.addWidget(widget, len(rows) + i, 1)
        f.addWidget(opts)

        self.prompt_box = QPlainTextEdit()
        self.prompt_box.setPlaceholderText("Enter prompt…")
        self.prompt_box.setMaximumHeight(100)
        f.addWidget(QLabel("Prompt:"))
        f.addWidget(self.prompt_box)

        ef = QHBoxLayout()
        ef.addWidget(QLabel("Extra args:"))
        self.extra_args = QLineEdit()
        ef.addWidget(self.extra_args)
        f.addLayout(ef)

        run_btn = QPushButton("▶  Run Speculative Decoding")
        run_btn.setObjectName("PrimaryButton")
        run_btn.clicked.connect(self._run)
        f.addWidget(run_btn)

        self._log("⚡ Speculative decoding: draft model generates tokens, target model verifies")
        self._log("   Use a small draft model (e.g. 1B) + large target (e.g. 70B) for speedup")
        f.addStretch(1)

    def _run(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return

        # Try llama-speculative-simple first, then llama-speculative
        exe = resolve_exe("llama-speculative", self.app.bin_dir)
        if not os.path.isfile(exe):
            exe = resolve_exe("llama-speculative-simple", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(self, "Error", "llama-speculative / llama-speculative-simple not found!")
            return

        target = self.target_model.text().strip()
        draft  = self.draft_model.text().strip()
        if not target or not draft:
            QMessageBox.critical(self, "Error", "Both target and draft model are required!")
            return

        cmd = [exe, "-m", target, "-md", draft]

        for flag, widget, default in [
            ("--ctx-size",  self.ctx,       "2048"),
            ("--n-predict", self.n_predict, "512"),
            ("-ngl",        self.n_gpu,     "0"),
            ("--threads",   self.threads,   "2"),
            ("--draft",     self.n_draft,   "16"),
        ]:
            val = widget.text().strip()
            if val and val != default:
                cmd += [flag, val]

        prompt = self.prompt_box.toPlainText().strip()
        if prompt:
            cmd += ["-p", prompt]

        extra = self.extra_args.text().strip()
        if extra:
            import shlex
            cmd += shlex.split(extra)

        shell_cmd = shell_quote_list(cmd)
        self._log(f"▶ {shell_cmd}")
        if not launch_in_terminal(shell_cmd, title="llama-speculative"):
            QMessageBox.critical(self, "Error", "No terminal found!")


# ── Main ExtraToolsTab ────────────────────────────────────────────────────────

class ExtraToolsTab(QWidget):
    def __init__(self, app: QWidget):
        super().__init__()
        self.app = app
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        btn_bin = QPushButton("📂  Select llama.cpp build/bin (Shared)")
        btn_bin.clicked.connect(self._pick_bin_dir)
        outer.addWidget(btn_bin)

        inner_tabs = QTabWidget()
        inner_tabs.setDocumentMode(True)

        self.logbox = LogConsole(height=220)

        self._tts_w    = _TtsWidget(self.app, self.logbox)
        self._mtmd_w   = _MultimodalWidget(self.app, self.logbox)
        self._rpc_w    = _RpcWidget(self.app, self.logbox)
        self._tok_w    = _TokenizeWidget(self.app, self.logbox)
        self._spec_w   = _SpeculativeWidget(self.app, self.logbox)

        inner_tabs.addTab(make_scrollable(self._tts_w),   "🔊  TTS")
        inner_tabs.addTab(make_scrollable(self._mtmd_w),  "🖼  Multimodal")
        inner_tabs.addTab(make_scrollable(self._rpc_w),   "🌐  RPC Server")
        inner_tabs.addTab(make_scrollable(self._tok_w),   "🔢  Tokenize")
        inner_tabs.addTab(make_scrollable(self._spec_w),  "⚡  Speculative")

        outer.addWidget(inner_tabs, 1)
        outer.addWidget(self.logbox)

        if TERMINAL:
            append_log(self.logbox, f"✔ Terminal: {TERMINAL}")
        else:
            append_log(self.logbox, "❌ No terminal — some features may fail")

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
