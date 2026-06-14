"""
gui/quant_tab.py — Quantize tab (PyQt6).

Features:
  • Full quant type list
  • Output/token-embedding tensor type dropdowns
  • All llama-quantize flags
  • GGUF info viewer on model select
  • RAM-based quant recommendation

Cross-platform: Linux · macOS · Windows · Android/Termux
"""

from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from core.llama_detect import models_dir, exe_name, resolve_exe
from core.quant_logic import (
    QUANT_TYPES, TENSOR_TYPES, build_quantize_args,
)
from utils.terminal import TERMINAL, launch_in_terminal, shell_quote_list
from utils.gguf_info import read_gguf_info
from utils.ram_detect import get_total_ram_gb, recommend_quant
from gui import make_scrollable, LogConsole, append_log, card


def _default_browse_dir(current: str) -> str:
    if current and os.path.exists(current):
        return os.path.dirname(current)
    return os.path.expanduser("~")


class QuantTab(QWidget):
    def __init__(self, app: QWidget):
        super().__init__()
        self.app = app
        self._build()

    # ── build ────────────────────────────────────────────────────────────

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        content = QWidget()
        f = QVBoxLayout(content)
        f.setContentsMargins(14, 14, 14, 14)
        f.setSpacing(10)

        # Buttons
        btn_bin = QPushButton("📂  Select llama.cpp build/bin (Shared)")
        btn_bin.clicked.connect(self._pick_bin_dir)
        f.addWidget(btn_bin)

        btn_gguf = QPushButton("📦  Select GGUF file (for Quantize)")
        btn_gguf.clicked.connect(self._pick_gguf)
        f.addWidget(btn_gguf)

        # RAM recommendation banner
        ram_gb = get_total_ram_gb()
        rec_type, rec_desc = recommend_quant(ram_gb)
        self._rec_type = rec_type
        ram_label = QLabel(f"💾  RAM: {ram_gb} GB   →   Recommended: {rec_type}")
        ram_label.setObjectName("Banner")
        f.addWidget(ram_label)

        # Quant type
        qrow = QHBoxLayout()
        qrow.addWidget(QLabel("Quant type:"))
        self.qtype_cb = QComboBox()
        self.qtype_cb.addItems(QUANT_TYPES)
        if rec_type in QUANT_TYPES:
            self.qtype_cb.setCurrentText(rec_type)
        qrow.addWidget(self.qtype_cb)
        qrow.addStretch(1)
        f.addLayout(qrow)

        # Tensor types
        trow = QHBoxLayout()
        self.out_tensor = QComboBox()
        self.out_tensor.addItems(TENSOR_TYPES)
        self.tok_emb = QComboBox()
        self.tok_emb.addItems(TENSOR_TYPES)
        trow.addWidget(QLabel("Output tensor type:"))
        trow.addWidget(self.out_tensor)
        trow.addWidget(QLabel("Token-emb type:"))
        trow.addWidget(self.tok_emb)
        trow.addStretch(1)
        f.addLayout(trow)

        # Numeric / path options
        nf = card("Options")
        nf_l = QGridLayout(nf)
        nf_l.setColumnStretch(1, 1)

        self.q_nthread = QLineEdit()
        self.q_imatrix = QLineEdit()
        self.q_inc_w   = QLineEdit()
        self.q_exc_w   = QLineEdit()
        self.q_ovr_kv  = QLineEdit()

        nf_l.addWidget(QLabel("--nthread"), 0, 0, Qt.AlignmentFlag.AlignRight)
        nf_l.addWidget(self.q_nthread, 0, 1)

        nf_l.addWidget(QLabel("--imatrix file"), 1, 0, Qt.AlignmentFlag.AlignRight)
        nf_l.addWidget(self.q_imatrix, 1, 1)
        imatrix_btn = QPushButton("…")
        imatrix_btn.setFixedWidth(64)
        imatrix_btn.clicked.connect(self._browse_imatrix)
        nf_l.addWidget(imatrix_btn, 1, 2)

        nf_l.addWidget(QLabel("--include-weights"), 2, 0, Qt.AlignmentFlag.AlignRight)
        nf_l.addWidget(self.q_inc_w, 2, 1)

        nf_l.addWidget(QLabel("--exclude-weights"), 3, 0, Qt.AlignmentFlag.AlignRight)
        nf_l.addWidget(self.q_exc_w, 3, 1)

        nf_l.addWidget(QLabel("--override-kv"), 4, 0, Qt.AlignmentFlag.AlignRight)
        nf_l.addWidget(self.q_ovr_kv, 4, 1)

        f.addWidget(nf)

        # Bool flags
        bf = card("Flags")
        bf_l = QGridLayout(bf)
        self.q_allow_req  = QCheckBox("--allow-requantize")
        self.q_leave_out  = QCheckBox("--leave-output-tensor")
        self.q_pure       = QCheckBox("--pure")
        self.q_keep_split = QCheckBox("--keep-split")
        bf_l.addWidget(self.q_allow_req,  0, 0)
        bf_l.addWidget(self.q_leave_out,  0, 1)
        bf_l.addWidget(self.q_pure,       1, 0)
        bf_l.addWidget(self.q_keep_split, 1, 1)
        f.addWidget(bf)

        run_btn = QPushButton("▶  Quantize")
        run_btn.setObjectName("PrimaryButton")
        run_btn.clicked.connect(self._run_quantize)
        f.addWidget(run_btn)

        f.addStretch(1)

        outer.addWidget(make_scrollable(content), 1)

        # Log
        self.logbox = LogConsole(height=252)
        outer.addWidget(self.logbox)

        if TERMINAL:
            self._log(f"✔ Terminal: {TERMINAL}")
        else:
            self._log("❌ No supported terminal detected")

    # ── actions ──────────────────────────────────────────────────────────

    def _log(self, msg: str):
        append_log(self.logbox, msg)

    def _pick_bin_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select llama.cpp build/bin",
            self.app.bin_dir or os.path.expanduser("~"),
        )
        if not d:
            return
        cli_path = os.path.join(d, exe_name("llama-cli"))
        if os.path.isfile(cli_path):
            self.app.bin_dir = d
            self.app.save()
            self._log(f"✔ bin dir: {d}")
        else:
            QMessageBox.critical(
                self, "Error",
                f"{exe_name('llama-cli')} not found in selected directory!"
            )

    def _pick_gguf(self):
        initial = _default_browse_dir(getattr(self.app, "quant_gguf", "")) or models_dir()
        p, _ = QFileDialog.getOpenFileName(
            self, "Select GGUF file", initial, "GGUF (*.gguf)"
        )
        if not p:
            return
        self.app.quant_gguf = p
        self.app.save()
        self._log(f"✔ GGUF: {p}")
        self._show_gguf_info(p)

    def _show_gguf_info(self, path: str):
        from core.llama_detect import LLAMA_ROOT
        info = read_gguf_info(path, LLAMA_ROOT)
        if info.error:
            self._log(f"⚠ GGUF info error: {info.error}")
            return
        lines = [
            "── GGUF Info ──────────────────",
            f"  Name        : {info.model_name}",
            f"  Architecture: {info.architecture}",
            f"  Quant type  : {info.quant_type}",
            f"  Context     : {info.context_length}",
            f"  Layers      : {info.n_layers}",
            f"  Embed dim   : {info.embedding_length}",
            f"  File size   : {info.file_size_mb:.1f} MB",
            "────────────────────────────────",
        ]
        for ln in lines:
            self._log(ln)

    def _browse_imatrix(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "Select imatrix file", models_dir(),
            "imatrix (*.dat *.imatrix);;All Files (*)"
        )
        if p:
            self.q_imatrix.setText(p)

    def _run_quantize(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        if not getattr(self.app, "quant_gguf", ""):
            QMessageBox.critical(self, "Error", "Select a source GGUF file first!")
            return

        exe = resolve_exe("llama-quantize", self.app.bin_dir)
        if not os.path.isfile(exe):
            QMessageBox.critical(
                self, "Error",
                f"{exe_name('llama-quantize')} not found in bin dir!\n{exe}"
            )
            return

        args = build_quantize_args(
            exe=exe,
            src_gguf=self.app.quant_gguf,
            qtype=self.qtype_cb.currentText(),
            out_tensor_type=self.out_tensor.currentText(),
            tok_emb_type=self.tok_emb.currentText(),
            nthread=self.q_nthread.text(),
            imatrix=self.q_imatrix.text(),
            include_weights=self.q_inc_w.text(),
            exclude_weights=self.q_exc_w.text(),
            override_kv=self.q_ovr_kv.text(),
            allow_requantize=self.q_allow_req.isChecked(),
            leave_output=self.q_leave_out.isChecked(),
            pure=self.q_pure.isChecked(),
            keep_split=self.q_keep_split.isChecked(),
        )

        shell_cmd = shell_quote_list(args)
        self._log(f"▶ {shell_cmd}")

        if not launch_in_terminal(shell_cmd, title="llama-quantize"):
            QMessageBox.critical(self, "Error", "No terminal found!")

    # ── public ───────────────────────────────────────────────────────────

    def startup_log(self, msg: str):
        self._log(msg)
