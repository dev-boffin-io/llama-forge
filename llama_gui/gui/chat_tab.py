"""
gui/chat_tab.py — Chat (SAFE) tab for llama-cli interactive mode (PyQt6).

Boolean flags panel  — checkboxes, unchecked = not passed
Value flags panel    — label + entry, empty = not passed

Updated for llama.cpp 2025:
  • New bool flags : --jinja, --no-warmup (already there), --thinking
  • New value flags: --ubatch-size, --cache-type-k, --cache-type-v,
                     --prio, --reasoning-budget, --samplers
  • Full built-in chat template list in --chat-template combobox
"""

from __future__ import annotations

import os
import shlex

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QFileDialog,
    QMessageBox, QSizePolicy,
)
from PyQt6.QtCore import Qt

from core.llama_detect import models_dir, supports_flag, exe_name, resolve_exe
from core.quant_logic import KV_CACHE_TYPES
from utils.terminal import TERMINAL, launch_in_terminal, shell_quote_list
from gui import make_scrollable, LogConsole, append_log, card

# All built-in chat templates supported by latest llama.cpp
_CHAT_TEMPLATES = [
    "chatml",           # safe default
    "llama3", "llama4",
    "llama2", "llama2-sys", "llama2-sys-bos", "llama2-sys-strip",
    "mistral-v1", "mistral-v3", "mistral-v3-tekken",
    "mistral-v7", "mistral-v7-tekken",
    "gemma",
    "phi3", "phi4",
    "command-r",
    "deepseek", "deepseek2", "deepseek3", "deepseek-ocr",
    "qwen2", "qwen3",
    "exaone3", "exaone4", "exaone-moe",
    "falcon3",
    "granite", "granite-4.0",
    "gpt-oss",
    "grok-2",
    "hunyuan-dense", "hunyuan-moe",
    "kimi-k2",
    "bailing", "bailing-think", "bailing2",
    "chatglm3", "chatglm4",
    "gigachat", "glmedge",
    "internlm2",
    "megrez",
    "minicpm",
    "monarch",
    "openchat",
    "orion",
    "pangu-embedded",
    "rwkv-world",
    "seed_oss",
    "smolvlm",
    "solar-open",
    "vicuna", "vicuna-orca",
    "yandex",
    "zephyr",
]


def _default_browse_dir(current: str) -> str:
    if current and os.path.exists(current):
        return os.path.dirname(current)
    return os.path.expanduser("~")


class ChatTab(QWidget):
    def __init__(self, app: QWidget):
        super().__init__()
        self.app = app
        self._bool_flags: dict[str, QCheckBox] = {}
        self._val_flags: dict[str, QLineEdit] = {}
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

        # ── File selectors ────────────────────────────────────────────
        btn_bin = QPushButton("📂  Select llama.cpp build/bin (Shared)")
        btn_bin.clicked.connect(self._pick_bin_dir)
        f.addWidget(btn_bin)

        btn_model = QPushButton("📦  Select GGUF model (for Chat)")
        btn_model.clicked.connect(self._pick_model)
        f.addWidget(btn_model)

        # ── Core args ─────────────────────────────────────────────────
        core = card("Core Arguments")
        core_l = QGridLayout(core)
        core_l.setColumnStretch(1, 1)
        core_l.setColumnStretch(3, 1)
        core_l.setColumnStretch(5, 1)

        self.ctx       = QLineEdit("2048")
        self.threads   = QLineEdit("2")
        self.n_predict = QLineEdit("-1")
        self.batch     = QLineEdit("512")
        self.ubatch    = QLineEdit("512")
        self.n_gpu     = QLineEdit("0")

        rows = [
            [("--ctx-size",     self.ctx),
             ("--threads",      self.threads),
             ("--n-predict",    self.n_predict)],
            [("--batch-size",   self.batch),
             ("--ubatch-size",  self.ubatch),
             ("--n-gpu-layers", self.n_gpu)],
        ]
        for r, items in enumerate(rows):
            for c, (lbl, widget) in enumerate(items):
                core_l.addWidget(QLabel(lbl), r, c * 2, Qt.AlignmentFlag.AlignRight)
                core_l.addWidget(widget, r, c * 2 + 1)
        f.addWidget(core)

        # ── Chat template ────────────────────────────────────────────
        ct_row = QHBoxLayout()
        ct_row.addWidget(QLabel("--chat-template:"))
        self.template = QComboBox()
        self.template.setEditable(True)
        self.template.addItems(_CHAT_TEMPLATES)
        self.template.setCurrentText("chatml")
        self.template.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ct_row.addWidget(self.template)
        f.addLayout(ct_row)

        # ── KV cache ─────────────────────────────────────────────────
        kv = card("KV Cache  (2025)")
        kv_l = QHBoxLayout(kv)
        self.cache_type_k = QComboBox()
        self.cache_type_k.addItems(KV_CACHE_TYPES)
        self.cache_type_v = QComboBox()
        self.cache_type_v.addItems(KV_CACHE_TYPES)
        kv_l.addWidget(QLabel("--cache-type-k"))
        kv_l.addWidget(self.cache_type_k)
        kv_l.addWidget(QLabel("--cache-type-v"))
        kv_l.addWidget(self.cache_type_v)
        kv_l.addStretch(1)
        f.addWidget(kv)

        # ── Boolean flags ─────────────────────────────────────────────
        bf = card("Flags (checked = enabled)")
        bf_l = QGridLayout(bf)
        bool_flag_names = [
            "--interactive-first",
            "--conversation",
            "--jinja",
            "--no-warmup",
            "--flash-attn",
            "--mlock",
            "--no-mmap",
            "--verbose",
            "--log-disable",
            "--special",
            "--thinking",
        ]
        cols = 3
        for i, flag in enumerate(bool_flag_names):
            cb = QCheckBox(flag)
            if flag == "--interactive-first":
                cb.setChecked(True)
            self._bool_flags[flag] = cb
            bf_l.addWidget(cb, i // cols, i % cols)
        f.addWidget(bf)

        # ── Value flags (optional) ──────────────────────────────────────
        vf = card("Optional Arguments (empty = skip)")
        vf_l = QGridLayout(vf)
        vf_l.setColumnStretch(1, 1)
        val_flag_names = [
            "--reasoning-budget",
            "--prio",
            "--rope-freq-base",
            "--rope-freq-scale",
            "--repeat-penalty",
            "--temp",
            "--top-k",
            "--top-p",
            "--min-p",
            "--seed",
            "--system-prompt",
            "--grammar-file",
            "--lora",
            "--override-kv",
        ]
        for r, flag in enumerate(val_flag_names):
            le = QLineEdit()
            self._val_flags[flag] = le
            vf_l.addWidget(QLabel(flag), r, 0, Qt.AlignmentFlag.AlignRight)
            vf_l.addWidget(le, r, 1)
        f.addWidget(vf)

        # ── Extra free-text ───────────────────────────────────────────
        ef = QHBoxLayout()
        ef.addWidget(QLabel("Extra args:"))
        self.extra_args = QLineEdit()
        ef.addWidget(self.extra_args)
        f.addLayout(ef)

        # ── Run button ────────────────────────────────────────────────
        run_btn = QPushButton("▶  Interactive Chat")
        run_btn.setObjectName("PrimaryButton")
        run_btn.clicked.connect(self._run_chat)
        f.addWidget(run_btn)

        f.addStretch(1)

        outer.addWidget(make_scrollable(content), 1)

        # ── Log ───────────────────────────────────────────────────────
        self.logbox = LogConsole(height=216)
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

    def _pick_model(self):
        initial = _default_browse_dir(getattr(self.app, "chat_model", "")) or models_dir()
        p, _ = QFileDialog.getOpenFileName(
            self, "Select GGUF model", initial, "GGUF (*.gguf)"
        )
        if p:
            self.app.chat_model = p
            self.app.save()
            self._log(f"✔ Model: {p}")

    def _run_chat(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        if not getattr(self.app, "chat_model", ""):
            QMessageBox.critical(self, "Error", "Select a GGUF model first!")
            return

        cli = resolve_exe("llama-cli", self.app.bin_dir)
        cmd_list = [cli, "-m", self.app.chat_model]

        for flag, widget in [
            ("--ctx-size",     self.ctx),
            ("--threads",      self.threads),
            ("--n-predict",    self.n_predict),
            ("--batch-size",   self.batch),
            ("--ubatch-size",  self.ubatch),
            ("--n-gpu-layers", self.n_gpu),
        ]:
            val = widget.text().strip()
            if val:
                if flag == "--n-predict" and val == "-1":
                    continue
                if flag == "--n-gpu-layers" and val == "0":
                    continue
                if flag == "--ubatch-size" and val == "512":
                    continue
                cmd_list += [flag, val]

        # Chat template
        tmpl = self.template.currentText().strip()
        if tmpl:
            cmd_list += ["--chat-template", tmpl]

        # KV cache types (only if non-default)
        k_type = self.cache_type_k.currentText()
        v_type = self.cache_type_v.currentText()
        if k_type and k_type != "f16":
            cmd_list += ["--cache-type-k", k_type]
        if v_type and v_type != "f16":
            cmd_list += ["--cache-type-v", v_type]

        # Boolean flags — only if checked AND supported
        for flag, cb in self._bool_flags.items():
            if cb.isChecked():
                if supports_flag(flag, cli):
                    cmd_list.append(flag)
                else:
                    self._log(f"⚠ {flag} not supported by this build, skipping")

        # Value flags — only if non-empty
        for flag, le in self._val_flags.items():
            val = le.text().strip()
            if val:
                cmd_list += [flag, val]

        # Extra free-text args
        extra = self.extra_args.text().strip()
        if extra:
            cmd_list += shlex.split(extra)

        shell_cmd = shell_quote_list(cmd_list)
        self._log(f"▶ {shell_cmd}")

        if not launch_in_terminal(shell_cmd, title="llama-cli chat"):
            QMessageBox.critical(self, "Error", "No terminal found!")

    # ── public ───────────────────────────────────────────────────────────

    def startup_log(self, msg: str):
        self._log(msg)
