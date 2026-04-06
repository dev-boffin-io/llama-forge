"""
server_tab.py — llama-server tab for llama-forge GUI.

Starts llama-server in a terminal window with configurable arguments.
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


class ServerTab:
    def __init__(self, notebook: ttk.Notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Server")
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
        ttk.Button(f, text="Select GGUF model (for Server)",
                   command=self._pick_model).pack(fill=tk.X, pady=6)

        # ── Core args ─────────────────────────────────────────────────
        core = ttk.LabelFrame(f, text="Core Arguments", padding=8)
        core.pack(fill=tk.X, pady=6)
        core.columnconfigure(1, weight=1)
        core.columnconfigure(3, weight=1)
        core.columnconfigure(5, weight=1)

        self.host      = tk.StringVar(value="127.0.0.1")
        self.port      = tk.StringVar(value="8080")
        self.ctx       = tk.StringVar(value="2048")
        self.threads   = tk.StringVar(value="2")
        self.n_gpu     = tk.StringVar(value="0")
        self.batch     = tk.StringVar(value="512")
        self.parallel  = tk.StringVar(value="1")
        self.n_predict = tk.StringVar(value="-1")

        for r, items in enumerate([
            [("--host",        self.host,      16),
             ("--port",        self.port,       8),
             ("--ctx-size",    self.ctx,        8)],
            [("--threads",     self.threads,    6),
             ("--n-gpu-layers",self.n_gpu,      6),
             ("--batch-size",  self.batch,      8)],
            [("--parallel",    self.parallel,   6),
             ("--n-predict",   self.n_predict,  8)],
        ]):
            for c, (lbl, var, w) in enumerate(items):
                ttk.Label(core, text=lbl).grid(row=r, column=c*2,   padx=8, pady=4, sticky="e")
                ttk.Entry(core, textvariable=var, width=w).grid(row=r, column=c*2+1, padx=6, pady=4, sticky="ew")

        # ── Boolean flags ─────────────────────────────────────────────
        bf = ttk.LabelFrame(f, text="Flags (checked = enabled)", padding=8)
        bf.pack(fill=tk.X, pady=6)

        self._bool_flags: dict[str, tk.BooleanVar] = {
            "--flash-attn":          tk.BooleanVar(value=False),
            "--mlock":               tk.BooleanVar(value=False),
            "--no-mmap":             tk.BooleanVar(value=False),
            "--no-warmup":           tk.BooleanVar(value=False),
            "--embedding":           tk.BooleanVar(value=False),
            "--reranking":           tk.BooleanVar(value=False),
            "--log-disable":         tk.BooleanVar(value=False),
            "--verbose":             tk.BooleanVar(value=False),
            "--slots-endpoint-disable": tk.BooleanVar(value=False),
            "--metrics":             tk.BooleanVar(value=False),
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
            "--api-key":            tk.StringVar(),
            "--chat-template":      tk.StringVar(),
            "--system-prompt":      tk.StringVar(),
            "--rope-freq-base":     tk.StringVar(),
            "--rope-freq-scale":    tk.StringVar(),
            "--override-kv":        tk.StringVar(),
            "--lora":               tk.StringVar(),
            "--path":               tk.StringVar(),
            "--ssl-key-file":       tk.StringVar(),
            "--ssl-cert-file":      tk.StringVar(),
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

        # ── Buttons ───────────────────────────────────────────────────
        btn_row = ttk.Frame(f)
        btn_row.pack(fill=tk.X, pady=14)
        ttk.Button(btn_row, text="▶ Start Server",
                   command=self._run_server).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(btn_row, text="🌐 Open Web UI",
                   command=self._open_webui).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

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
        if os.path.isfile(os.path.join(d, "llama-server")):
            self.app.bin_dir = d
            self.app.save()
            self._log(f"✔ bin dir: {d}")
        else:
            messagebox.showerror("Error", "llama-server not found in selected directory!")

    def _pick_model(self):
        initial = (
            os.path.dirname(self.app.server_model)
            if getattr(self.app, "server_model", "") and
               os.path.exists(self.app.server_model)
            else models_dir()
        )
        p = filedialog.askopenfilename(
            title="Select GGUF model",
            initialdir=initial,
            filetypes=[("GGUF", "*.gguf")],
        )
        if p:
            self.app.server_model = p
            self.app.save()
            self._log(f"✔ Model: {p}")

    def _run_server(self):
        if not self.app.bin_dir:
            messagebox.showerror("Error", "Select llama.cpp build/bin first!")
            return
        if not getattr(self.app, "server_model", ""):
            messagebox.showerror("Error", "Select a GGUF model first!")
            return

        srv = os.path.join(self.app.bin_dir, "llama-server")

        cmd_list = [srv, "-m", self.app.server_model]

        # Core args
        for flag, var in [
            ("--host",         self.host),
            ("--port",         self.port),
            ("--ctx-size",     self.ctx),
            ("--threads",      self.threads),
            ("--n-gpu-layers", self.n_gpu),
            ("--batch-size",   self.batch),
            ("--parallel",     self.parallel),
            ("--n-predict",    self.n_predict),
        ]:
            val = var.get().strip()
            if val:
                if flag == "--n-predict" and val == "-1":
                    continue
                if flag == "--n-gpu-layers" and val == "0":
                    continue
                cmd_list += [flag, val]

        # Boolean flags
        for flag, var in self._bool_flags.items():
            if var.get():
                if supports_flag(flag, srv):
                    cmd_list.append(flag)
                else:
                    self._log(f"⚠ {flag} not supported by this build, skipping")

        # Value flags
        for flag, var in self._val_flags.items():
            val = var.get().strip()
            if val:
                cmd_list += [flag, val]

        # Extra args
        if self.extra_args.get().strip():
            import shlex
            cmd_list += shlex.split(self.extra_args.get().strip())

        shell_cmd = shell_quote_list(cmd_list)
        self._log(f"▶ {shell_cmd}")

        if not launch_in_terminal(shell_cmd, title="llama-server"):
            messagebox.showerror("Error", "No terminal found!")

    def _open_webui(self):
        host = self.host.get().strip() or "127.0.0.1"
        port = self.port.get().strip() or "8080"
        url  = f"http://{host}:{port}"
        self._log(f"🌐 Opening: {url}")
        import webbrowser
        webbrowser.open(url)

    # ── public ───────────────────────────────────────────────────────────

    def startup_log(self, msg: str):
        self._log(msg)
