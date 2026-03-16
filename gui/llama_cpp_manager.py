#!/usr/bin/env python3
"""
llama.cpp Tools GUI
Project-root aware — works as script or PyInstaller onefile.
Config is saved next to the script (or beside the binary for onefile).
"""

import os
import sys
import json
import subprocess
import shutil
import tkinter as tk
from tkinter import font, ttk, filedialog, messagebox, scrolledtext
import threading

# ─────────────────────────────────────────────
# Project-root detection
# Works for:
#   1. Normal script:   python3 llama_cpp_manager.py  (anywhere in the llama.cpp tree)
#   2. PyInstaller onefile: the binary placed in llama.cpp root or run from there
# ─────────────────────────────────────────────

def _find_llama_root():
    """
    Walk up from the script / executable location looking for a directory
    that looks like the llama.cpp project root (contains CMakeLists.txt AND
    convert_hf_to_gguf.py).  Falls back to CWD, then home.
    """
    if getattr(sys, 'frozen', False):          # PyInstaller onefile
        start = os.path.dirname(sys.executable)
    else:
        start = os.path.dirname(os.path.abspath(__file__))

    probe = start
    for _ in range(6):                          # walk up at most 6 levels
        if (os.path.isfile(os.path.join(probe, "CMakeLists.txt")) and
                os.path.isfile(os.path.join(probe, "convert_hf_to_gguf.py"))):
            return probe
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent

    # fallback: CWD, then home
    for fallback in (os.getcwd(), os.path.expanduser("~")):
        if (os.path.isfile(os.path.join(fallback, "CMakeLists.txt")) and
                os.path.isfile(os.path.join(fallback, "convert_hf_to_gguf.py"))):
            return fallback

    return start   # best-effort

LLAMA_ROOT = _find_llama_root()
BIN_DIR_DEFAULT = os.path.join(LLAMA_ROOT, "build", "bin")
MODELS_DIR_DEFAULT = os.path.join(LLAMA_ROOT, "models")

# ─────────────────────────────────────────────
# Config persistence  (~/.llama_cpp_gui.json)
# Stored paths are kept absolute so the app
# works even if launched from a different CWD.
# ─────────────────────────────────────────────

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".llama_cpp_gui.json")

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

APP = "llama.cpp Tools GUI"

def which(cmd):
    return shutil.which(cmd)

def detect_terminal():
    for t in ["xfce4-terminal", "gnome-terminal", "xterm", "konsole", "terminator"]:
        if which(t):
            return t
    return None

TERMINAL = detect_terminal()

def supports(flag, exe):
    try:
        output = subprocess.check_output(
            [exe, "--help"], stderr=subprocess.STDOUT, text=True
        )
        return flag in output
    except Exception:
        return False

def _models_dir():
    """Return best initial directory for GGUF browse dialogs."""
    if os.path.isdir(MODELS_DIR_DEFAULT):
        return MODELS_DIR_DEFAULT
    return LLAMA_ROOT

def _bin_dir_valid(d):
    return d and os.path.isfile(os.path.join(d, "llama-cli"))


# ─────────────────────────────────────────────
# Converter sub-window
# ─────────────────────────────────────────────

class ConverterManager(tk.Toplevel):
    def __init__(self, parent, llama_root: str):
        super().__init__(parent)
        self.title("llama.cpp Converter Manager (Pro)")
        self.geometry("1500x950")
        self.minsize(1200, 800)

        style = ttk.Style(self)
        style.theme_use('clam')

        default_font = tk.font.nametofont("TkDefaultFont")
        default_font.configure(size=30, family="DejaVu Sans")
        self.option_add("*Font", default_font)

        self.output_font = tk.font.Font(family="DejaVu Sans Mono", size=26)

        style.configure("TButton", padding=20)
        style.configure("TFrame", padding=20)

        self.llama_dir = tk.StringVar(value=llama_root)
        self.script    = tk.StringVar()
        self.input_path  = tk.StringVar()
        self.output_path = tk.StringVar()
        self.extra_args  = tk.StringVar()
        self.dry_run     = tk.BooleanVar(value=False)
        self.base_model_path = tk.StringVar()

        self.create_ui()

    def create_ui(self):
        frm = ttk.Frame(self, padding=20)
        frm.pack(fill="both", expand=True)

        # llama.cpp dir
        ttk.Label(frm, text="llama.cpp Directory").grid(row=0, column=0, sticky="w", pady=10)
        ttk.Entry(frm, textvariable=self.llama_dir, width=60).grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(frm, text="Browse", command=self.browse_llama).grid(row=0, column=2, padx=10, pady=10)

        # script selection
        ttk.Label(frm, text="Convert Script").grid(row=1, column=0, sticky="w", pady=10)
        scripts = [
            "convert_hf_to_gguf.py",
            "convert_llama_ggml_to_gguf.py",
            "convert_lora_to_gguf.py",
        ]
        self.script_cb = ttk.Combobox(
            frm, values=scripts, textvariable=self.script, width=57, state="readonly"
        )
        self.script_cb.grid(row=1, column=1, padx=10, pady=10)
        self.script_cb.current(0)
        self.script_cb.bind("<<ComboboxSelected>>", self.on_script_change)

        # input
        ttk.Label(frm, text="Input Model / Path").grid(row=2, column=0, sticky="w", pady=10)
        ttk.Entry(frm, textvariable=self.input_path, width=60).grid(row=2, column=1, padx=10, pady=10)
        ttk.Button(frm, text="Browse", command=self.browse_input).grid(row=2, column=2, padx=10, pady=10)

        # LoRA base model (shown only for LoRA script)
        self.base_row = 3
        self.base_label = ttk.Label(frm, text="Base Model (for LoRA)", foreground="red")
        self.base_entry = ttk.Entry(frm, textvariable=self.base_model_path, width=60)
        self.base_btn   = ttk.Button(frm, text="Browse", command=self.browse_base)

        # output
        ttk.Label(frm, text="Output File / Dir").grid(row=4, column=0, sticky="w", pady=10)
        ttk.Entry(frm, textvariable=self.output_path, width=60).grid(row=4, column=1, padx=10, pady=10)
        ttk.Button(frm, text="Browse", command=self.browse_output).grid(row=4, column=2, padx=10, pady=10)

        # extra args
        ttk.Label(frm, text="Extra Arguments").grid(row=5, column=0, sticky="w", pady=10)
        ttk.Entry(frm, textvariable=self.extra_args, width=60).grid(
            row=5, column=1, columnspan=2, padx=10, pady=10, sticky="ew"
        )

        # dry run
        ttk.Checkbutton(
            frm, text="Show command only (Dry Run)", variable=self.dry_run, padding=10
        ).grid(row=6, column=0, columnspan=3, pady=15)

        # run
        ttk.Button(frm, text="Run Conversion 🚀", command=self.run).grid(
            row=7, column=0, columnspan=3, pady=30
        )

        # output box
        output_frame = ttk.Frame(frm)
        output_frame.grid(row=8, column=0, columnspan=3, sticky="nsew", pady=10)
        self.output = tk.Text(
            output_frame,
            font=self.output_font,
            bg="#1e1e1e",
            fg="#00ff88",
            insertbackground="#00ff88",
            relief="flat",
            padx=15,
            pady=15,
        )
        self.output.pack(fill="both", expand=True)

        frm.rowconfigure(8, weight=1)
        frm.columnconfigure(1, weight=1)

        self.on_script_change(None)

    def on_script_change(self, event):
        script = self.script.get()
        self.extra_args.set("")

        if script == "convert_lora_to_gguf.py":
            self.base_label.grid(row=self.base_row, column=0, sticky="w", pady=10)
            self.base_entry.grid(row=self.base_row, column=1, padx=10, pady=10)
            self.base_btn.grid(row=self.base_row,   column=2, padx=10, pady=10)
            self.log("⚠️ LoRA conversion requires base model GGUF!\n")
        else:
            self.base_label.grid_forget()
            self.base_entry.grid_forget()
            self.base_btn.grid_forget()

        if script == "convert_hf_to_gguf.py":
            self.extra_args.set("--outtype f16")
            self.log("ℹ️ Auto-filled: --outtype f16 (recommended for HF)\n")
        elif script == "convert_llama_ggml_to_gguf.py":
            self.extra_args.set("--outtype f16")
            self.log("⚠️ LEGACY GGML → GGUF (use f16)\n")
        elif script == "convert_lora_to_gguf.py":
            self.extra_args.set("--outtype q8_0")

    def browse_llama(self):
        d = filedialog.askdirectory(
            title="Select llama.cpp directory", initialdir=LLAMA_ROOT
        )
        if d:
            self.llama_dir.set(d)

    def browse_input(self):
        d = filedialog.askdirectory(
            title="Select input model/path", initialdir=_models_dir()
        )
        if d:
            self.input_path.set(d)

    def browse_output(self):
        d = filedialog.askdirectory(
            title="Select output directory", initialdir=_models_dir()
        )
        if d:
            self.output_path.set(d)

    def browse_base(self):
        p = filedialog.askopenfilename(
            title="Select base model GGUF",
            initialdir=_models_dir(),
            filetypes=[("GGUF", "*.gguf")],
        )
        if p:
            self.base_model_path.set(p)

    def log(self, text):
        self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.update_idletasks()

    def run(self):
        if not self.llama_dir.get():
            messagebox.showerror("Error", "llama.cpp directory missing", parent=self)
            return

        script_path = os.path.join(self.llama_dir.get(), self.script.get())
        if not os.path.isfile(script_path):
            messagebox.showerror(
                "Error", f"Script not found:\n{script_path}", parent=self
            )
            return

        cmd = ["python3", script_path, self.input_path.get()]

        if self.output_path.get():
            cmd += ["--outfile", self.output_path.get()]

        if self.script.get() == "convert_lora_to_gguf.py":
            if not self.base_model_path.get():
                messagebox.showerror(
                    "Error", "Base model required for LoRA conversion!", parent=self
                )
                return
            cmd += ["--base", self.base_model_path.get()]

        if self.extra_args.get().strip():
            cmd += self.extra_args.get().split()

        full_cmd = " ".join(cmd)
        self.log(f"\n▶ Command:\n{full_cmd}\n\n")

        if self.dry_run.get():
            self.log("🛠️ Dry Run mode – command shown only (not executed)\n")
            return

        threading.Thread(target=self.execute, args=(cmd,), daemon=True).start()

    def execute(self, cmd):
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )
            for line in process.stdout:
                self.log(line)
            process.wait()
            if process.returncode == 0:
                self.log("\n✅ Conversion completed successfully!\n")
            else:
                self.log(f"\n⚠️ Exited with code {process.returncode}\n")
        except Exception as e:
            self.log(f"\n❌ Error: {e}\n")


# ─────────────────────────────────────────────
# Main App
# ─────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP)
        self.geometry("1700x900")
        self.minsize(1280, 720)

        style = ttk.Style()
        style.theme_use('clam')

        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=30, family="DejaVu Sans")
        self.option_add("*Font", default_font)

        self.log_font = font.Font(family="DejaVu Sans Mono", size=26)

        style.configure("TButton", padding=20)
        style.configure("TNotebook", padding=10)
        style.configure("TNotebook.Tab", padding=(20, 10))
        style.configure("TFrame", padding=20)

        # ── Load persisted config ──────────────────────────────────────
        cfg = load_config()

        # bin_dir: config → auto-detect → empty
        saved_bin = cfg.get("bin_dir", "")
        if _bin_dir_valid(saved_bin):
            self.bin_dir = saved_bin
        elif _bin_dir_valid(BIN_DIR_DEFAULT):
            self.bin_dir = BIN_DIR_DEFAULT
        else:
            self.bin_dir = ""

        # last-used model paths (remembered across sessions)
        self.chat_model = cfg.get("chat_model", "")
        self.quant_gguf = cfg.get("quant_gguf", "")

        self.build_ui()

        # Convert Tools button (top-right)
        convert_btn = ttk.Button(
            self, text="Convert Tools", command=self.open_converter
        )
        convert_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

        # Show auto-detected root info
        self._startup_info()

    def _startup_info(self):
        info = f"📁 Project root: {LLAMA_ROOT}"
        self.log(info, tab="chat")
        self.log(info, tab="quant")
        if self.bin_dir:
            self.log(f"✔ bin dir auto-set: {self.bin_dir}", tab="chat")
            self.log(f"✔ bin dir auto-set: {self.bin_dir}", tab="quant")
        else:
            self.log(
                f"⚠️ build/bin not found at {BIN_DIR_DEFAULT} — please select manually.",
                tab="chat",
            )
        if self.chat_model:
            self.log(f"✔ Last chat model: {self.chat_model}", tab="chat")
        if self.quant_gguf:
            self.log(f"✔ Last quant GGUF: {self.quant_gguf}", tab="quant")

    def _save(self):
        save_config({
            "bin_dir":    self.bin_dir,
            "chat_model": self.chat_model,
            "quant_gguf": self.quant_gguf,
        })

    def open_converter(self):
        ConverterManager(self, LLAMA_ROOT)

    def log(self, msg, tab="chat"):
        if tab == "chat" and hasattr(self, 'chat_logbox'):
            self.chat_logbox.insert(tk.END, msg + "\n")
            self.chat_logbox.see(tk.END)
        elif tab == "quant" and hasattr(self, 'quant_logbox'):
            self.quant_logbox.insert(tk.END, msg + "\n")
            self.quant_logbox.see(tk.END)

    def build_ui(self):
        tabs = ttk.Notebook(self)
        tabs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chat_tab  = ttk.Frame(tabs)
        self.quant_tab = ttk.Frame(tabs)

        tabs.add(self.chat_tab,  text="Chat (SAFE)")
        tabs.add(self.quant_tab, text="Quantize")

        self.build_chat_tab()
        self.build_quant_tab()

    # ── bin dir ────────────────────────────────────────────────────────

    def pick_bin_dir(self):
        initial = self.bin_dir if self.bin_dir else LLAMA_ROOT
        d = filedialog.askdirectory(
            title="Select llama.cpp build/bin directory", initialdir=initial
        )
        if not d:
            return
        if os.path.exists(os.path.join(d, "llama-cli")):
            self.bin_dir = d
            self._save()
            self.log(f"✔ bin dir set: {d}", tab="chat")
            self.log(f"✔ bin dir set: {d}", tab="quant")
        else:
            messagebox.showerror("Error", "llama-cli not found in selected directory!")

    # ── Chat tab ───────────────────────────────────────────────────────

    def build_chat_tab(self):
        f = ttk.Frame(self.chat_tab)
        f.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Button(
            f, text="Select llama.cpp build/bin (Shared)", command=self.pick_bin_dir
        ).pack(fill=tk.X, pady=10)
        ttk.Button(
            f, text="Select GGUF model (for Chat)", command=self.pick_chat_model
        ).pack(fill=tk.X, pady=10)

        args = ttk.Frame(f)
        args.pack(fill=tk.X, pady=20)

        self.template = tk.StringVar(value="chatml")
        self.ctx      = tk.StringVar(value="2048")
        self.threads  = tk.StringVar(value="2")

        ttk.Label(args, text="Chat template").grid(row=0, column=0, padx=15, sticky="e")
        ttk.Entry(args, textvariable=self.template, width=12).grid(row=0, column=1, padx=10)

        ttk.Label(args, text="CTX").grid(row=0, column=2, padx=15, sticky="e")
        ttk.Entry(args, textvariable=self.ctx, width=8).grid(row=0, column=3, padx=10)

        ttk.Label(args, text="Threads").grid(row=0, column=4, padx=15, sticky="e")
        ttk.Entry(args, textvariable=self.threads, width=8).grid(row=0, column=5, padx=10)

        ttk.Button(
            f, text="▶ Interactive Chat (FIXED)", command=self.run_chat
        ).pack(fill=tk.X, pady=20)

        self.chat_logbox = scrolledtext.ScrolledText(
            f, font=self.log_font, bg="#1e1e1e", fg="#00ff88"
        )
        self.chat_logbox.pack(fill=tk.BOTH, expand=True, pady=10)

        if TERMINAL:
            self.log(f"✔ Detected terminal: {TERMINAL}", tab="chat")
        else:
            self.log("❌ No supported terminal detected", tab="chat")

    def pick_chat_model(self):
        initial = (
            os.path.dirname(self.chat_model)
            if self.chat_model and os.path.exists(self.chat_model)
            else _models_dir()
        )
        p = filedialog.askopenfilename(
            title="Select GGUF model for Chat",
            initialdir=initial,
            filetypes=[("GGUF", "*.gguf")],
        )
        if p:
            self.chat_model = p
            self._save()
            self.log(f"✔ Chat model selected: {p}", tab="chat")

    def run_chat(self):
        if not self.bin_dir:
            messagebox.showerror("Error", "Please select llama.cpp build/bin directory first!")
            return
        if not self.chat_model:
            messagebox.showerror("Error", "Please select a GGUF model for Chat!")
            return

        cli = os.path.join(self.bin_dir, "llama-cli")
        flags = [
            f"-m \"{self.chat_model}\"",
            f"--ctx-size {self.ctx.get()}",
            f"--threads {self.threads.get()}",
        ]

        if supports("--chat-template", cli):
            flags.append(f"--chat-template {self.template.get()}")
            self.log("✔ --chat-template supported and enabled", tab="chat")

        if supports("--interactive-first", cli):
            flags.append("--interactive-first")
            self.log("✔ --interactive-first supported and enabled", tab="chat")

        cmd = cli + " " + " ".join(flags)
        self.log("▶ Running chat:\n" + cmd, tab="chat")

        if TERMINAL:
            subprocess.Popen([
                TERMINAL,
                "--command",
                f"bash -c \"{cmd}; echo; echo '--- Chat exited ---'; read -n1\"",
            ])
        else:
            messagebox.showerror("Error", "No terminal found to run command!")

    # ── Quantize tab ───────────────────────────────────────────────────

    def build_quant_tab(self):
        f = ttk.Frame(self.quant_tab)
        f.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Button(
            f, text="Select llama.cpp build/bin (Shared)", command=self.pick_bin_dir
        ).pack(fill=tk.X, pady=15)
        ttk.Button(
            f, text="Select GGUF file (for Quantize)", command=self.pick_quant_gguf
        ).pack(fill=tk.X, pady=15)

        qframe = ttk.Frame(f)
        qframe.pack(fill=tk.X, pady=15)
        ttk.Label(qframe, text="Quant type:").pack(side=tk.LEFT, padx=10)

        quant_types = [
            "q2_K", "q3_K_S", "q3_K_M", "q4_0", "q4_K_S", "q4_K_M",
            "q5_K_S", "q5_K_M", "q6_K", "q8_0", "f16",
        ]
        self.qtype_cb = ttk.Combobox(
            qframe, values=quant_types, width=12, state="readonly"
        )
        self.qtype_cb.pack(side=tk.LEFT, padx=10)
        self.qtype_cb.current(quant_types.index("q4_K_M"))

        ttk.Button(f, text="▶ Quantize", command=self.run_quantize).pack(
            fill=tk.X, pady=30
        )

        self.quant_logbox = scrolledtext.ScrolledText(
            f, font=self.log_font, bg="#1e1e1e", fg="#00ff88"
        )
        self.quant_logbox.pack(fill=tk.BOTH, expand=True, pady=10)

        if TERMINAL:
            self.log(f"✔ Detected terminal: {TERMINAL}", tab="quant")

    def pick_quant_gguf(self):
        initial = (
            os.path.dirname(self.quant_gguf)
            if self.quant_gguf and os.path.exists(self.quant_gguf)
            else _models_dir()
        )
        p = filedialog.askopenfilename(
            title="Select source GGUF for quantization",
            initialdir=initial,
            filetypes=[("GGUF", "*.gguf")],
        )
        if p:
            self.quant_gguf = p
            self._save()
            self.log(f"✔ Source GGUF selected: {p}", tab="quant")

    def run_quantize(self):
        if not self.bin_dir:
            messagebox.showerror("Error", "Please select llama.cpp build/bin directory first!")
            return
        if not self.quant_gguf:
            messagebox.showerror("Error", "Please select a source GGUF file!")
            return

        qtype = self.qtype_cb.get()
        if not qtype:
            messagebox.showerror("Error", "Please select a quantization type!")
            return

        exe = os.path.join(self.bin_dir, "llama-quantize")
        if not os.path.exists(exe):
            messagebox.showerror(
                "Error", "llama-quantize not found in selected bin directory!"
            )
            return

        out = self.quant_gguf.replace(".gguf", f"-{qtype}.gguf")
        cmd = f"{exe} \"{self.quant_gguf}\" \"{out}\" {qtype}"

        self.log("▶ Running quantization:\n" + cmd, tab="quant")

        if TERMINAL:
            subprocess.Popen([
                TERMINAL,
                "--command",
                f"bash -c \"{cmd}; echo; echo '--- Quantize finished ---'; read -n1\"",
            ])
        else:
            messagebox.showerror("Error", "No terminal found!")


if __name__ == "__main__":
    App().mainloop()
