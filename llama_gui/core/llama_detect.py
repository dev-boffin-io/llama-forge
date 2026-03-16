"""
llama_detect.py — llama.cpp project root detection and config persistence.
"""

from __future__ import annotations
import os
import sys
import json

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".llama_cpp_gui.json")

_ROOT_MARKERS = ("CMakeLists.txt", "convert_hf_to_gguf.py")


def find_llama_root() -> str:
    """
    Walk up from the script/executable directory looking for the llama.cpp
    project root (directory that contains all _ROOT_MARKERS).

    Search order:
      1. Directory of the running script / frozen executable
      2. CWD
      3. $HOME (last resort)
    """
    if getattr(sys, "frozen", False):       # PyInstaller onefile
        start = os.path.dirname(sys.executable)
    else:
        start = os.path.dirname(os.path.abspath(__file__))

    candidates = [start, os.getcwd(), os.path.expanduser("~")]

    for base in candidates:
        probe = base
        for _ in range(8):
            if all(os.path.isfile(os.path.join(probe, m)) for m in _ROOT_MARKERS):
                return probe
            parent = os.path.dirname(probe)
            if parent == probe:
                break
            probe = parent

    return start   # best-effort fallback


LLAMA_ROOT:      str = find_llama_root()
BIN_DIR_DEFAULT: str = os.path.join(LLAMA_ROOT, "build", "bin")
MODELS_DIR:      str = os.path.join(LLAMA_ROOT, "models")


def models_dir() -> str:
    return MODELS_DIR if os.path.isdir(MODELS_DIR) else LLAMA_ROOT


def bin_dir_valid(d: str) -> bool:
    return bool(d) and os.path.isfile(os.path.join(d, "llama-cli"))


def supports_flag(flag: str, exe: str) -> bool:
    import subprocess
    try:
        out = subprocess.check_output([exe, "--help"], stderr=subprocess.STDOUT, text=True)
        return flag in out
    except Exception:
        return False


# ── Config ───────────────────────────────────────────────────────────────────

def load_config() -> dict:
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg: dict) -> None:
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass
