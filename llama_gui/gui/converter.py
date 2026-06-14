"""
gui/converter.py — Converter Manager dialog (PyQt6).
"""

from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import QProcess

from core.llama_detect import LLAMA_ROOT, models_dir
from core.converter_logic import (
    SCRIPTS, OUTTYPE_VALUES, DEFAULT_OUTTYPE,
    HF_BOOL_FLAGS, HF_TEXT_FLAGS, build_convert_args,
)
from utils.terminal import shell_quote_list
from gui import make_scrollable, LogConsole, append_log, card


class ConverterDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("llama.cpp Converter Manager")
        self.resize(1400, 900)
        self.setMinimumSize(1000, 640)

        self._proc: QProcess | None = None
        self._build()
        self._on_script_change(SCRIPTS[0])

    # ── build ────────────────────────────────────────────────────────────

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        content = QWidget()
        frm = QGridLayout(content)
        frm.setContentsMargins(14, 14, 14, 14)
        frm.setVerticalSpacing(10)
        frm.setHorizontalSpacing(8)
        frm.setColumnStretch(1, 1)

        r = 0

        # llama.cpp dir
        self.llama_dir = QLineEdit(LLAMA_ROOT)
        frm.addWidget(QLabel("llama.cpp Directory"), r, 0)
        frm.addWidget(self.llama_dir, r, 1)
        btn = QPushButton("Browse")
        btn.clicked.connect(self._browse_llama)
        frm.addWidget(btn, r, 2)
        r += 1

        # script
        self.script_cb = QComboBox()
        self.script_cb.addItems(SCRIPTS)
        self.script_cb.currentTextChanged.connect(self._on_script_change)
        frm.addWidget(QLabel("Convert Script"), r, 0)
        frm.addWidget(self.script_cb, r, 1, 1, 2)
        r += 1

        # input
        self.input_path = QLineEdit()
        frm.addWidget(QLabel("Input Model / Path"), r, 0)
        frm.addWidget(self.input_path, r, 1)
        btn = QPushButton("Browse")
        btn.clicked.connect(self._browse_input)
        frm.addWidget(btn, r, 2)
        r += 1

        # LoRA base (hidden unless convert_lora_to_gguf.py)
        self._lora_lbl = QLabel("Base Model (LoRA)")
        self._lora_lbl.setStyleSheet("color: #f7768e;")
        self.base_model = QLineEdit()
        self._lora_btn = QPushButton("Browse")
        self._lora_btn.clicked.connect(self._browse_base)
        frm.addWidget(self._lora_lbl, r, 0)
        frm.addWidget(self.base_model, r, 1)
        frm.addWidget(self._lora_btn, r, 2)
        self._lora_row = r
        r += 1

        # outtype
        self.outtype = QComboBox()
        self.outtype.addItems(OUTTYPE_VALUES)
        frm.addWidget(QLabel("Output Type (--outtype)"), r, 0)
        frm.addWidget(self.outtype, r, 1)
        r += 1

        # HF flags panel (hidden unless convert_hf_to_gguf.py)
        self._hf_flags_box = card("HF Flags")
        hf_flags_l = QGridLayout(self._hf_flags_box)
        self.hf_bools: dict[str, QCheckBox] = {}
        for i, flag in enumerate(HF_BOOL_FLAGS):
            cb = QCheckBox(flag)
            self.hf_bools[flag] = cb
            hf_flags_l.addWidget(cb, i // 3, i % 3)
        frm.addWidget(self._hf_flags_box, r, 0, 1, 3)
        self._hf_flags_row = r
        r += 1

        # HF text options panel (hidden unless convert_hf_to_gguf.py)
        self._hf_text_box = card("HF Options")
        hf_text_l = QGridLayout(self._hf_text_box)
        hf_text_l.setColumnStretch(1, 1)
        self.hf_texts: dict[str, QLineEdit] = {}
        for ri, flag in enumerate(HF_TEXT_FLAGS):
            le = QLineEdit()
            self.hf_texts[flag] = le
            hf_text_l.addWidget(QLabel(flag), ri, 0)
            hf_text_l.addWidget(le, ri, 1)
        frm.addWidget(self._hf_text_box, r, 0, 1, 3)
        self._hf_text_row = r
        r += 1

        # output path
        self.output_path = QLineEdit()
        frm.addWidget(QLabel("Output File / Dir"), r, 0)
        frm.addWidget(self.output_path, r, 1)
        btn = QPushButton("Browse")
        btn.clicked.connect(self._browse_output)
        frm.addWidget(btn, r, 2)
        r += 1

        # extra args
        self.extra_args = QLineEdit()
        frm.addWidget(QLabel("Extra Arguments"), r, 0)
        frm.addWidget(self.extra_args, r, 1, 1, 2)
        r += 1

        # dry-run + run button
        self.dry_run = QCheckBox("Dry Run (show command only)")
        frm.addWidget(self.dry_run, r, 0, 1, 3)
        r += 1

        run_btn = QPushButton("Run Conversion 🚀")
        run_btn.setObjectName("PrimaryButton")
        run_btn.clicked.connect(self._run)
        frm.addWidget(run_btn, r, 0, 1, 3)
        r += 1

        outer.addWidget(make_scrollable(content), 1)

        # Output log
        self.logbox = LogConsole(height=324)
        outer.addWidget(self.logbox)

    # ── script change ────────────────────────────────────────────────────

    def _on_script_change(self, script: str):
        self.outtype.setCurrentText(DEFAULT_OUTTYPE.get(script, "f16"))

        is_lora = script == "convert_lora_to_gguf.py"
        self._lora_lbl.setVisible(is_lora)
        self.base_model.setVisible(is_lora)
        self._lora_btn.setVisible(is_lora)

        is_hf = script == "convert_hf_to_gguf.py"
        self._hf_flags_box.setVisible(is_hf)
        self._hf_text_box.setVisible(is_hf)
        if not is_hf:
            for v in self.hf_bools.values():
                v.setChecked(False)
            for v in self.hf_texts.values():
                v.clear()

    # ── browse helpers ───────────────────────────────────────────────────

    def _browse_llama(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select llama.cpp directory", self.llama_dir.text() or "/"
        )
        if d:
            self.llama_dir.setText(d)

    def _browse_input(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select input model/path", models_dir()
        )
        if d:
            self.input_path.setText(d)

    def _browse_output(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select output directory", models_dir()
        )
        if d:
            self.output_path.setText(d)

    def _browse_base(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "Select base model GGUF", models_dir(), "GGUF (*.gguf)"
        )
        if p:
            self.base_model.setText(p)

    # ── log ──────────────────────────────────────────────────────────────

    def _log(self, text: str):
        append_log(self.logbox, text)

    # ── run ──────────────────────────────────────────────────────────────

    def _run(self):
        try:
            cmd = build_convert_args(
                llama_dir=self.llama_dir.text(),
                script=self.script_cb.currentText(),
                input_path=self.input_path.text(),
                outtype=self.outtype.currentText(),
                output_path=self.output_path.text(),
                base_model=self.base_model.text(),
                hf_bools={f: v.isChecked() for f, v in self.hf_bools.items()},
                hf_texts={f: v.text() for f, v in self.hf_texts.items()},
                extra_args=self.extra_args.text(),
            )
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        display = shell_quote_list(cmd)
        self._log(f"\n▶ Command:\n{display}\n")

        if self.dry_run.isChecked():
            self._log("🛠 Dry Run — not executed")
            return

        if self._proc is not None and self._proc.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.warning(self, "Busy", "A conversion is already running.")
            return

        proc = QProcess(self)
        proc.setProgram(cmd[0])
        proc.setArguments(cmd[1:])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(self._on_ready_read)
        proc.finished.connect(self._on_finished)
        proc.errorOccurred.connect(self._on_error)

        self._proc = proc
        proc.start()

    def _on_ready_read(self):
        if self._proc is None:
            return
        data = self._proc.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            if line:
                self._log(line)

    def _on_finished(self, code: int, _status):
        if code == 0:
            self._log("\n✅ Done!")
        else:
            self._log(f"\n⚠ Exited with code {code}")
        self._proc = None

    def _on_error(self, error):
        self._log(f"\n❌ Process error: {error}")
        self._proc = None
