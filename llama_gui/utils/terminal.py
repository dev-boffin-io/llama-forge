"""
terminal.py — cross-platform terminal detection and launch helper.

Supported platforms:
  • Linux  — xfce4-terminal, gnome-terminal, konsole, xterm, …
  • macOS  — Terminal.app (AppleScript), iTerm2 (AppleScript)
  • Windows — Windows Terminal (wt), PowerShell, cmd
  • Android/Termux — xfce4-terminal (X11/XFCE via proot)

launch_in_terminal(shell_cmd, title="") → bool
  Returns True if launched, False if no terminal available.
"""

from __future__ import annotations
import os
import shutil
import subprocess
import sys


# ── OS detection ──────────────────────────────────────────────────────────────

def _is_windows() -> bool:
    return sys.platform == "win32"

def _is_macos() -> bool:
    return sys.platform == "darwin"

def _is_linux() -> bool:
    return sys.platform.startswith("linux")


# ── Linux X11 terminal tables ─────────────────────────────────────────────────

# Map: real terminal binary → (exec_flag, pass_as_single_string)
# pass_as_single_string=True  → terminal <flag> "bash -c 'cmd'"  (single arg)
# pass_as_single_string=False → terminal <flag> bash -c "cmd"    (split args)
_TERMINAL_FLAGS: dict[str, tuple[str, bool]] = {
    "xfce4-terminal":         ("-e",  True),
    "gnome-terminal":         ("--",  False),
    "konsole":                ("-e",  True),
    "xterm":                  ("-e",  True),
    "terminator":             ("-x",  False),
    "lxterminal":             ("-e",  True),
    "mate-terminal":          ("-e",  True),
    "tilix":                  ("--",  False),
    "xfce4-terminal.wrapper": ("-e",  True),
    "alacritty":              ("-e",  False),
    "kitty":                  ("--",  False),
    "foot":                   ("--",  False),
    "wezterm":                ("--",  False),
    "st":                     ("-e",  False),
    "urxvt":                  ("-e",  False),
    "rxvt":                   ("-e",  False),
    "sakura":                 ("-e",  True),
    "terminology":            ("-e",  True),
}

_TITLE_FLAG: dict[str, str] = {
    "xfce4-terminal": "--title",
    "gnome-terminal": "--title",
    "konsole":        "--title",
    "tilix":          "--title",
    "lxterminal":     "--title",
    "mate-terminal":  "--title",
    "alacritty":      "--title",
    "kitty":          "--title",
    "wezterm":        "--title",
}

_LINUX_CANDIDATES = [
    "x-terminal-emulator",   # Debian/Ubuntu update-alternatives
    "xfce4-terminal",
    "gnome-terminal",
    "konsole",
    "xterm",
    "terminator",
    "lxterminal",
    "mate-terminal",
    "tilix",
    "alacritty",
    "kitty",
    "foot",
    "wezterm",
    "st",
    "urxvt",
]


def _resolve_terminal(binary: str) -> str:
    """Follow symlinks to find the real terminal binary name."""
    path = shutil.which(binary)
    if not path:
        return binary
    try:
        real = os.path.realpath(path)
        return os.path.basename(real)
    except OSError:
        return binary


# ── Platform launchers ────────────────────────────────────────────────────────

def _launch_linux(shell_cmd: str, title: str) -> bool:
    """Launch shell_cmd in a new X11 terminal window."""
    term = None
    real = None
    for t in _LINUX_CANDIDATES:
        if shutil.which(t):
            term = t
            real = _resolve_terminal(t)
            break

    if not term:
        return False

    flag, single = _TERMINAL_FLAGS.get(real,
                   _TERMINAL_FLAGS.get(term, ("-e", True)))

    pause = "; echo; echo '--- finished ---'; read -rn1"
    full_cmd = shell_cmd + pause

    cmd_parts = [term]

    title_flag = _TITLE_FLAG.get(real) or _TITLE_FLAG.get(term)
    if title and title_flag:
        cmd_parts += [title_flag, title]

    if single:
        inner = full_cmd.replace("'", "'\\''")
        cmd_parts += [flag, f"bash -c '{inner}'"]
    else:
        cmd_parts += [flag, "bash", "-c", full_cmd]

    subprocess.Popen(cmd_parts)
    return True


def _launch_macos(shell_cmd: str, title: str) -> bool:
    """
    Launch shell_cmd in a new macOS terminal window.
    Prefers iTerm2 if installed, falls back to Terminal.app.
    """
    pause = r'; echo; echo "--- finished ---"; read -rn1 _'
    full_cmd = shell_cmd + pause
    # Escape for AppleScript double-quoted string
    esc = full_cmd.replace("\\", "\\\\").replace('"', '\\"')

    # Try iTerm2 first
    iterm_check = subprocess.run(
        ["osascript", "-e", 'id of application "iTerm"'],
        capture_output=True, text=True
    )
    if iterm_check.returncode == 0:
        script = f'''
tell application "iTerm"
    activate
    set newWindow to (create window with default profile)
    tell current session of newWindow
        write text "{esc}"
    end tell
end tell
'''
    else:
        # Terminal.app
        title_cmd = f'set custom title of front window to "{title}"' if title else ""
        script = f'''
tell application "Terminal"
    activate
    do script "{esc}"
    {title_cmd}
end tell
'''

    try:
        subprocess.Popen(["osascript", "-e", script])
        return True
    except Exception:
        return False


def _launch_windows(shell_cmd: str, title: str) -> bool:
    """
    Launch shell_cmd in a new Windows terminal window.
    Tries: Windows Terminal (wt) → PowerShell → cmd.
    """
    pause = " & pause"

    # Prefer Windows Terminal
    if shutil.which("wt"):
        # wt runs a new PowerShell tab
        ps_cmd = f'powershell -NoExit -Command "{shell_cmd.replace(chr(34), chr(39))}"'
        title_arg = ["--title", title] if title else []
        cmd = ["wt"] + title_arg + ["powershell", "-NoExit", "-Command", shell_cmd]
        try:
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
            return True
        except Exception:
            pass

    # Fallback: PowerShell
    if shutil.which("powershell"):
        ps_cmd = f'powershell -NoExit -Command "{shell_cmd}"'
        try:
            subprocess.Popen(
                ["powershell", "-NoExit", "-Command", shell_cmd],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return True
        except Exception:
            pass

    # Last resort: cmd.exe
    try:
        title_part = f'"{title}" ' if title else ""
        subprocess.Popen(
            f'start {title_part}cmd /K "{shell_cmd}"',
            shell=True
        )
        return True
    except Exception:
        return False


# ── Public API ────────────────────────────────────────────────────────────────

def detect_terminal() -> str | None:
    """
    Return a human-readable description of the available terminal,
    or None if none detected.
    """
    if _is_windows():
        for t in ("wt", "powershell", "cmd"):
            if shutil.which(t):
                return t
        return "cmd"  # always present on Windows
    if _is_macos():
        return "Terminal.app"
    # Linux/Android
    for t in _LINUX_CANDIDATES:
        if shutil.which(t):
            return _resolve_terminal(t)
    return None


TERMINAL = detect_terminal()


def launch_in_terminal(shell_cmd: str, title: str = "") -> bool:
    """
    Run shell_cmd in a new terminal window on any supported platform.

    shell_cmd   — a shell-quoted command string (not a list)
    title       — window title hint (best-effort per terminal)

    Returns True if launched, False if no terminal is available.
    """
    if _is_windows():
        return _launch_windows(shell_cmd, title)
    if _is_macos():
        return _launch_macos(shell_cmd, title)
    return _launch_linux(shell_cmd, title)


def shell_quote_list(args: list[str]) -> str:
    """Convert arg list to a shell-safe display string."""
    if _is_windows():
        # Windows: wrap args with spaces in double quotes
        parts = []
        for a in args:
            if not a or " " in a or '"' in a:
                escaped = a.replace("\\", "\\\\").replace('"', '\\"')
                parts.append(f'"{escaped}"')
            else:
                parts.append(a)
        return " ".join(parts)
    else:
        # POSIX
        parts = []
        for a in args:
            if not a or " " in a or '"' in a:
                escaped = a.replace("\\", "\\\\").replace('"', '\\"')
                parts.append(f'"{escaped}"')
            else:
                parts.append(a)
        return " ".join(parts)
