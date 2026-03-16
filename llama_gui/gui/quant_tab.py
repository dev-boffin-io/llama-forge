"""
quant_tab.py — Quantize tab.

Features:
  • Full quant type list
  • Output/token-embedding tensor type dropdowns
  • All llama-quantize flags
  • GGUF info viewer on model select
  • RAM-based quant recommendation
"""

from __future__ import annotations
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.llama_detect import models_dir
from core.quant_logic import (
    QUANT_TYPES, TENSOR_TYPES, DEFAULT_QUANT, build_quantize_args
)
from utils.terminal import TERMINAL, launch_in_terminal, shell_quote_list
from utils.gguf_info import read_gguf_info
from utils.ram_detect import get_total_ram_gb, recommend_quant
from gui import make_scrollable, log_widget, append_log


class QuantTab:
    def __init__(self, notebook: ttk.Notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Quantize")
        self._build()

    # ── build ────────────────────────────────────────────────────────────

    def _build(self):
        ctrl_host = ttk.Frame(self.frame)
        ctrl_host.pack(fill="both", expand=True)
        log_host = ttk.Frame(self.frame, padding=(8, 0, 8, 8))
        log_host.pack(fill="x", expand=False)

        _canvas, f = make_scrollable(ctrl_host)
        f.configure(padding=12)

        # Buttons
        ttk.Button(f, text="Select llama.cpp build/bin (Shared)",
                   command=self._pick_bin_dir).pack(fill=tk.X, pady=6)
        ttk.Button(f, text="Select GGUF file (for Quantize)",
                   command=self._pick_gguf).pack(fill=tk.X, pady=6)

        # RAM recommendation banner
        ram_gb = get_total_ram_gb()
        rec_type, rec_desc = recommend_quant(ram_gb)
        ram_label = f"💾 RAM: {ram_gb} GB  →  Recommended: {rec_type}"
        ttk.Label(f, text=ram_label, foreground="#2255aa").pack(anchor="w", padx=4, pady=4)

        # Quant type
        qrow = ttk.Frame(f)
        qrow.pack(fill=tk.X, pady=6)
        ttk.Label(qrow, text="Quant type:").pack(side=tk.LEFT, padx=8)
        self.qtype_var = tk.StringVar(value=rec_type)
        self.qtype_cb = ttk.Combobox(
            qrow, values=QUANT_TYPES, textvariable=self.qtype_var,
            width=14, state="readonly"
        )
        self.qtype_cb.pack(side=tk.LEFT, padx=6)

        # Tensor types
        trow = ttk.Frame(f)
        trow.pack(fill=tk.X, pady=4)
        self.out_tensor = tk.StringVar(value="default")
        self.tok_emb    = tk.StringVar(value="default")
        for lbl, var in [("Output tensor type:", self.out_tensor),
                         ("Token-emb type:",     self.tok_emb)]:
            ttk.Label(trow, text=lbl).pack(side=tk.LEFT, padx=8)
            ttk.Combobox(trow, values=TENSOR_TYPES, textvariable=var,
                         width=10, state="readonly").pack(side=tk.LEFT, padx=4)

        # Numeric options
        nf = ttk.LabelFrame(f, text="Options", padding=8)
        nf.pack(fill=tk.X, pady=6)
        nf.columnconfigure(1, weight=1)

        self.q_nthread  = tk.StringVar()
        self.q_imatrix  = tk.StringVar()
        self.q_inc_w    = tk.StringVar()
        self.q_exc_w    = tk.StringVar()
        self.q_ovr_kv   = tk.StringVar()

        ttk.Label(nf, text="--nthread").grid(row=0, column=0, sticky="e", padx=6, pady=3)
        ttk.Entry(nf, textvariable=self.q_nthread, width=8).grid(row=0, column=1, sticky="w", padx=4)

        ttk.Label(nf, text="--imatrix file").grid(row=1, column=0, sticky="e", padx=6, pady=3)
        ttk.Entry(nf, textvariable=self.q_imatrix).grid(row=1, column=1, sticky="ew", padx=4)
        ttk.Button(nf, text="…", width=3,
                   command=self._browse_imatrix).grid(row=1, column=2, padx=4)

        ttk.Label(nf, text="--include-weights").grid(row=2, column=0, sticky="e", padx=6, pady=3)
        ttk.Entry(nf, textvariable=self.q_inc_w).grid(row=2, column=1, sticky="ew", padx=4)

        ttk.Label(nf, text="--exclude-weights").grid(row=3, column=0, sticky="e", padx=6, pady=3)
        ttk.Entry(nf, textvariable=self.q_exc_w).grid(row=3, column=1, sticky="ew", padx=4)

        ttk.Label(nf, text="--override-kv").grid(row=4, column=0, sticky="e", padx=6, pady=3)
        ttk.Entry(nf, textvariable=self.q_ovr_kv).grid(row=4, column=1, sticky="ew", padx=4)

        # Bool flags
        bf = ttk.LabelFrame(f, text="Flags", padding=8)
        bf.pack(fill=tk.X, pady=6)
        self.q_allow_req  = tk.BooleanVar()
        self.q_leave_out  = tk.BooleanVar()
        self.q_pure       = tk.BooleanVar()
        self.q_keep_split = tk.BooleanVar()
        for i, (lbl, var) in enumerate([
            ("--allow-requantize",    self.q_allow_req),
            ("--leave-output-tensor", self.q_leave_out),
            ("--pure",                self.q_pure),
            ("--keep-split",          self.q_keep_split),
        ]):
            ttk.Checkbutton(bf, text=lbl, variable=var).grid(
                row=i//2, column=i%2, padx=16, pady=3, sticky="w"
            )

        ttk.Button(f, text="▶ Quantize", command=self._run_quantize).pack(
            fill=tk.X, pady=12
        )

        # Log
        self.logbox = log_widget(log_host, self.app.log_font)
        self.logbox.configure(height=6)
        self.logbox.pack(fill="x", expand=False)

        if TERMINAL:
            self._log(f"✔ Terminal: {TERMINAL}")

    # ── actions ──────────────────────────────────────────────────────────

    def _log(self, msg: str):
        append_log(self.logbox, msg + "\n")

    def _pick_bin_dir(self):
        d = filedialog.askdirectory(title="Select llama.cpp build/bin",
                                    initialdir=self.app.bin_dir or "/")
        if not d:
            return
        if os.path.isfile(os.path.join(d, "llama-cli")):
            self.app.bin_dir = d
            self.app.save()
            self._log(f"✔ bin dir: {d}")
        else:
            messagebox.showerror("Error", "llama-cli not found!")

    def _pick_gguf(self):
        from core.llama_detect import LLAMA_ROOT
        initial = (
            os.path.dirname(self.app.quant_gguf)
            if getattr(self.app, "quant_gguf", "") and
               os.path.exists(self.app.quant_gguf)
            else models_dir()
        )
        p = filedialog.askopenfilename(
            title="Select GGUF file",
            initialdir=initial,
            filetypes=[("GGUF", "*.gguf")],
        )
        if not p:
            return
        self.app.quant_gguf = p
        self.app.save()
        self._log(f"✔ GGUF: {p}")

        # Show GGUF info + set recommended quant
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
        for l in lines:
            self._log(l)

    def _browse_imatrix(self):
        p = filedialog.askopenfilename(
            title="Select imatrix file",
            initialdir=models_dir(),
            filetypes=[("imatrix", "*.dat *.imatrix"), ("All", "*")],
        )
        if p:
            self.q_imatrix.set(p)

    def _run_quantize(self):
        if not self.app.bin_dir:
            messagebox.showerror("Error", "Select llama.cpp build/bin first!")
            return
        if not getattr(self.app, "quant_gguf", ""):
            messagebox.showerror("Error", "Select a source GGUF file first!")
            return

        exe = os.path.join(self.app.bin_dir, "llama-quantize")
        if not os.path.isfile(exe):
            messagebox.showerror("Error", "llama-quantize not found in bin dir!")
            return

        args = build_quantize_args(
            exe=exe,
            src_gguf=self.app.quant_gguf,
            qtype=self.qtype_var.get(),
            out_tensor_type=self.out_tensor.get(),
            tok_emb_type=self.tok_emb.get(),
            nthread=self.q_nthread.get(),
            imatrix=self.q_imatrix.get(),
            include_weights=self.q_inc_w.get(),
            exclude_weights=self.q_exc_w.get(),
            override_kv=self.q_ovr_kv.get(),
            allow_requantize=self.q_allow_req.get(),
            leave_output=self.q_leave_out.get(),
            pure=self.q_pure.get(),
            keep_split=self.q_keep_split.get(),
        )

        shell_cmd = shell_quote_list(args)
        self._log(f"▶ {shell_cmd}")

        if not launch_in_terminal(shell_cmd, title="llama-quantize"):
            messagebox.showerror("Error", "No terminal found!")

    # ── public ───────────────────────────────────────────────────────────

    def startup_log(self, msg: str):
        self._log(msg)
