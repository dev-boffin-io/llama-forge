"""
gui/server_tab.py — llama-server tab for llama-forge GUI (PyQt6).

Starts llama-server in the BACKGROUND (no terminal window needed) using
QProcess. Output is streamed directly into the log box inside the GUI.

PID persistence: when a server is started, its PID is written to a
~/.cache/llama-forge/server_<port>.pid file so that GUI restarts can
still show an active Stop button and terminate the process.

Multi-server support: each port gets its own entry in the active-server
list. Select a running server from the list and press Stop to kill it.

Cross-platform: Linux · macOS · Windows · Android/Termux

Updated for llama.cpp 2025:
  New bool flags  : --jinja, --cont-batching, --kv-unified,
                    --no-prefill-assistant, --ctx-shift-disable
  New value flags : --ubatch-size, --cache-reuse, --cache-type-k,
                    --cache-type-v, --defrag-thold, --prio,
                    --slot-save-path, --reasoning-budget,
                    --tensor-split, --think
"""

from __future__ import annotations

import os
import shlex
import sys
import webbrowser

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QFileDialog,
    QMessageBox, QListWidget,
)
from PyQt6.QtCore import Qt, QProcess

from core.llama_detect import models_dir, supports_flag, exe_name, resolve_exe
from core.quant_logic import KV_CACHE_TYPES
from utils.terminal import shell_quote_list
from gui import make_scrollable, LogConsole, append_log, card

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
    """Return True if a process with this PID is running (cross-platform)."""
    if sys.platform == "win32":
        import ctypes
        SYNCHRONIZE = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if not handle:
            return False
        result = ctypes.windll.kernel32.WaitForSingleObject(handle, 0)
        ctypes.windll.kernel32.CloseHandle(handle)
        return result != 0
    else:
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False


def _terminate_pid(pid: int) -> None:
    """Send termination signal cross-platform."""
    if sys.platform == "win32":
        import ctypes
        PROCESS_TERMINATE = 0x0001
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        if handle:
            ctypes.windll.kernel32.TerminateProcess(handle, 1)
            ctypes.windll.kernel32.CloseHandle(handle)
    else:
        import signal
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def _default_browse_dir(current: str) -> str:
    if current and os.path.exists(current):
        return os.path.dirname(current)
    return os.path.expanduser("~")


# ─────────────────────────────────────────────────────────────────────────────


class ServerTab(QWidget):
    def __init__(self, app: QWidget):
        super().__init__()
        self.app = app

        # port → {"proc": QProcess|None, "saved_pid": int|None, "label": str}
        self._servers: dict[str, dict] = {}

        self._build()
        self._restore_state()

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

        btn_model = QPushButton("📦  Select GGUF model (for Server)")
        btn_model.clicked.connect(self._pick_model)
        f.addWidget(btn_model)

        # ── Core args ─────────────────────────────────────────────────
        core = card("Core Arguments")
        core_l = QGridLayout(core)
        for c in (1, 3, 5):
            core_l.setColumnStretch(c, 1)

        self.host       = QLineEdit("127.0.0.1")
        self.port       = QLineEdit("8080")
        self.ctx        = QLineEdit("2048")
        self.threads    = QLineEdit("2")
        self.n_gpu      = QLineEdit("0")
        self.batch      = QLineEdit("512")
        self.ubatch     = QLineEdit("512")
        self.parallel   = QLineEdit("1")
        self.n_predict  = QLineEdit("-1")

        rows = [
            [("--host",        self.host),
             ("--port",        self.port),
             ("--ctx-size",    self.ctx)],
            [("--threads",     self.threads),
             ("--n-gpu-layers", self.n_gpu),
             ("--batch-size",  self.batch)],
            [("--ubatch-size", self.ubatch),
             ("--parallel",    self.parallel),
             ("--n-predict",   self.n_predict)],
        ]
        for r, items in enumerate(rows):
            for c, (lbl, widget) in enumerate(items):
                core_l.addWidget(QLabel(lbl), r, c * 2, Qt.AlignmentFlag.AlignRight)
                core_l.addWidget(widget, r, c * 2 + 1)
        f.addWidget(core)

        # ── KV Cache section ────────────────────────────────────────────
        kv = card("KV Cache  (2025)")
        kv_l = QGridLayout(kv)
        kv_l.setColumnStretch(1, 1)
        kv_l.setColumnStretch(3, 1)

        self.cache_type_k = QComboBox()
        self.cache_type_k.addItems(KV_CACHE_TYPES)
        self.cache_type_v = QComboBox()
        self.cache_type_v.addItems(KV_CACHE_TYPES)
        self.cache_reuse  = QLineEdit()
        self.defrag_thold = QLineEdit()

        kv_l.addWidget(QLabel("--cache-type-k"), 0, 0, Qt.AlignmentFlag.AlignRight)
        kv_l.addWidget(self.cache_type_k, 0, 1)
        kv_l.addWidget(QLabel("--cache-type-v"), 0, 2, Qt.AlignmentFlag.AlignRight)
        kv_l.addWidget(self.cache_type_v, 0, 3)

        kv_l.addWidget(QLabel("--cache-reuse (prefix tokens, 0=off)"), 1, 0, Qt.AlignmentFlag.AlignRight)
        kv_l.addWidget(self.cache_reuse, 1, 1)
        kv_l.addWidget(QLabel("--defrag-thold (0.0–1.0, -1=off)"), 1, 2, Qt.AlignmentFlag.AlignRight)
        kv_l.addWidget(self.defrag_thold, 1, 3)
        f.addWidget(kv)

        # ── Boolean flags ─────────────────────────────────────────────
        bf = card("Flags (checked = enabled)")
        bf_l = QGridLayout(bf)
        bool_flag_names = [
            "--flash-attn",
            "--jinja",
            "--cont-batching",
            "--kv-unified",
            "--mlock",
            "--no-mmap",
            "--no-warmup",
            "--no-prefill-assistant",
            "--ctx-shift-disable",
            "--embedding",
            "--reranking",
            "--log-disable",
            "--verbose",
            "--slots-endpoint-disable",
            "--metrics",
        ]
        self._bool_flags: dict[str, QCheckBox] = {}
        cols = 3
        for i, flag in enumerate(bool_flag_names):
            cb = QCheckBox(flag)
            self._bool_flags[flag] = cb
            bf_l.addWidget(cb, i // cols, i % cols)
        f.addWidget(bf)

        # ── Value flags (optional) ──────────────────────────────────────
        vf = card("Optional Arguments (empty = skip)")
        vf_l = QGridLayout(vf)
        vf_l.setColumnStretch(1, 1)
        val_flag_names = [
            "--api-key",
            "--chat-template",
            "--system-prompt",
            "--slot-save-path",
            "--reasoning-budget",
            "--think",
            "--prio",
            "--tensor-split",
            "--rope-freq-base",
            "--rope-freq-scale",
            "--override-kv",
            "--lora",
            "--path",
            "--ssl-key-file",
            "--ssl-cert-file",
        ]
        self._val_flags: dict[str, QLineEdit] = {}
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

        # ── Active Servers list ───────────────────────────────────────
        sf = card("Active Servers  (select → Stop)")
        sf_l = QVBoxLayout(sf)
        self._server_list = QListWidget()
        self._server_list.setFixedHeight(200)
        sf_l.addWidget(self._server_list)
        f.addWidget(sf)

        # ── Buttons ───────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("▶  Start Server")
        self._start_btn.setObjectName("PrimaryButton")
        self._start_btn.clicked.connect(self._run_server)
        self._stop_btn = QPushButton("⏹  Stop Selected")
        self._stop_btn.setObjectName("StopButton")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_server)
        self._webui_btn = QPushButton("🌐  Open Web UI")
        self._webui_btn.clicked.connect(self._open_webui)
        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addWidget(self._webui_btn)
        f.addLayout(btn_row)

        f.addStretch(1)

        outer.addWidget(make_scrollable(content), 1)

        # ── Log ───────────────────────────────────────────────────────
        self.logbox = LogConsole(height=324)
        outer.addWidget(self.logbox)

        self._log("✔ Server runs in background — output appears here")

    # ── server list helpers ───────────────────────────────────────────────

    def _listbox_label(self, port: str) -> str:
        entry = self._servers.get(port, {})
        proc: QProcess | None = entry.get("proc")
        saved_pid = entry.get("saved_pid")
        if proc is not None and proc.state() != QProcess.ProcessState.NotRunning:
            pid = proc.processId()
        else:
            pid = saved_pid
        return f"port {port}   PID {pid}   [{entry.get('label', '')}]"

    def _refresh_listbox(self):
        self._server_list.clear()
        for port in list(self._servers.keys()):
            self._server_list.addItem(self._listbox_label(port))
        self._stop_btn.setEnabled(bool(self._servers))

    def _selected_port(self) -> str | None:
        row = self._server_list.currentRow()
        if row < 0:
            return None
        ports = list(self._servers.keys())
        return ports[row] if row < len(ports) else None

    # ── state restore ─────────────────────────────────────────────────────

    def _restore_state(self):
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
        append_log(self.logbox, msg)

    def _pick_bin_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select llama.cpp build/bin",
            self.app.bin_dir or os.path.expanduser("~"),
        )
        if not d:
            return
        srv_path = os.path.join(d, exe_name("llama-server"))
        if os.path.isfile(srv_path):
            self.app.bin_dir = d
            self.app.save()
            self._log(f"✔ bin dir: {d}")
        else:
            QMessageBox.critical(
                self, "Error",
                f"{exe_name('llama-server')} not found in selected directory!"
            )

    def _pick_model(self):
        initial = _default_browse_dir(getattr(self.app, "server_model", "")) or models_dir()
        p, _ = QFileDialog.getOpenFileName(
            self, "Select GGUF model", initial, "GGUF (*.gguf)"
        )
        if p:
            self.app.server_model = p
            self.app.save()
            self._log(f"✔ Model: {p}")

    def _run_server(self):
        if not self.app.bin_dir:
            QMessageBox.critical(self, "Error", "Select llama.cpp build/bin first!")
            return
        if not getattr(self.app, "server_model", ""):
            QMessageBox.critical(self, "Error", "Select a GGUF model first!")
            return

        port = self.port.text().strip() or "8080"

        if port in self._servers:
            QMessageBox.warning(
                self, "Already running",
                f"A server is already tracked on port {port}.\n"
                "Stop it first or use a different port.",
            )
            return

        srv = resolve_exe("llama-server", self.app.bin_dir)
        cmd_list = [srv, "-m", self.app.server_model]

        # Core args
        for flag, widget in [
            ("--host",         self.host),
            ("--port",         self.port),
            ("--ctx-size",     self.ctx),
            ("--threads",      self.threads),
            ("--n-gpu-layers", self.n_gpu),
            ("--batch-size",   self.batch),
            ("--ubatch-size",  self.ubatch),
            ("--parallel",     self.parallel),
            ("--n-predict",    self.n_predict),
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

        # KV cache flags (only add if non-default)
        k_type = self.cache_type_k.currentText()
        v_type = self.cache_type_v.currentText()
        if k_type and k_type != "f16":
            cmd_list += ["--cache-type-k", k_type]
        if v_type and v_type != "f16":
            cmd_list += ["--cache-type-v", v_type]
        if self.cache_reuse.text().strip():
            cmd_list += ["--cache-reuse", self.cache_reuse.text().strip()]
        if self.defrag_thold.text().strip():
            cmd_list += ["--defrag-thold", self.defrag_thold.text().strip()]

        # Boolean flags
        for flag, cb in self._bool_flags.items():
            if cb.isChecked():
                if supports_flag(flag, srv):
                    cmd_list.append(flag)
                else:
                    self._log(f"⚠ {flag} not supported by this build, skipping")

        # Value flags
        for flag, le in self._val_flags.items():
            val = le.text().strip()
            if val:
                cmd_list += [flag, val]

        # Extra args
        extra = self.extra_args.text().strip()
        if extra:
            cmd_list += shlex.split(extra)

        self._log(f"▶ {shell_quote_list(cmd_list)}")

        proc = QProcess(self)
        proc.setProgram(cmd_list[0])
        proc.setArguments(cmd_list[1:])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(lambda p=port: self._on_ready_read(p))
        proc.errorOccurred.connect(lambda err, p=port: self._on_error(p, err))
        proc.finished.connect(lambda code, status, p=port: self._on_server_done(p, code))

        proc.start()
        if not proc.waitForStarted(3000):
            QMessageBox.critical(
                self, "Error",
                f"{exe_name('llama-server')} not found or failed to start:\n{srv}"
            )
            return

        model_short = os.path.basename(self.app.server_model)
        _write_pid(port, proc.processId())
        self._servers[port] = {"proc": proc, "saved_pid": None, "label": model_short}
        self._log(f"✔ PID {proc.processId()} saved (port {port})")
        self._refresh_listbox()

    def _on_ready_read(self, port: str):
        entry = self._servers.get(port)
        if not entry:
            return
        proc: QProcess | None = entry.get("proc")
        if proc is None:
            return
        data = proc.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            if line:
                append_log(self.logbox, line)

    def _on_error(self, port: str, error):
        self._log(f"⚠ QProcess error on port {port}: {error}")

    def _stop_server(self):
        port = self._selected_port()
        if port is None:
            port = self.port.text().strip() or "8080"

        entry = self._servers.get(port)
        if entry is None:
            self._log(f"⚠ No tracked server on port {port}.")
            return

        proc: QProcess | None = entry.get("proc")
        saved_pid = entry.get("saved_pid")

        if proc is not None and proc.state() != QProcess.ProcessState.NotRunning:
            proc.terminate()
            self._log(f"⏹ Sent terminate to server on port {port} (PID {proc.processId()}).")
        elif saved_pid and _pid_alive(saved_pid):
            _terminate_pid(saved_pid)
            self._log(f"⏹ Sent terminate to PID {saved_pid} (port {port}).")
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
        _clear_pid(port)
        self._servers.pop(port, None)
        self._refresh_listbox()

    def _open_webui(self):
        host = self.host.text().strip() or "127.0.0.1"
        port = self._selected_port() or self.port.text().strip() or "8080"
        url = f"http://{host}:{port}"
        self._log(f"🌐 Opening: {url}")
        webbrowser.open(url)

    # ── public ───────────────────────────────────────────────────────────

    def startup_log(self, msg: str):
        self._log(msg)

    def on_app_close(self):
        """Best-effort: just leave background servers running (PID file
        persists so the GUI can reattach on next launch)."""
        pass
