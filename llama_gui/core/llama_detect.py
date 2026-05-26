"""
llama_detect.py — llama.cpp project root detection and config persistence.

Cross-platform: Linux · macOS · Windows · Android/Termux
"""

from __future__ import annotations
import os
import sys
import json
import platform

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".llama_cpp_gui.json")

_ROOT_MARKERS = ("CMakeLists.txt", "convert_hf_to_gguf.py")


# ── OS helpers ────────────────────────────────────────────────────────────────

def is_windows() -> bool:
    return sys.platform == "win32"

def is_macos() -> bool:
    return sys.platform == "darwin"

def is_android() -> bool:
    """True when running inside Termux or proot-Debian on Android."""
    return "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ

def is_linux() -> bool:
    return sys.platform.startswith("linux")


def exe_name(binary: str) -> str:
    """Return binary with .exe suffix on Windows, unchanged elsewhere."""
    if is_windows() and not binary.endswith(".exe"):
        return binary + ".exe"
    return binary


# ── Build-dir candidates (platform-aware) ────────────────────────────────────

def _build_bin_candidates(root: str) -> list[str]:
    """
    Return a list of likely bin-directory paths in priority order
    for the given project root, covering all supported platforms.
    """
    candidates = [
        # Standard CMake out-of-source builds
        os.path.join(root, "build", "bin"),
        os.path.join(root, "build", "bin", "Release"),   # MSVC Release
        os.path.join(root, "build", "bin", "Debug"),     # MSVC Debug
        os.path.join(root, "build", "Release"),          # some generators
        os.path.join(root, "build", "Debug"),
        # Termux / proot-Debian (cmake --install goes to /data/... or /usr)
        os.path.join(root, "build"),
        # Homebrew / system install (macOS)
        "/opt/homebrew/bin",
        "/usr/local/bin",
        # Linux system-wide install
        "/usr/bin",
    ]
    if is_android():
        termux_prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
        candidates.insert(0, os.path.join(termux_prefix, "bin"))
    return candidates


# ── Root detection ────────────────────────────────────────────────────────────

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


LLAMA_ROOT: str = find_llama_root()

# First valid build/bin directory, or the canonical default as a string
def _find_bin_dir_default(root: str) -> str:
    for d in _build_bin_candidates(root):
        if _bin_dir_has_cli(d):
            return d
    # Fall back to the standard path even if it doesn't exist yet
    return os.path.join(root, "build", "bin")

def _bin_dir_has_cli(d: str) -> bool:
    return bool(d) and os.path.isfile(os.path.join(d, exe_name("llama-cli")))

BIN_DIR_DEFAULT: str = _find_bin_dir_default(LLAMA_ROOT)
MODELS_DIR:      str = os.path.join(LLAMA_ROOT, "models")


def models_dir() -> str:
    return MODELS_DIR if os.path.isdir(MODELS_DIR) else LLAMA_ROOT


def bin_dir_valid(d: str) -> bool:
    """True if d contains llama-cli (or llama-cli.exe on Windows)."""
    return _bin_dir_has_cli(d)


def resolve_exe(name: str, bin_dir: str) -> str:
    """
    Return the full path to a llama binary (e.g. 'llama-cli').
    Appends .exe on Windows automatically.
    """
    return os.path.join(bin_dir, exe_name(name))


def supports_flag(flag: str, exe: str) -> bool:
    import subprocess
    try:
        out = subprocess.check_output(
            [exe, "--help"], stderr=subprocess.STDOUT, text=True
        )
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
