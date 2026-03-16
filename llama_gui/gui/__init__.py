"""
gui/__init__.py — shared Tkinter helpers used across tabs.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk


def scale_font(base: int) -> int:
    """Return DPI-scaled font size (96 dpi baseline, clamped 1×–2×)."""
    try:
        root = tk._default_root
        if root is None:
            return base
        dpi = root.winfo_fpixels("1i")
        return max(base, min(int(base * dpi / 96.0), base * 2))
    except Exception:
        return base


def make_scrollable(parent: tk.Widget) -> tuple[tk.Canvas, ttk.Frame]:
    """
    Pack a vertically-scrollable frame inside *parent*.
    Returns (canvas, inner_frame).
    Mouse-wheel works on Linux (Button-4/5) and Windows/macOS (MouseWheel).
    """
    canvas = tk.Canvas(parent, highlightthickness=0)
    vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner = ttk.Frame(canvas)
    win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>",
                lambda e: canvas.itemconfig(win_id, width=e.width))

    # Cross-platform mouse-wheel
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll( 1, "units"))

    return canvas, inner


def log_widget(parent: tk.Widget, font_obj) -> tk.Text:
    """Create a dark-themed scrollable log Text widget."""
    from tkinter import scrolledtext
    box = scrolledtext.ScrolledText(
        parent,
        font=font_obj,
        bg="#1e1e1e",
        fg="#00ff88",
        insertbackground="#00ff88",
        relief="flat",
        padx=10,
        pady=10,
    )
    return box


def append_log(widget: tk.Text, text: str) -> None:
    """Thread-safe append to a log Text widget (call via root.after if needed)."""
    widget.insert(tk.END, text)
    widget.see(tk.END)
