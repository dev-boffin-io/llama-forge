"""
server_tab.py — llama-server tab for llama-forge GUI.

Starts llama-server in the BACKGROUND (no terminal window needed).
Output is streamed directly into the log box inside the GUI.

PID persistence: when a server is started, its PID is written to a
~/.cache/llama-forge/server_<port>.pid file so that GUI restarts can
still show an active Stop button and terminate the process.

Multi-server support: each port gets its own entry in the active-server
list. Select a running server from the list and press Stop to kill it.
"""

from __future__ import annotations
import os
import signal
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.llama_detect import models_dir, supports_flag
from utils.terminal import shell_quote_list
from gui import make_scrollable, log_widget, append_log

# ── PID file helpers ──────────────────────────────────────────────────────────

_PID_DIR = os.path.join(os.path.expanduser("~"), ".cache", "llama-forge")


def _pid_path(port: str) -> str:
    os.makedirs(_PID_DIR, exist_ok=True)
    return os.path.join(_PID_DIR, f"server_{port}.pid")


def _write_pid(port: str, pid: int) -> None:
    try:
        with open(_pid_path(port), "w") as f:
            f.write(str(pid))
    except OSError:
        pass


def _read_pid(port: str) -> int | None:
    try:
        with open(_pid_path(port)) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def _clear_pid(port: str) -> None:
    try:
        os.remove(_pid_path(port))
    except OSError:
        pass


def _pid_alive(pid: int) -> bool:
    """Return True if a process with this PID is running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


# ─────────────────────────────────────────────────────────────────────────────


class ServerTab:
    def __init__(self, notebook: ttk.Notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Server")

        # port → {"proc": Popen|None, "saved_pid": int|None, "label": str}
        self._servers: dict[str, dict] = {}

        self._build()
        self._restore_state()   # check for servers left running from last session

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
            "--flash-attn":             tk.BooleanVar(value=False),
            "--mlock":                  tk.BooleanVar(value=False),
            "--no-mmap":                tk.BooleanVar(value=False),
            "--no-warmup":              tk.BooleanVar(value=False),
            "--embedding":              tk.BooleanVar(value=False),
            "--reranking":              tk.BooleanVar(value=False),
            "--log-disable":            tk.BooleanVar(value=False),
            "--verbose":                tk.BooleanVar(value=False),
            "--slots-endpoint-disable": tk.BooleanVar(value=False),
            "--metrics":                tk.BooleanVar(value=False),
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
            "--api-key":        tk.StringVar(),
            "--chat-template":  tk.StringVar(),
            "--system-prompt":  tk.StringVar(),
            "--rope-freq-base": tk.StringVar(),
            "--rope-freq-scale":tk.StringVar(),
            "--override-kv":    tk.StringVar(),
            "--lora":           tk.StringVar(),
            "--path":           tk.StringVar(),
            "--ssl-key-file":   tk.StringVar(),
            "--ssl-cert-file":  tk.StringVar(),
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

        # ── Active Servers list ───────────────────────────────────────
        sf = ttk.LabelFrame(f, text="Active Servers  (select → Stop)", padding=8)
        sf.pack(fill=tk.X, pady=6)
        sf.columnconfigure(0, weight=1)

        self._server_listbox = tk.Listbox(
            sf, height=4, selectmode=tk.SINGLE,
            font=self.app.log_font, bg="#1e1e1e", fg="#a9dc76",
            selectbackground="#3d3d3d", selectforeground="#ffffff",
            activestyle="none",
        )
        self._server_listbox.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        # ── Buttons ───────────────────────────────────────────────────
        btn_row = ttk.Frame(f)
        btn_row.pack(fill=tk.X, pady=14)
        self._start_btn = ttk.Button(btn_row, text="▶ Start Server",
                                     command=self._run_server)
        self._start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self._stop_btn = ttk.Button(btn_row, text="⏹ Stop Selected",
                                    command=self._stop_server, state="disabled")
        self._stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(btn_row, text="🌐 Open Web UI",
                   command=self._open_webui).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        # ── Log ───────────────────────────────────────────────────────
        self.logbox = log_widget(log_host, self.app.log_font)
        self.logbox.configure(height=10)
        self.logbox.pack(fill="x", expand=False)

        self._log("✔ Server runs in background — output appears here")

    # ── server list helpers ───────────────────────────────────────────────

    def _listbox_label(self, port: str) -> str:
        entry = self._servers.get(port, {})
        proc = entry.get("proc")
        saved_pid = entry.get("saved_pid")
        pid = proc.pid if (proc and proc.poll() is None) else saved_pid
        return f"port {port}  PID {pid}  [{entry.get('label', '')}]"

    def _refresh_listbox(self):
        """Rebuild the listbox from self._servers."""
        self._server_listbox.delete(0, tk.END)
        for port in list(self._servers.keys()):
            self._server_listbox.insert(tk.END, self._listbox_label(port))
        if self._servers:
            self._stop_btn.config(state="normal")
        else:
            self._stop_btn.config(state="disabled")

    def _selected_port(self) -> str | None:
        """Return the port string of the selected listbox item, or None."""
        sel = self._server_listbox.curselection()
        if not sel:
            return None
        ports = list(self._servers.keys())
        idx = sel[0]
        return ports[idx] if idx < len(ports) else None

    # ── state restore (GUI reopen) ────────────────────────────────────────

    def _restore_state(self):
        """Check for servers left running from previous GUI sessions."""
        try:
            for fname in os.listdir(_PID_DIR):
                if not fname.startswith("server_") or not fname.endswith(".pid"):
                    continue
                port = fname[len("server_"):-len(".pid")]
                pid = _read_pid(port)
                if pid and _pid_alive(pid):
                    self._servers[port] = {"proc": None, "saved_pid": pid,
                                           "label": "restored"}
                    self._log(f"⚡ Server already running on port {port} (PID {pid})")
                else:
                    if pid:
                        _clear_pid(port)
        except FileNotFoundError:
            pass
        self._refresh_listbox()

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

        port = self.port.get().strip() or "8080"

        if port in self._servers:
            messagebox.showwarning(
                "Already running",
                f"A server is already tracked on port {port}.\n"
                "Stop it first or use a different port.",
            )
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

        self._log(f"▶ {shell_quote_list(cmd_list)}")

        import subprocess as _sp
        try:
            proc = _sp.Popen(
                cmd_list,
                stdout=_sp.PIPE,
                stderr=_sp.STDOUT,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            messagebox.showerror("Error", f"llama-server not found:\n{srv}")
            return

        model_short = os.path.basename(self.app.server_model)
        _write_pid(port, proc.pid)
        self._servers[port] = {"proc": proc, "saved_pid": None,
                                "label": model_short}
        self._log(f"✔ PID {proc.pid} saved (port {port})")
        self._refresh_listbox()

        # Capture proc and port locally — reader thread must NOT touch self._servers
        def _reader(p=proc, _port=port):
            try:
                for raw in p.stdout:
                    line = raw.rstrip("\n")
                    if line:
                        self.frame.after(0, lambda l=line: append_log(self.logbox, l + "\n"))
                p.wait()
                rc = p.returncode
            except Exception:
                import traceback
                tb = traceback.format_exc()
                self.frame.after(0, lambda: append_log(self.logbox, f"\n❌ Exception:\n{tb}\n"))
                rc = -1
            finally:
                _clear_pid(_port)
                self.frame.after(0, self._on_server_done, _port, rc)

        threading.Thread(target=_reader, daemon=True).start()

    def _stop_server(self):
        port = self._selected_port()
        if port is None:
            # Fall back to port field value if nothing selected in listbox
            port = self.port.get().strip() or "8080"

        entry = self._servers.get(port)
        if entry is None:
            self._log(f"⚠ No tracked server on port {port}.")
            return

        proc      = entry.get("proc")
        saved_pid = entry.get("saved_pid")

        if proc and proc.poll() is None:
            # Server started in this session — terminate via Popen handle;
            # _on_server_done (called from _reader) will clean up self._servers
            proc.terminate()
            self._log(f"⏹ Sent SIGTERM to server on port {port} (PID {proc.pid}).")
        elif saved_pid and _pid_alive(saved_pid):
            # Server restored from PID file (previous session)
            try:
                os.kill(saved_pid, signal.SIGTERM)
                self._log(f"⏹ Sent SIGTERM to PID {saved_pid} (port {port}).")
            except ProcessLookupError:
                self._log(f"⚠ PID {saved_pid} already gone.")
            _clear_pid(port)
            del self._servers[port]
            self._refresh_listbox()
        else:
            self._log(f"⚠ Server on port {port} is not alive.")
            _clear_pid(port)
            del self._servers[port]
            self._refresh_listbox()

    def _on_server_done(self, port: str, rc: int):
        self._log(f"\n--- server on port {port} exited (code {rc}) ---\n")
        self._servers.pop(port, None)
        self._refresh_listbox()

    def _open_webui(self):
        host = self.host.get().strip() or "127.0.0.1"
        # If a server is selected in the list, use its port; else use field
        port = self._selected_port() or self.port.get().strip() or "8080"
        url  = f"http://{host}:{port}"
        self._log(f"🌐 Opening: {url}")
        import webbrowser
        webbrowser.open(url)

    # ── public ───────────────────────────────────────────────────────────

    def startup_log(self, msg: str):
        self._log(msg)
