"""
converter.py — Converter Manager Toplevel window.
"""

from __future__ import annotations
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont

from core.llama_detect import LLAMA_ROOT, models_dir
from core.converter_logic import (
    SCRIPTS, OUTTYPE_VALUES, DEFAULT_OUTTYPE,
    HF_BOOL_FLAGS, HF_TEXT_FLAGS, build_convert_args
)
from utils.subprocess_stream import stream_process
from gui import make_scrollable, log_widget, append_log, scale_font


class ConverterManager(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("llama.cpp Converter Manager")
        self.geometry("1920x900")
        self.minsize(1400, 700)

        style = ttk.Style(self)
        style.theme_use("clam")
        base = scale_font(28)
        mono = scale_font(26)
        df = tkfont.nametofont("TkDefaultFont")
        df.configure(size=base, family="DejaVu Sans")
        self.option_add("*Font", df)
        self.out_font = tkfont.Font(family="DejaVu Sans Mono", size=mono)
        style.configure("TButton", padding=20)
        style.configure("TFrame", padding=14)

        # State
        self.llama_dir   = tk.StringVar(value=LLAMA_ROOT)
        self.script      = tk.StringVar()
        self.input_path  = tk.StringVar()
        self.output_path = tk.StringVar()
        self.outtype     = tk.StringVar(value="f16")
        self.extra_args  = tk.StringVar()
        self.dry_run     = tk.BooleanVar(value=False)
        self.base_model  = tk.StringVar()

        # HF flags
        self.hf_bools = {f: tk.BooleanVar() for f in HF_BOOL_FLAGS}
        self.hf_texts = {f: tk.StringVar()  for f in HF_TEXT_FLAGS}

        self._build()

    # ── build ────────────────────────────────────────────────────────────

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="both", expand=True)
        bot = ttk.Frame(self, padding=(8, 0, 8, 8))
        bot.pack(fill="x", expand=False)

        _canvas, frm = make_scrollable(top)
        frm.configure(padding=14)
        frm.columnconfigure(1, weight=1)

        r = 0

        # llama.cpp dir
        ttk.Label(frm, text="llama.cpp Directory").grid(row=r, column=0, sticky="w", pady=6)
        ttk.Entry(frm, textvariable=self.llama_dir).grid(row=r, column=1, sticky="ew", padx=8)
        ttk.Button(frm, text="Browse",
                   command=self._browse_llama).grid(row=r, column=2, padx=6)
        r += 1

        # script
        ttk.Label(frm, text="Convert Script").grid(row=r, column=0, sticky="w", pady=6)
        self.script_cb = ttk.Combobox(frm, values=SCRIPTS, textvariable=self.script,
                                      state="readonly")
        self.script_cb.grid(row=r, column=1, sticky="ew", padx=8)
        self.script_cb.current(0)
        self.script_cb.bind("<<ComboboxSelected>>", self._on_script_change)
        r += 1

        # input
        ttk.Label(frm, text="Input Model / Path").grid(row=r, column=0, sticky="w", pady=6)
        ttk.Entry(frm, textvariable=self.input_path).grid(row=r, column=1, sticky="ew", padx=8)
        ttk.Button(frm, text="Browse",
                   command=self._browse_input).grid(row=r, column=2, padx=6)
        r += 1

        # LoRA base (hidden initially)
        self._lora_row = r
        self._lora_lbl = ttk.Label(frm, text="Base Model (LoRA)", foreground="red")
        self._lora_ent = ttk.Entry(frm, textvariable=self.base_model)
        self._lora_btn = ttk.Button(frm, text="Browse", command=self._browse_base)
        r += 1

        # outtype
        ttk.Label(frm, text="Output Type (--outtype)").grid(row=r, column=0, sticky="w", pady=6)
        ttk.Combobox(frm, values=OUTTYPE_VALUES, textvariable=self.outtype,
                     width=10, state="readonly").grid(row=r, column=1, sticky="w", padx=8)
        r += 1

        # HF flags panel (hidden initially)
        self._hf_flags_row = r
        self._hf_flags_frame = ttk.LabelFrame(frm, text="HF Flags", padding=8)
        flag_list = list(self.hf_bools.items())
        for i, (flag, var) in enumerate(flag_list):
            ttk.Checkbutton(self._hf_flags_frame, text=flag, variable=var).grid(
                row=i//4, column=i%4, padx=10, pady=3, sticky="w"
            )
        r += 1

        # HF text options panel (hidden initially)
        self._hf_text_row = r
        self._hf_text_frame = ttk.LabelFrame(frm, text="HF Options", padding=8)
        self._hf_text_frame.columnconfigure(1, weight=1)
        for ri, (flag, var) in enumerate(self.hf_texts.items()):
            ttk.Label(self._hf_text_frame, text=flag).grid(
                row=ri, column=0, sticky="e", padx=8, pady=3)
            ttk.Entry(self._hf_text_frame, textvariable=var).grid(
                row=ri, column=1, sticky="ew", padx=6, pady=3)
        r += 1

        # output path
        ttk.Label(frm, text="Output File / Dir").grid(row=r, column=0, sticky="w", pady=6)
        ttk.Entry(frm, textvariable=self.output_path).grid(row=r, column=1, sticky="ew", padx=8)
        ttk.Button(frm, text="Browse",
                   command=self._browse_output).grid(row=r, column=2, padx=6)
        r += 1

        # extra args
        ttk.Label(frm, text="Extra Arguments").grid(row=r, column=0, sticky="w", pady=6)
        ttk.Entry(frm, textvariable=self.extra_args).grid(
            row=r, column=1, columnspan=2, sticky="ew", padx=8)
        r += 1

        # dry-run + run button
        ttk.Checkbutton(frm, text="Dry Run (show command only)",
                        variable=self.dry_run).grid(row=r, column=0, columnspan=3, pady=8)
        r += 1
        ttk.Button(frm, text="Run Conversion 🚀",
                   command=self._run).grid(row=r, column=0, columnspan=3, pady=14)

        # Output log
        self.logbox = log_widget(bot, self.out_font)
        self.logbox.configure(height=6)
        self.logbox.pack(fill="x", expand=False)

        self._on_script_change(None)

    # ── script change ────────────────────────────────────────────────────

    def _on_script_change(self, _event):
        script = self.script.get()
        self.outtype.set(DEFAULT_OUTTYPE.get(script, "f16"))

        frm = self._lora_lbl.master  # the inner scrollable frame

        # LoRA row
        if script == "convert_lora_to_gguf.py":
            self._lora_lbl.grid(row=self._lora_row, column=0, sticky="w", pady=6)
            self._lora_ent.grid(row=self._lora_row, column=1, sticky="ew", padx=8)
            self._lora_btn.grid(row=self._lora_row, column=2, padx=6)
        else:
            self._lora_lbl.grid_forget()
            self._lora_ent.grid_forget()
            self._lora_btn.grid_forget()

        # HF panels
        if script == "convert_hf_to_gguf.py":
            self._hf_flags_frame.grid(
                row=self._hf_flags_row, column=0, columnspan=3,
                sticky="ew", padx=4, pady=4)
            self._hf_text_frame.grid(
                row=self._hf_text_row, column=0, columnspan=3,
                sticky="ew", padx=4, pady=4)
        else:
            self._hf_flags_frame.grid_forget()
            self._hf_text_frame.grid_forget()
            for v in self.hf_bools.values(): v.set(False)
            for v in self.hf_texts.values(): v.set("")

    # ── browse helpers ───────────────────────────────────────────────────

    def _browse_llama(self):
        d = filedialog.askdirectory(title="Select llama.cpp directory",
                                    initialdir=self.llama_dir.get() or "/")
        if d: self.llama_dir.set(d)

    def _browse_input(self):
        d = filedialog.askdirectory(title="Select input model/path",
                                    initialdir=models_dir())
        if d: self.input_path.set(d)

    def _browse_output(self):
        d = filedialog.askdirectory(title="Select output directory",
                                    initialdir=models_dir())
        if d: self.output_path.set(d)

    def _browse_base(self):
        p = filedialog.askopenfilename(
            title="Select base model GGUF",
            initialdir=models_dir(),
            filetypes=[("GGUF", "*.gguf")],
        )
        if p: self.base_model.set(p)

    # ── log ──────────────────────────────────────────────────────────────

    def _log(self, text: str):
        append_log(self.logbox, text)
        self.update_idletasks()

    # ── run ──────────────────────────────────────────────────────────────

    def _run(self):
        try:
            cmd = build_convert_args(
                llama_dir=self.llama_dir.get(),
                script=self.script.get(),
                input_path=self.input_path.get(),
                outtype=self.outtype.get(),
                output_path=self.output_path.get(),
                base_model=self.base_model.get(),
                hf_bools={f: v.get() for f, v in self.hf_bools.items()},
                hf_texts={f: v.get() for f, v in self.hf_texts.items()},
                extra_args=self.extra_args.get(),
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        from utils.terminal import shell_quote_list
        display = shell_quote_list(cmd)
        self._log(f"\n▶ Command:\n{display}\n\n")

        if self.dry_run.get():
            self._log("🛠 Dry Run — not executed\n")
            return

        def _on_line(line):
            self.after(0, self._log, line)

        def _on_done(rc):
            if rc == 0:
                self.after(0, self._log, "\n✅ Done!\n")
            else:
                self.after(0, self._log, f"\n⚠ Exited with code {rc}\n")

        stream_process(cmd, _on_line, _on_done)
