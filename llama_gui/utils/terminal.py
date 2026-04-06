"""
terminal.py — terminal detection and cross-platform launch helper.

Resolves x-terminal-emulator symlink to find the real terminal binary,
then uses the correct flags for that terminal.
"""

import os
import shutil
import subprocess

# Map: real terminal binary → (exec_flag, pass_as_single_string)
# pass_as_single_string=True  → terminal <flag> "bash -c 'cmd'"  (single arg)
# pass_as_single_string=False → terminal <flag> bash -c "cmd"    (split args)
_TERMINAL_FLAGS: dict[str, tuple[str, bool]] = {
    "xfce4-terminal": ("-e",        True),
    "gnome-terminal": ("--",        False),
    "konsole":        ("-e",        True),
    "xterm":          ("-e",        True),
    "terminator":     ("-x",        False),
    "lxterminal":     ("-e",        True),
    "mate-terminal":  ("-e",        True),
    "tilix":          ("--",        False),
    "xfce4-terminal.wrapper": ("-e", True),
}

_TITLE_FLAG: dict[str, str] = {
    "xfce4-terminal": "--title",
    "gnome-terminal": "--title",
    "konsole":        "--title",
    "tilix":          "--title",
    "lxterminal":     "--title",
    "mate-terminal":  "--title",
}


def _resolve_terminal(binary: str) -> str:
    """
    Follow symlinks to find the real terminal binary name.
    e.g. x-terminal-emulator → /usr/bin/xfce4-terminal → 'xfce4-terminal'
    """
    path = shutil.which(binary)
    if not path:
        return binary
    try:
        real = os.path.realpath(path)        # resolve all symlinks
        return os.path.basename(real)
    except OSError:
        return binary


def detect_terminal() -> tuple[str, str] | tuple[None, None]:
    """
    Return (launch_binary, real_name) for the first available terminal.
    launch_binary is what we actually Popen; real_name is used for flag lookup.
    """
    candidates = [
        "x-terminal-emulator",   # Debian/Ubuntu update-alternatives
        "xfce4-terminal",
        "gnome-terminal",
        "konsole",
        "xterm",
        "terminator",
        "lxterminal",
        "mate-terminal",
        "tilix",
    ]
    for t in candidates:
        if shutil.which(t):
            real = _resolve_terminal(t)
            return t, real
    return None, None


TERMINAL, _REAL_TERM = detect_terminal()


def launch_in_terminal(shell_cmd: str, title: str = "") -> bool:
    """
    Run shell_cmd in a new terminal window.
    shell_cmd must be a properly shell-quoted string.
    Returns True if launched, False if no terminal available.
    """
    if not TERMINAL:
        return False

    real = _REAL_TERM or TERMINAL
    flag, single = _TERMINAL_FLAGS.get(real,
                   _TERMINAL_FLAGS.get(TERMINAL, ("-e", True)))

    pause = "; echo; echo '--- finished ---'; read -rn1"
    full_cmd = shell_cmd + pause

    cmd_parts = [TERMINAL]

    # Optional title
    title_flag = _TITLE_FLAG.get(real) or _TITLE_FLAG.get(TERMINAL)
    if title and title_flag:
        cmd_parts += [title_flag, title]

    if single:
        # terminal -e "bash -c 'cmd; pause'"
        inner = full_cmd.replace("'", "'\\''")
        cmd_parts += [flag, f"bash -c '{inner}'"]
    else:
        # terminal -- bash -c "cmd; pause"
        cmd_parts += [flag, "bash", "-c", full_cmd]

    subprocess.Popen(cmd_parts)
    return True


def shell_quote_list(args: list[str]) -> str:
    """Convert arg list to a shell-safe display string."""
    parts = []
    for a in args:
        if not a or " " in a or '"' in a:
            escaped = a.replace("\\", "\\\\").replace('"', '\\"')
            parts.append(f'"{escaped}"')
        else:
            parts.append(a)
    return " ".join(parts)

