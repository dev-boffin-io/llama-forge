"""
chat_tab.py — Chat (SAFE) tab for llama-cli interactive mode.

Boolean flags panel  — checkboxes, unchecked = not passed
Value flags panel    — label + entry, empty = not passed
"""

from __future__ import annotations
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.llama_detect import models_dir, supports_flag
from utils.terminal import TERMINAL, _REAL_TERM, launch_in_terminal, shell_quote_list
from gui import make_scrollable, log_widget, append_log


class ChatTab:
    def __init__(self, notebook: ttk.Notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Chat (SAFE)")
        self._build()

    # ── build ────────────────────────────────────────────────────────────

    def _build(self):
        ctrl_host = ttk.Frame(self.frame)
        ctrl_host.pack(fill="both", expand=True)
        log_host = ttk.Frame(self.frame, padding=(8, 0, 8, 8))
        log_host.pack(fill="x", expand=False)

        _canvas, f = make_scrollable(ctrl_host)
        f.configure(padding=12)

        # ── File selectors ────────────────────────────────────────────
        ttk.Button(f, text="Select llama.cpp build/bin (Shared)",
                   command=self._pick_bin_dir).pack(fill=tk.X, pady=6)
        ttk.Button(f, text="Select GGUF model (for Chat)",
                   command=self._pick_model).pack(fill=tk.X, pady=6)

        # ── Core args (always sent) ───────────────────────────────────
        core = ttk.LabelFrame(f, text="Core Arguments", padding=8)
        core.pack(fill=tk.X, pady=6)
        core.columnconfigure(1, weight=1)
        core.columnconfigure(3, weight=1)
        core.columnconfigure(5, weight=1)

        self.ctx     = tk.StringVar(value="2048")
        self.threads = tk.StringVar(value="2")
        self.template = tk.StringVar(value="chatml")
        self.n_predict = tk.StringVar(value="-1")
        self.batch    = tk.StringVar(value="512")
        self.n_gpu    = tk.StringVar(value="0")

        for r, items in enumerate([
            [("--ctx-size",      self.ctx,      8),
             ("--threads",       self.threads,  6),
             ("--chat-template", self.template, 10)],
            [("--n-predict",     self.n_predict, 6),
             ("--batch-size",    self.batch,     6),
             ("--n-gpu-layers",  self.n_gpu,     6)],
        ]):
            for c, (lbl, var, w) in enumerate(items):
                ttk.Label(core, text=lbl).grid(row=r, column=c*2,   padx=8, pady=4, sticky="e")
                ttk.Entry(core, textvariable=var, width=w).grid(row=r, column=c*2+1, padx=6, pady=4, sticky="ew")

        # ── Boolean flags ─────────────────────────────────────────────
        bf = ttk.LabelFrame(f, text="Flags (checked = enabled)", padding=8)
        bf.pack(fill=tk.X, pady=6)

        self._bool_flags: dict[str, tk.BooleanVar] = {
            "--interactive-first":  tk.BooleanVar(value=True),
            "--conversation":       tk.BooleanVar(value=False),
            "--no-warmup":          tk.BooleanVar(value=False),
            "--flash-attn":         tk.BooleanVar(value=False),
            "--mlock":              tk.BooleanVar(value=False),
            "--no-mmap":            tk.BooleanVar(value=False),
            "--verbose":            tk.BooleanVar(value=False),
            "--log-disable":        tk.BooleanVar(value=False),
            "--special":            tk.BooleanVar(value=False),
        }
        items = list(self._bool_flags.items())
        cols = 3
        for i, (flag, var) in enumerate(items):
            ttk.Checkbutton(bf, text=flag, variable=var).grid(
                row=i // cols, column=i % cols, padx=14, pady=3, sticky="w"
            )

        # ── Value flags (optional) ────────────────────────────────────
        vf = ttk.LabelFrame(f, text="Optional Arguments (empty = skip)", padding=8)
        vf.pack(fill=tk.X, pady=6)
        vf.columnconfigure(1, weight=1)

        self._val_flags: dict[str, tk.StringVar] = {
            "--rope-freq-base":    tk.StringVar(),
            "--rope-freq-scale":   tk.StringVar(),
            "--repeat-penalty":    tk.StringVar(),
            "--temp":              tk.StringVar(),
            "--top-k":             tk.StringVar(),
            "--top-p":             tk.StringVar(),
            "--min-p":             tk.StringVar(),
            "--seed":              tk.StringVar(),
            "--system-prompt":     tk.StringVar(),
            "--grammar-file":      tk.StringVar(),
            "--lora":              tk.StringVar(),
            "--override-kv":       tk.StringVar(),
        }
        for r, (flag, var) in enumerate(self._val_flags.items()):
            ttk.Label(vf, text=flag).grid(row=r, column=0, padx=8, pady=3, sticky="e")
            ttk.Entry(vf, textvariable=var).grid(row=r, column=1, padx=6, pady=3, sticky="ew")

        # ── Extra free-text ───────────────────────────────────────────
        ef = ttk.Frame(f)
        ef.pack(fill=tk.X, pady=6)
        ttk.Label(ef, text="Extra args:").pack(side=tk.LEFT, padx=8)
        self.extra_args = tk.StringVar()
        ttk.Entry(ef, textvariable=self.extra_args).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        # ── Run button ────────────────────────────────────────────────
        ttk.Button(f, text="▶ Interactive Chat",
                   command=self._run_chat).pack(fill=tk.X, pady=14)

        # ── Log ───────────────────────────────────────────────────────
        self.logbox = log_widget(log_host, self.app.log_font)
        self.logbox.configure(height=6)
        self.logbox.pack(fill="x", expand=False)

        if TERMINAL:
            real_name = _REAL_TERM or TERMINAL
            self._log(f"✔ Terminal: {TERMINAL}" +
                      (f" → {real_name}" if real_name != TERMINAL else ""))
        else:
            self._log("❌ No supported terminal detected")

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
            messagebox.showerror("Error", "llama-cli not found in selected directory!")

    def _pick_model(self):
        initial = (
            os.path.dirname(self.app.chat_model)
            if getattr(self.app, "chat_model", "") and
               os.path.exists(self.app.chat_model)
            else models_dir()
        )
        p = filedialog.askopenfilename(
            title="Select GGUF model",
            initialdir=initial,
            filetypes=[("GGUF", "*.gguf")],
        )
        if p:
            self.app.chat_model = p
            self.app.save()
            self._log(f"✔ Model: {p}")

    def _run_chat(self):
        if not self.app.bin_dir:
            messagebox.showerror("Error", "Select llama.cpp build/bin first!")
            return
        if not getattr(self.app, "chat_model", ""):
            messagebox.showerror("Error", "Select a GGUF model first!")
            return

        cli = os.path.join(self.app.bin_dir, "llama-cli")

        # Core args (always included if non-empty)
        cmd_list = [cli, "-m", self.app.chat_model]

        for flag, var in [
            ("--ctx-size",      self.ctx),
            ("--threads",       self.threads),
            ("--chat-template", self.template),
            ("--n-predict",     self.n_predict),
            ("--batch-size",    self.batch),
            ("--n-gpu-layers",  self.n_gpu),
        ]:
            val = var.get().strip()
            if val:
                # skip defaults that add no value
                if flag == "--n-predict" and val == "-1":
                    continue
                if flag == "--n-gpu-layers" and val == "0":
                    continue
                cmd_list += [flag, val]

        # Boolean flags — only if checked AND supported
        for flag, var in self._bool_flags.items():
            if var.get():
                if supports_flag(flag, cli):
                    cmd_list.append(flag)
                else:
                    self._log(f"⚠ {flag} not supported by this build, skipping")

        # Value flags — only if non-empty
        for flag, var in self._val_flags.items():
            val = var.get().strip()
            if val:
                cmd_list += [flag, val]

        # Extra free-text args
        if self.extra_args.get().strip():
            import shlex
            cmd_list += shlex.split(self.extra_args.get().strip())

        shell_cmd = shell_quote_list(cmd_list)
        self._log(f"▶ {shell_cmd}")

        if not launch_in_terminal(shell_cmd, title="llama-cli chat"):
            messagebox.showerror("Error", "No terminal found!")

    # ── public ───────────────────────────────────────────────────────────

    def startup_log(self, msg: str):
        self._log(msg)
